---
title: Understanding Drop and RAII
sidebar:
  order: 21
---

When a value goes out of scope in Rust, the compiler inserts code to clean it up. This is not garbage collection – there is no runtime deciding when to reclaim memory. The cleanup happens deterministically, at a precisely known point in the program, and it applies to all resources, not just memory. This pattern is called RAII (Resource Acquisition Is Initialization), and it is central to how Rust manages files, locks, network connections, and anything else that needs cleanup.

Swift developers already understand deterministic cleanup through ARC: when the last strong reference to a class instance goes away, `deinit` runs immediately. Rust achieves a similar result through the `Drop` trait and scope-based ownership, but without reference counting.

## The `Drop` trait

The `Drop` trait is Rust's equivalent of Swift's `deinit`. It has a single method, `drop`, which the compiler calls automatically when a value goes out of scope:

```rust
// Rust
struct FileHandle {
    name: String,
}

impl Drop for FileHandle {
    fn drop(&mut self) {
        println!("Closing file: {}", self.name);
    }
}

fn main() {
    let _f = FileHandle {
        name: String::from("data.txt"),
    };
    println!("File is open");
    // _f is dropped here – "Closing file: data.txt" prints
}
```

The Swift equivalent:

```swift
// Swift
class FileHandle {
    let name: String
    init(name: String) { self.name = name }
    deinit { print("Closing file: \(name)") }
}

func example() {
    let f = FileHandle(name: "data.txt")
    print("File is open")
    // f is deallocated here if no other references exist
}
```

The output is the same in both cases – the cleanup message prints after "File is open." But the mechanisms differ in an important way:

- **Swift's `deinit`** runs when the reference count reaches zero. If another variable holds a reference to the same object, `deinit` is delayed until the last reference goes away.
- **Rust's `drop`** runs when the owning variable goes out of scope. There is no reference count. Each value has exactly one owner, and when that owner's scope ends, the value is dropped.

## RAII: tying resources to scope

RAII is a pattern from C++ that Rust adopts fully: a resource (memory, a file, a lock, a network connection) is acquired when a value is created and released when the value is destroyed. Because Rust drops values deterministically at the end of their scope, this means resources are always cleaned up – even if the function returns early due to an error.

```rust
// Rust
use std::fs::File;
use std::io::{self, Write};

fn write_log(message: &str) -> io::Result<()> {
    let mut file = File::create("log.txt")?;
    writeln!(file, "{message}")?;
    // file is closed here automatically when it goes out of scope
    Ok(())
}

fn main() {
    let _ = write_log("application started");
}
```

There is no explicit `file.close()` call. The `File` type implements `Drop`, and the compiler ensures it runs when `file` goes out of scope, regardless of whether the function succeeds or fails. If `writeln!` returns an error and `?` causes an early return, the file is still closed.

In Swift, you get similar behavior with class instances and `deinit`, but it depends on ARC. If you store a reference to the file handle elsewhere, the cleanup is deferred. Rust's scope-based model is simpler to reason about: you can always see exactly where the cleanup will happen by looking at the closing brace.

Swift also has `defer` for scope-based cleanup of non-class resources:

```swift
// Swift
func writeLog(message: String) throws {
    let file = try FileHandle(forWritingTo: URL(fileURLWithPath: "log.txt"))
    defer { file.closeFile() }
    file.write(message.data(using: .utf8)!)
    // file.closeFile() runs here, even if an error occurs
}
```

Rust's RAII makes `defer` unnecessary – the cleanup is baked into the type itself.

## Drop order

When a scope contains multiple values, Rust drops them in reverse declaration order – the last declared value is dropped first:

```rust
// Rust
struct Named(&'static str);

impl Drop for Named {
    fn drop(&mut self) {
        println!("Dropping {}", self.0);
    }
}

fn main() {
    let _a = Named("first");
    let _b = Named("second");
    let _c = Named("third");
    // Drops: third, second, first
}
```

This reverse order is important for correctness: later variables may reference or depend on earlier ones, so they need to be cleaned up first. The same principle applies to struct fields – they are dropped in declaration order (first field first, last field last). Note that this differs from the local variable rule.

Swift does not guarantee a specific deallocation order for local variables, since `deinit` timing depends on when ARC determines the last reference is released. In practice, Swift usually deallocates in a similar order at the end of a scope, but the language does not make this a guarantee you can rely on.

## Early cleanup with `std::mem::drop`

Sometimes you want to release a resource before the end of its scope. In Rust, you cannot call `drop()` directly – the compiler would try to drop the value again at the end of the scope, leading to a double-free. Instead, you pass the value to `std::mem::drop`, which takes ownership and triggers the `Drop` implementation:

```rust
// Rust
struct Connection {
    id: u32,
}

impl Drop for Connection {
    fn drop(&mut self) {
        println!("Closing connection {}", self.id);
    }
}

fn main() {
    let conn = Connection { id: 1 };
    println!("Using connection");

    drop(conn); // explicitly drop early
    println!("Connection is now closed");

    // conn is no longer valid here – using it would be a compile error
}
```

`drop` is just a function that takes ownership of its argument and immediately drops it. Because the value has been moved into `drop`, the compiler knows it is gone and will not try to drop it again at the end of the scope.

A common use case is releasing a lock early:

```rust
// Rust
use std::sync::Mutex;

fn main() {
    let data = Mutex::new(vec![1, 2, 3]);

    {
        let mut guard = data.lock().unwrap();
        guard.push(4);
        // guard is dropped at the end of this block, releasing the lock
    }

    // Or equivalently:
    let mut guard = data.lock().unwrap();
    guard.push(5);
    drop(guard); // release the lock early

    println!("{:?}", data.lock().unwrap());
}
```

