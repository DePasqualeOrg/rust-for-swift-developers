---
title: Unsafe Rust
sidebar:
  order: 22
---

Everything covered so far in this guide operates within Rust's safety guarantees: the compiler verifies memory safety, prevents data races, and ensures every value is valid. But some operations cannot be verified at compile time – dereferencing a raw pointer, calling a C function, or accessing hardware registers. For these cases, Rust provides `unsafe` blocks that tell the compiler "I have verified this is correct; trust me."

The `unsafe` keyword does not mean "dangerous" or "bad." It means "the programmer is taking responsibility for upholding invariants that the compiler cannot check." This is conceptually similar to how Swift's standard library is built on top of C and C++ code that the Swift compiler does not verify – the safe interface is what matters to callers.

## The five unsafe superpowers

An `unsafe` block unlocks exactly five capabilities that are not available in safe Rust:

1. **Dereference raw pointers**: raw pointers (`*const T` and `*mut T`) can be created in safe code, but dereferencing them requires `unsafe` because the compiler cannot guarantee they point to valid memory.

2. **Call unsafe functions or methods**: some functions are marked `unsafe fn` because they have preconditions the compiler cannot verify. Calling them requires an `unsafe` block. Note that in Rust Edition 2024 and later, the body of an `unsafe fn` no longer implicitly allows unsafe operations – you still need explicit `unsafe` blocks within the function body.

3. **Access or modify mutable static variables**: global mutable state is inherently unsafe in a concurrent program because multiple threads could access it simultaneously.

4. **Implement unsafe traits**: some traits (like `Send` and `Sync`) have invariants that the compiler cannot check. Implementing them requires `unsafe impl` to signal that you have verified the invariants yourself.

5. **Access fields of unions**: Rust's `union` type is like a C union – the compiler does not know which variant is active, so reading a field requires `unsafe`.

Everything else – borrowing rules, lifetime checks, type safety, bounds checking – remains fully enforced inside `unsafe` blocks. Writing `unsafe` does not turn off the borrow checker.

## `unsafe` blocks

An `unsafe` block is a scoped region where you can use the five superpowers. The intent is to keep the unsafe surface area as small as possible:

```rust
// Rust
let x: i32 = 42;
let ptr: *const i32 = &x; // creating a raw pointer is safe

// Dereferencing the pointer requires unsafe
let value = unsafe { *ptr };
```

The raw pointer `ptr` is created in safe code – that is fine because creating a pointer does not do anything dangerous. The unsafe operation is *dereferencing* it, because the compiler cannot guarantee the pointer is still valid at that point.

## `unsafe` functions

Functions whose correctness depends on preconditions the caller must uphold are marked `unsafe fn`. The caller must wrap the invocation in an `unsafe` block:

```rust
// Rust
/// Reads `count` bytes starting at `ptr`.
///
/// # Safety
///
/// - `ptr` must point to at least `count` valid, initialized bytes.
/// - The memory must not be modified by another thread during this call.
unsafe fn read_bytes(ptr: *const u8, count: usize) -> Vec<u8> {
    let mut result = Vec::with_capacity(count);
    for i in 0..count {
        result.push(*ptr.add(i));
    }
    result
}

fn main() {
    let data = [1u8, 2, 3, 4, 5];
    let bytes = unsafe { read_bytes(data.as_ptr(), data.len()) };
    println!("{bytes:?}");
}
```

The `# Safety` doc comment is a strong convention in the Rust ecosystem. It documents the preconditions that callers must satisfy. This is comparable to Swift's documentation of preconditions on functions like `UnsafeMutablePointer.initialize(to:)`.

## Safe abstractions over unsafe code

The most common use of `unsafe` is to build a safe public interface on top of unsafe internals. The standard library does this extensively – `Vec`, `String`, `HashMap`, and most collection types use unsafe code internally for performance, but expose a safe API that users cannot misuse.

```rust
// Rust
struct FixedBuffer {
    data: [u8; 1024],
    len: usize,
}

impl FixedBuffer {
    fn new() -> Self {
        FixedBuffer {
            data: [0; 1024],
            len: 0,
        }
    }

    fn push(&mut self, byte: u8) -> Result<(), &'static str> {
        if self.len >= self.data.len() {
            return Err("buffer full");
        }
        self.data[self.len] = byte;
        self.len += 1;
        Ok(())
    }

    fn as_slice(&self) -> &[u8] {
        // This is safe because we maintain the invariant that
        // self.len <= self.data.len() and all bytes up to self.len
        // are initialized.
        &self.data[..self.len]
    }
}

let mut buf = FixedBuffer::new();
buf.push(72).unwrap();
buf.push(105).unwrap();
buf.as_slice() // [72, 105]
```

