---
title: C FFI Basics
sidebar:
  order: 28
---

Most real-world software eventually needs to cross a language boundary. A Swift app may call into a C library for cryptography or image processing. A Rust library may need to expose its functionality to C, Python, or Swift callers. The mechanism that makes this possible is the Foreign Function Interface – FFI.

Both Swift and Rust have strong FFI support for C, and the patterns are more similar than you might expect. Understanding C FFI is also essential context for later chapters – the limitations you encounter here motivate the WebAssembly Component Model as a better approach for cross-language interop.

## Calling C from Rust

### Declaring external functions

To call a C function from Rust, you declare its signature inside an `extern "C"` block. This tells the compiler that the function exists somewhere else and uses the C calling convention:

```rust
// Rust
unsafe extern "C" {
    pub safe fn abs(input: i32) -> i32;
    pub unsafe fn strlen(s: *const std::ffi::c_char) -> usize;
}

let result = abs(-5); // 5
```

Swift's equivalent is more automatic. When you import a C module, Swift generates native declarations from the C headers:

```swift
// Swift
import Darwin // or Glibc on Linux

let result = abs(-5)
print("abs(-5) = \(result)") // abs(-5) = 5
```

Notice that in Swift, calling C functions is seamless – the compiler handles the bridging. In Rust 2024, the declaration block itself is `unsafe extern "C"` because you are asserting that the signatures are correct. Individual items inside the block default to `unsafe`, though you can mark a function `safe` when the Rust signature fully captures the caller's obligations. In day-to-day FFI code, most calls still go through `unsafe`.

### Linking to C libraries

When the C function comes from a library that is not part of the standard C runtime, you need to tell the linker where to find it. Rust provides the `#[link]` attribute for this:

```rust
// Rust
#[link(name = "m")]
unsafe extern "C" {
    pub safe fn sqrt(x: f64) -> f64;
}

let val = sqrt(144.0); // 12.0
```

The `#[link(name = "m")]` attribute corresponds to the `-lm` linker flag for the C math library. For more complex linking scenarios, you can use a `build.rs` build script with the `cc` crate to compile C source files or configure library search paths.

In Swift, you configure linking through Xcode's build settings or through a `module.modulemap` file that maps C headers to a Swift-importable module.

## Exposing Rust to C callers

### `extern "C"` functions and `#[no_mangle]`

To make a Rust function callable from C (or any language that can call C functions, including Swift), you apply two attributes:

```rust
// Rust
#[unsafe(no_mangle)]
pub extern "C" fn add(a: i32, b: i32) -> i32 {
    a + b
}
```

- **`extern "C"`**: tells the compiler to use the C calling convention instead of Rust's default calling convention.
- **`#[unsafe(no_mangle)]`**: prevents the compiler from changing the function's symbol name. By default, Rust mangles function names to include module paths and type information. `#[unsafe(no_mangle)]` preserves the exact name so C callers can find it.

Older Rust examples often show `#[no_mangle]`. In Rust 2024, this became `#[unsafe(no_mangle)]` because exporting a fixed symbol name is considered an unsafe attribute: it creates a global contract with the linker and with foreign callers.

In Swift, you use `@_cdecl` to achieve the same thing:

```swift
// Swift
@_cdecl("add")
func add(_ a: Int32, _ b: Int32) -> Int32 {
    a + b
}
```

### C-compatible types and `repr(C)`

C has a specific layout for structures – fields are laid out in declaration order with platform-defined alignment. Rust's default struct layout is unspecified and may reorder fields for optimization. To guarantee C-compatible layout, use `#[repr(C)]`:

```rust
// Rust
#[repr(C)]
pub struct Point {
    pub x: f64,
    pub y: f64,
}

#[unsafe(no_mangle)]
pub extern "C" fn distance_from_origin(p: Point) -> f64 {
    (p.x * p.x + p.y * p.y).sqrt()
}
```

The equivalent C struct would be:

```c
// C
typedef struct {
    double x;
    double y;
} Point;
```

Without `#[repr(C)]`, the Rust compiler is free to reorder fields, insert different padding, or optimize the layout in ways that would break compatibility with C callers.

Common `repr(C)` types you will use in FFI:

- **Integers**: `i8`/`u8`, `i16`/`u16`, `i32`/`u32`, `i64`/`u64` correspond directly to `int8_t`, `uint16_t`, etc.
- **Floats**: `f32` and `f64` correspond to `float` and `double`.
- **Pointers**: `*const T` and `*mut T` are C-compatible raw pointers.
- **Enums**: `#[repr(C)]` enums map to C enums. `#[repr(i32)]` specifies the underlying integer type explicitly.

```rust
// Rust
#[repr(C)]
pub enum Status {
    Ok = 0,
    Error = 1,
    NotFound = 2,
}
```

## Passing strings across FFI

Strings are one of the trickiest aspects of FFI, because Rust and C have fundamentally different string representations:

- **C strings** are null-terminated byte arrays (`char*`).
- **Rust strings** (`String`, `&str`) are UTF-8 byte slices with a known length and no null terminator.

Rust provides two types in `std::ffi` for bridging this gap:

- **`CStr`**: a borrowed reference to a C string (analogous to `&str` for Rust strings). Used when receiving a string from C.
- **`CString`**: an owned C string with a null terminator (analogous to `String`). Used when passing a string to C.

### Receiving a C string in Rust

```rust
// Rust
use std::ffi::{c_char, CStr};

/// # Safety
///
/// `name` must point to a valid null-terminated C string.
#[unsafe(no_mangle)]
pub unsafe extern "C" fn greet(name: *const c_char) {
    let c_str = unsafe { CStr::from_ptr(name) };
    match c_str.to_str() {
        Ok(name) => println!("Hello, {name}!"),
        Err(_) => println!("Hello, stranger! (invalid UTF-8)"),
    }
}
```

`CStr::from_ptr` borrows the C string without copying it. The `to_str()` method validates the UTF-8 encoding and returns a `Result`.

### Sending a string to C

```rust
// Rust
use std::ffi::{c_char, CString};

fn call_c_function() {
    let greeting = CString::new("hello from Rust")
        .expect("CString::new failed");

    // greeting.as_ptr() returns a *const c_char suitable for C
    unsafe {
        puts(greeting.as_ptr());
    }
    // greeting must outlive any C code using the pointer
}

unsafe extern "C" {
    fn puts(s: *const c_char) -> i32;
}

```

`CString::new` takes a Rust string and appends a null terminator. It returns an error if the input contains an interior null byte (which is valid in Rust strings but not in C strings).

In Swift, string bridging to C is handled automatically in many cases – you can pass a Swift `String` to a function expecting `UnsafePointer<CChar>` and the compiler creates a temporary C string. Rust requires you to manage this conversion explicitly.

## Opaque types and pointers

A common FFI pattern is the opaque pointer – you expose a type to C as an opaque handle without revealing its internal structure. The C side only holds a pointer and passes it back to your functions:

```rust
// Rust
use std::ffi::c_char;

pub struct Database {
    path: String,
    connection_count: u32,
}

/// # Safety
///
/// `path` must point to a valid null-terminated UTF-8 string.
#[unsafe(no_mangle)]
pub unsafe extern "C" fn db_open(path: *const c_char) -> *mut Database {
    let path_str = unsafe { std::ffi::CStr::from_ptr(path) }
        .to_str()
        .expect("invalid UTF-8");

    let db = Database {
        path: path_str.to_owned(),
        connection_count: 0,
    };

    Box::into_raw(Box::new(db))
}

/// # Safety
///
/// `db` must be a valid pointer returned by `db_open` and must not have been freed.
#[unsafe(no_mangle)]
pub unsafe extern "C" fn db_connection_count(db: *const Database) -> u32 {
    let db = unsafe { &*db };
    db.connection_count
}

/// # Safety
///
/// `db` must be a pointer returned by `db_open` and must not be used after calling this function.
#[unsafe(no_mangle)]
pub unsafe extern "C" fn db_close(db: *mut Database) {
    if !db.is_null() {
        let _ = unsafe { Box::from_raw(db) };
        // Box is dropped here, freeing the memory
    }
}
```

The corresponding C header would look like:

```c
// C header
typedef struct Database Database; // opaque – no fields visible

Database* db_open(const char* path);
uint32_t db_connection_count(const Database* db);
void db_close(Database* db);
```

This pattern is very similar to what you see in Swift when working with Core Foundation types – you receive an opaque reference and pass it to API functions. The difference is that in Rust, you must manually manage the conversion between Rust's ownership model and C's pointer-based model using `Box::into_raw` and `Box::from_raw`.

## Safety considerations

Most raw FFI calls are `unsafe` in Rust. An `unsafe extern` block says "these declarations are trusted", and individual items can be marked `safe` only when their signatures fully express the caller obligations. The compiler still cannot verify:

- **Pointer validity**: C pointers may be null, dangling, or point to memory that has been freed.
- **Lifetime correctness**: C has no concept of lifetimes. A pointer received from C might outlive the data it points to.
- **Thread safety**: C functions may not be thread-safe, but nothing in their signature indicates this.
- **Type correctness**: if you declare the wrong signature for a C function, the compiler will not catch the mismatch – you will get undefined behavior at runtime.
- **Memory ownership**: when C allocates memory, Rust must not free it with Rust's allocator (and vice versa). Each side must free its own allocations.

Compare this with Swift's approach to C interop. Swift also uses `UnsafePointer`, `UnsafeMutablePointer`, and related types when working with C APIs, and many of the same concerns apply. The difference is that Swift hides more of the unsafety behind automatic bridging – for example, Swift automatically bridges `String` to C strings and manages `Unmanaged` references for Core Foundation types. Rust makes every unsafe operation explicit.