In Swift, you might use an inner scope or `defer` to achieve the same effect. There is no direct equivalent to `std::mem::drop` because Swift relies on ARC rather than scope-based ownership.

## `Drop` and ownership

The `Drop` trait integrates deeply with Rust's ownership system. When you move a value, the original variable no longer owns it, so `drop` is not called on the original:

```rust
// Rust
struct Resource {
    name: String,
}

impl Drop for Resource {
    fn drop(&mut self) {
        println!("Dropping {}", self.name);
    }
}

fn consume(r: Resource) {
    println!("Consumed {}", r.name);
    // r is dropped here
}

fn main() {
    let r = Resource {
        name: String::from("database"),
    };
    consume(r);
    // r has been moved – nothing to drop here
    // "Dropping database" prints once, inside consume
}
```

This is one of the guarantees that ownership provides: every value is dropped exactly once. There is no double-free, no use-after-free, and no forgotten cleanup. The compiler enforces this at compile time.

## `Drop` and `Copy` are mutually exclusive

A type cannot implement both `Drop` and `Copy`. This is a deliberate design choice. `Copy` types are duplicated by simple bitwise copying – there is no special logic when a copy is made or when the original goes away. `Drop` types have custom cleanup logic that must run exactly once. If a type could be both `Copy` and `Drop`, the compiler could not guarantee that `drop` runs exactly once, because copies would create multiple instances that each think they own the resource.

```rust
// Rust – this does not compile
// #[derive(Copy, Clone)]
// struct Handle {
//     fd: i32,
// }
//
// impl Drop for Handle {
//     fn drop(&mut self) {
//         println!("Closing fd {}", self.fd);
//     }
// }
// Error: the trait `Copy` cannot be implemented for this type
// because the type has a destructor
```

If you need a type that can be copied and also needs cleanup, you need to manage the resource through a smart pointer like `Rc` or `Arc`, which handle the shared ownership and ensure cleanup happens only once.

In Swift, this distinction does not arise because structs (value types) do not have `deinit` and classes (reference types) do not have copy semantics. The two concepts are separated by the struct/class divide rather than by trait constraints.

## RAII beyond memory

The RAII pattern is not limited to memory management. Any resource that needs cleanup benefits from being tied to a scope:

- **Files**: `std::fs::File` implements `Drop` to close the file descriptor
- **Locks**: `MutexGuard` implements `Drop` to release the lock
- **Temporary files**: a temporary file handle can delete the file on drop
- **Database transactions**: a transaction wrapper can roll back uncommitted changes on drop
- **Timers and instrumentation**: a timing guard can log elapsed time on drop

```rust
// Rust
use std::time::Instant;

struct Timer {
    label: String,
    start: Instant,
}

impl Timer {
    fn new(label: &str) -> Self {
        Timer {
            label: label.to_string(),
            start: Instant::now(),
        }
    }
}

impl Drop for Timer {
    fn drop(&mut self) {
        let elapsed = self.start.elapsed();
        println!("{}: {elapsed:?}", self.label);
    }
}

fn main() {
    let _timer = Timer::new("main");
    // ... do some work ...
    let mut sum = 0u64;
    for i in 0..1_000_000 {
        sum += i;
    }
    println!("Sum: {sum}");
    // _timer is dropped here, printing the elapsed time
}
```

This pattern is clean and composable. You can stack multiple RAII guards in a single scope, and they are all cleaned up in reverse order. The compiler guarantees that cleanup happens even if the function returns early, and no `defer` blocks or manual cleanup calls are needed.

## Key differences and gotchas

- **Scope-based vs. reference-count-based**: Rust drops values when their owning scope ends. Swift drops class instances when the reference count reaches zero. Both are deterministic, but the trigger differs.
- **No `deinit` for structs in Swift**: Swift's `deinit` is only available on classes. Rust's `Drop` works on any type – structs, enums, or any other owned value.
- **Exactly-once guarantee**: Rust guarantees that `drop` is called exactly once per value. Moves transfer ownership, preventing double drops. Swift's ARC also provides this guarantee for class instances, but through a different mechanism.
- **Cannot call `drop` directly**: You cannot write `value.drop()` in Rust. Use `std::mem::drop(value)` or let the value go out of scope. Calling `value.drop()` directly is a compile error because it would leave the value in an invalid state while it is still technically in scope.
- **`Drop` prevents `Copy`**: If your type needs custom cleanup, it cannot be `Copy`. Design your types accordingly – use `Clone` instead if you need explicit duplication.
- **No finalizers**: Rust's `Drop` is not a finalizer. It runs synchronously, deterministically, and inline with the rest of your code. There is no deferred or asynchronous cleanup.
- **Drop in collections**: When a `Vec<T>` is dropped, it drops all of its elements first, then frees the backing memory. The same applies to `HashMap`, `String`, and other owning collections. This recursive drop behavior is automatic.

## Further reading

- [The Drop Trait](https://doc.rust-lang.org/book/ch15-03-drop.html): The Rust Programming Language
- [std::ops::Drop](https://doc.rust-lang.org/std/ops/trait.Drop.html): standard library documentation
- [std::mem::drop](https://doc.rust-lang.org/std/mem/fn.drop.html): the `drop` function
- [RAII](https://doc.rust-lang.org/rust-by-example/scope/raii.html): Rust by Example
- [Destructors](https://doc.rust-lang.org/reference/destructors.html): Rust reference