This example does not actually need `unsafe` because Rust's slice indexing is bounds-checked. But the principle applies: many standard library types use `unsafe` internally (e.g., `Vec` manages raw allocations with `std::alloc`) while exposing a fully safe API. As a user of these types, you benefit from the performance without bearing the verification burden.

Swift works the same way. The Swift standard library is implemented in Swift, C++, and some C, with low-level memory management code that the Swift compiler does not verify. The safe surface – `Array`, `Dictionary`, `String` – is what developers interact with.

## When you might encounter `unsafe`

Most Rust code does not need `unsafe`. Here are the common situations where it comes up:

### FFI (Foreign Function Interface)

Calling C functions requires `unsafe` because the Rust compiler cannot verify the C code's behavior:

```rust
// Rust
extern "C" {
    fn abs(input: i32) -> i32;
}

let result = unsafe { abs(-5) };
```

This is covered in detail in [Chapter 28](../../interop-and-ffi/c-ffi-basics/). If you have used Swift's C interop (importing C headers via bridging headers or module maps), the concept is familiar – you are trusting that the foreign function behaves according to its declared signature.

### Performance-critical code

Occasionally, avoiding bounds checks or using raw pointers yields measurable performance improvements. The standard library's sort implementation, for example, uses unsafe code to avoid redundant bounds checks in its inner loop. Application code rarely needs this level of optimization.

### Low-level system interfaces

Interacting with hardware, system calls, or memory-mapped I/O often requires raw pointers and unsafe code. This is the domain of operating systems, device drivers, and embedded firmware.

### Implementing concurrency primitives

Types like `Mutex`, `Arc`, and channels use unsafe code internally to manage shared mutable state with atomic operations. You use the safe API they provide; you do not write the unsafe internals unless you are building a new concurrency primitive.

## A note on WebAssembly

If you are targeting WebAssembly (covered in [Part X](../../rust-and-webassembly/introduction-to-webassembly/)), the Wasm sandbox limits what an `unsafe` bug can directly affect. Guest code does not get arbitrary access to the host's memory space or syscalls unless the host explicitly exposes those capabilities. But `unsafe` still deserves the same rigor: it can corrupt the guest's own linear memory, violate invariants, or trigger traps. Wasm reduces the default blast radius; it does not make `unsafe` code safe.

This makes Wasm an appealing target for Rust code that needs to be both performant and security-conscious.

## Key differences and gotchas

- **`unsafe` does not disable the borrow checker**: all of Rust's safety rules still apply inside an `unsafe` block, except for the five specific superpowers listed above.
- **Minimize the unsafe surface**: keep `unsafe` blocks as small as possible. Wrap them in safe functions with documented preconditions. This is a community norm, not a compiler requirement.
- **Undefined behavior is real**: if you violate the safety contract of an `unsafe` block (e.g., dereference a null pointer, create a dangling reference, cause a data race), the behavior is undefined – the same as in C or C++. The compiler may optimize based on the assumption that undefined behavior never occurs.
- **`unsafe` is greppable**: one of the design goals is that you can search a codebase for `unsafe` to find and audit all the places where safety depends on the programmer rather than the compiler.
- **No equivalent in Swift**: Swift does not have an `unsafe` keyword that relaxes compiler checks. Instead, unsafe operations in Swift are accessed through explicitly named types and functions (`UnsafePointer`, `UnsafeMutableBufferPointer`, `withUnsafeBytes`, etc.). The intent is the same – marking operations that bypass safety checks – but the mechanism is different. Rust's `unsafe` is a language-level scope; Swift's approach is an API-level convention.

## Further reading

- [Unsafe Rust](https://doc.rust-lang.org/book/ch19-01-unsafe-rust.html): The Rust Programming Language
- [The Rustonomicon](https://doc.rust-lang.org/nomicon/): the guide to unsafe Rust and its dark arts
- [std::ptr](https://doc.rust-lang.org/std/ptr/): raw pointer operations
- [Rust API Guidelines on Safety](https://rust-lang.github.io/api-guidelines/documentation.html#c-failure): documenting safety contracts