### Best practices for safe FFI

When writing FFI code in Rust, the standard practice is to create a safe Rust wrapper around the unsafe FFI layer:

```rust
// Rust
use std::ffi::{c_char, CStr, CString};

// Raw FFI bindings (unsafe)
unsafe extern "C" {
    fn c_library_init() -> *mut std::ffi::c_void;
    fn c_library_process(handle: *mut std::ffi::c_void, input: *const c_char) -> i32;
    fn c_library_free(handle: *mut std::ffi::c_void);
}

// Safe wrapper
pub struct Library {
    handle: *mut std::ffi::c_void,
}

impl Library {
    pub fn new() -> Option<Self> {
        let handle = unsafe { c_library_init() };
        if handle.is_null() {
            None
        } else {
            Some(Library { handle })
        }
    }

    pub fn process(&self, input: &str) -> Result<i32, std::ffi::NulError> {
        let c_input = CString::new(input)?;
        let result = unsafe { c_library_process(self.handle, c_input.as_ptr()) };
        Ok(result)
    }
}

impl Drop for Library {
    fn drop(&mut self) {
        unsafe { c_library_free(self.handle) };
    }
}
```

This pattern – raw `extern` declarations behind a safe public API – is the Rust equivalent of Swift's pattern of wrapping C APIs in a Swift class with `deinit` for cleanup. The `Drop` implementation ensures the C resource is freed when the Rust wrapper goes out of scope, just as `deinit` does in Swift.

## The `bindgen` and `cbindgen` tools

Writing FFI declarations by hand is tedious and error-prone. The Rust ecosystem provides two tools to automate this:

- **`bindgen`**: reads C/C++ header files and generates Rust `extern "C"` declarations automatically. This is the Rust equivalent of Swift's automatic C header import.
- **`cbindgen`**: reads Rust source code and generates C/C++ header files for your `extern "C"` functions and `#[repr(C)]` types.

These tools are essential for larger FFI projects and are commonly integrated into the build process via `build.rs`.

## Key differences and gotchas

**Most FFI calls are `unsafe`**: in Swift, calling a C function usually does not require any special annotation. In Rust, raw FFI declarations live in an `unsafe extern` block, and many imported functions remain `unsafe fn` to call. Rust makes that unsafety explicit instead of hiding it behind the bridge.

**No automatic string bridging**: Swift automatically converts between `String` and `UnsafePointer<CChar>` in many contexts. Rust requires explicit conversion using `CStr` and `CString`, and you must ensure the C string outlives any pointer derived from it.

**Layout is not guaranteed without `repr(C)`**: Rust's default struct layout is unspecified. If you forget `#[repr(C)]`, your structs will have incorrect layout when accessed from C, leading to silent data corruption rather than a compile error.

**Memory ownership must be tracked manually**: when you pass a `Box::into_raw` pointer to C, Rust no longer manages that memory. You must ensure it comes back through `Box::from_raw` eventually, or you will leak memory. Mixing allocators – freeing Rust-allocated memory with C's `free()` or vice versa – is undefined behavior.

**Panics must not cross the FFI boundary**: if a Rust function called from C panics, the behavior is undefined. Use `std::panic::catch_unwind` at the FFI boundary to convert panics into error codes:

```rust
// Rust
use std::panic;

#[unsafe(no_mangle)]
pub extern "C" fn safe_divide(a: i32, b: i32, result: *mut i32) -> i32 {
    let outcome = panic::catch_unwind(|| a / b);
    match outcome {
        Ok(val) => {
            unsafe { *result = val };
            0 // success
        }
        Err(_) => -1, // error (e.g., division by zero)
    }
}
```

Note that `catch_unwind` only works with the default `panic = "unwind"` strategy. If the profile is configured with `panic = "abort"` in `Cargo.toml`, the process terminates immediately on panic and `catch_unwind` never gets a chance to run.

**Error handling is reduced to integers**: C has no `Result`, no exceptions, and no sum types. FFI functions typically return integer error codes, which is a significant step down from Rust's `Result<T, E>` or Swift's `throws`. This is one of the fundamental limitations that motivates richer interop mechanisms like UniFFI and the Component Model.

## Further reading

- [The Rust FFI Omnibus](http://jakegoulding.com/rust-ffi-omnibus/): practical cookbook for common FFI patterns
- [The Rustonomicon – FFI](https://doc.rust-lang.org/nomicon/ffi.html): the official guide to unsafe FFI in Rust
- [The `bindgen` User Guide](https://rust-lang.github.io/rust-bindgen/): generating Rust bindings from C headers
- [The `cbindgen` documentation](https://github.com/mozilla/cbindgen): generating C headers from Rust code
- [The `CStr` and `CString` documentation](https://doc.rust-lang.org/std/ffi/index.html): Rust's FFI string types
