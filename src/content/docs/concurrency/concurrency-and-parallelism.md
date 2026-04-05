---
title: Concurrency and Parallelism
sidebar:
  order: 23
---

Swift and Rust both care deeply about safe concurrency, but they achieve it through fundamentally different mechanisms. Swift uses actors, isolation rules, and `Sendable` checking to prevent data races, with the exact diagnostics depending on the language mode and compiler settings you enable. Rust prevents data races in safe code at compile time through its ownership system and two marker traits: `Send` and `Sync`. If your safe Rust code compiles, it is free of data races without needing runtime isolation checks.

## Spawning threads

### Swift

Swift offers several ways to run work on another thread. The most direct are `Thread` and Grand Central Dispatch:

```swift
// Swift
import Foundation

// Using Thread
let thread = Thread {
    print("Hello from a thread")
}
thread.start()

// Using GCD
DispatchQueue.global().async {
    print("Hello from GCD")
}
```

In modern Swift, you would more commonly use structured concurrency (`Task`, `TaskGroup`) rather than raw threads or GCD. But threads are the foundation that everything else builds on.

### Rust

Rust's standard library provides `std::thread::spawn`, which takes a closure and runs it on a new OS thread:

```rust
// Rust
use std::thread;

fn main() {
    let handle = thread::spawn(|| {
        println!("Hello from a thread");
    });

    handle.join().unwrap(); // wait for the thread to finish
}
```

`thread::spawn` returns a `JoinHandle<T>`, where `T` is the closure's return type. Calling `.join()` blocks the current thread until the spawned thread finishes and returns a `Result` containing the thread's return value (or a panic payload).

```rust
// Rust
use std::thread;

fn main() {
    let handle = thread::spawn(|| {
        42
    });

    let result = handle.join().unwrap();
    println!("Thread returned: {result}"); // 42
}
```

Unlike Swift's `Task`, `thread::spawn` creates an actual OS thread – there is no lightweight task scheduler in the standard library. For lightweight concurrency, you use an async runtime like tokio, covered in the next chapter.

## Moving data into threads

When a closure is sent to another thread, Rust's ownership system determines what data the closure can access. By default, closures capture variables by reference, but references to local variables cannot outlive the current scope – so the compiler will reject code that tries to borrow local data across a thread boundary.

The `move` keyword transfers ownership of captured variables into the closure:

```rust
// Rust
use std::thread;

fn main() {
    let name = String::from("Alice");

    let handle = thread::spawn(move || {
        println!("Hello, {name}");
    });

    // println!("{name}"); // compile error: value moved into the closure

    handle.join().unwrap();
}
```

After the `move`, `name` belongs to the spawned thread's closure. The original thread can no longer use it. This is how Rust prevents data races at the most basic level: if one thread owns the data, no other thread can access it.

In Swift, you can capture values in a closure sent to a different thread, but Swift relies on value semantics (for structs) or reference counting (for classes) to manage safety. When `Sendable` checking applies to the code in question, the compiler verifies that captured values conform to `Sendable`.

## The `Send` trait

`Send` is a marker trait that indicates a type can be safely transferred from one thread to another. Most types in Rust are `Send` – integers, strings, vectors, and any struct composed entirely of `Send` fields. The compiler automatically implements `Send` for types that qualify.

A type that is not `Send` cannot be moved to another thread. The canonical example is `Rc<T>` (reference-counted pointer), which uses non-atomic reference counting. Moving an `Rc` to another thread would allow two threads to modify the reference count simultaneously without synchronization – a data race. The compiler catches this:

```rust
// Rust – this does not compile
use std::rc::Rc;
use std::thread;

fn main() {
    let data = Rc::new(42);

    thread::spawn(move || {
        println!("{data}");
    });
    // error: `Rc<i32>` cannot be sent between threads safely
}
```

The fix is to use `Arc<T>` (atomic reference counting) instead, which is `Send`:

```rust
// Rust
use std::sync::Arc;
use std::thread;

fn main() {
    let data = Arc::new(42);
    let data_clone = Arc::clone(&data);

    let handle = thread::spawn(move || {
        println!("{data_clone}");
    });

    handle.join().unwrap();
}
```

### Comparison with Swift's `Sendable`

Swift's `Sendable` protocol serves the same conceptual purpose as Rust's `Send`: it marks types that are safe to pass across concurrency boundaries. The key differences:

- **Enforcement timing**: Rust enforces `Send` unconditionally at compile time. Swift's `Sendable` diagnostics depend on language mode and compiler settings, so the exact behavior is more configurable.
- **Reference types**: in Swift, a class can conform to `Sendable` if it is a `final` class with only immutable stored properties (or if it uses internal synchronization and is marked `@unchecked Sendable`). In Rust, there are no classes – structs and enums are `Send` if all their fields are.
- **Automatic conformance**: both languages derive thread-safety markers automatically. Rust implements `Send` for any type whose fields are all `Send`. Swift infers `Sendable` for value types with `Sendable` fields and for frozen enums/structs.

## The `Sync` trait

`Sync` is a companion to `Send`. A type `T` is `Sync` if `&T` (an immutable reference to `T`) is `Send` – meaning it is safe for multiple threads to hold shared references to the same value simultaneously.

Most immutable types are `Sync`. Types with interior mutability, like `Cell<T>` and `RefCell<T>`, are not `Sync` because they allow mutation through shared references without synchronization.

Together, `Send` and `Sync` form Rust's compile-time thread safety model:

- **`Send`**: the value can be transferred to another thread
- **`Sync`**: the value can be referenced from multiple threads at the same time

Swift has no direct equivalent of `Sync` as a separate concept. The `Sendable` protocol covers both transferring and sharing, and actors handle shared mutable state through runtime isolation.

## Shared state with `Mutex<T>`

When multiple threads need to read and write the same data, Rust uses `Mutex<T>` – a mutual exclusion lock that wraps the protected data:

```rust
// Rust
use std::sync::Mutex;

let counter = Mutex::new(0);

{
    let mut value = counter.lock().unwrap();
    *value += 1;
} // lock is released when `value` goes out of scope
```

Several things are notable about Rust's mutex design:

1. **The data lives inside the mutex.** You cannot access the data without locking. In C or Swift, a lock and the data it protects are separate, and nothing stops you from accessing the data without acquiring the lock. In Rust, the type system enforces this.

2. **Lock returns a guard.** `lock()` returns a `MutexGuard<T>` that implements `Deref` and `DerefMut`, so you can use it like a reference to the inner value. When the guard is dropped, the lock is automatically released.

3. **`lock()` returns a `Result`.** If a thread panics while holding the lock, the mutex becomes "poisoned." Subsequent calls to `lock()` return `Err`, letting you detect the corrupted state. Calling `.unwrap()` is common when you want to propagate the panic.

### Comparison with Swift actors

In Swift, the primary mechanism for protecting shared mutable state is actors:

```swift
// Swift
actor Counter {
    var value = 0

    func increment() {
        value += 1
    }

    func get() -> Int {
        value
    }
}

let counter = Counter()
await counter.increment()
let current = await counter.get()
```

Actors provide an ergonomic API – you just `await` access and the runtime serializes it. But there are tradeoffs:

- **Actors require async contexts.** You need `await` to access an actor's state, which means the caller must be in an async function. Mutexes work in any context.
- **Actors have runtime overhead.** The Swift runtime manages actor isolation, message queuing, and executor scheduling. A mutex is a simple OS-level lock with minimal overhead.
- **Actors protect an entire object.** A mutex wraps a specific piece of data. You can have fine-grained locking with multiple mutexes, while actors serialize all access to their entire state.

Swift also has `NSLock`, `os_unfair_lock`, and other lock primitives, but actors are the recommended approach in modern Swift.

## The `Arc<Mutex<T>>` pattern

A `Mutex` alone cannot be shared between threads because each thread needs its own handle to it. `Arc<T>` (atomic reference counting) provides shared ownership, and combining it with `Mutex<T>` gives you thread-safe shared mutable state:

```rust
// Rust
use std::sync::{Arc, Mutex};
use std::thread;

fn main() {
    let counter = Arc::new(Mutex::new(0));
    let mut handles = vec![];

    for _ in 0..10 {
        let counter = Arc::clone(&counter);
        let handle = thread::spawn(move || {
            let mut value = counter.lock().unwrap();
            *value += 1;
        });
        handles.push(handle);
    }

    for handle in handles {
        handle.join().unwrap();
    }

    println!("Final count: {}", counter.lock().unwrap()); // 10
}
```

Each thread gets its own `Arc` clone (incrementing the reference count), and the `Mutex` inside ensures only one thread accesses the data at a time. This pattern is Rust's equivalent of what you would achieve with a Swift actor or a class protected by a lock.

Note the similarity to Swift's pattern of sharing a reference type across tasks:

```swift
// Swift
actor Counter {
    var value = 0
    func increment() { value += 1 }
    func get() -> Int { value }
}

let counter = Counter()
await withTaskGroup(of: Void.self) { group in
    for _ in 0..<10 {
        group.addTask {
            await counter.increment()
        }
    }
}
print("Final count: \(await counter.get())")
```

The actor version is more concise and does not require manual reference counting, but the Rust version has no runtime overhead beyond the mutex and atomic operations.

## `RwLock<T>`

When you have many readers and few writers, `Mutex` is unnecessarily restrictive – it blocks all access while any thread holds the lock, even for reads. `RwLock<T>` (read-write lock) allows multiple concurrent readers or a single writer:

```rust
// Rust
use std::sync::RwLock;

let config = RwLock::new(String::from("default"));

// Multiple readers can access simultaneously
{
    let value = config.read().unwrap();
}

// Only one writer at a time, and no readers while writing
{
    let mut value = config.write().unwrap();
    *value = String::from("updated");
}
```

`RwLock` is useful for configuration, caches, and other data that is read far more often than it is written. Like `Mutex`, you typically wrap it in an `Arc` for sharing across threads.

Swift has no direct equivalent in the standard library, but `os_unfair_lock` and GCD concurrent queues with barriers serve a similar role.

## Channels

Channels provide a way for threads to communicate by sending messages rather than sharing memory. Rust's standard library includes `std::sync::mpsc` – a multi-producer, single-consumer channel:

```rust
// Rust
use std::sync::mpsc;
use std::thread;

fn main() {
    let (tx, rx) = mpsc::channel();

    thread::spawn(move || {
        tx.send("hello from the thread").unwrap();
    });

    let message = rx.recv().unwrap();
    println!("{message}");
}
```

`mpsc::channel()` returns a transmitter (`tx`) and a receiver (`rx`). The transmitter can be cloned to allow multiple producers:

```rust
// Rust
use std::sync::mpsc;
use std::thread;

fn main() {
    let (tx, rx) = mpsc::channel();

    for i in 0..3 {
        let tx = tx.clone();
        thread::spawn(move || {
            tx.send(format!("message {i}")).unwrap();
        });
    }

    drop(tx); // drop the original transmitter so the receiver knows when all senders are done

    for message in rx {
        println!("{message}");
    }
}
```

The receiver implements `Iterator`, so you can use a `for` loop to process messages until all transmitters are dropped.

### Comparison with Swift's `AsyncStream`

Swift's closest equivalent is `AsyncStream`, which provides a channel-like interface for producing and consuming values asynchronously:

```swift
// Swift
let stream = AsyncStream<String> { continuation in
    Task {
        continuation.yield("hello from the task")
        continuation.finish()
    }
}

for await message in stream {
    print(message)
}
```

The main differences:

- **`mpsc::channel` is synchronous.** `recv()` blocks the current thread. `AsyncStream` is async and suspends the task.
- **`mpsc` supports multiple producers natively** by cloning the transmitter. `AsyncStream` is single-producer by default; for multiple producers, you use `AsyncStream.makeStream()` and share the continuation.
- **Ownership transfer**: when you send a value through a Rust channel, ownership is transferred to the receiver. The sender can no longer use the value. In Swift, value types preserve value semantics and reference types are retained.

### Bounded channels

`mpsc::channel()` is unbounded – senders never block. For bounded channels (where the sender blocks when the buffer is full), use `mpsc::sync_channel`:

```rust
// Rust
use std::sync::mpsc;
use std::thread;

fn main() {
    let (tx, rx) = mpsc::sync_channel(2); // buffer size of 2

    thread::spawn(move || {
        for i in 0..5 {
            tx.send(i).unwrap(); // blocks when buffer is full
            println!("Sent {i}");
        }
    });

    for value in rx {
        println!("Received {value}");
    }
}
```

## How Rust prevents data races at compile time

The interaction between ownership, borrowing, `Send`, and `Sync` creates a compile-time guarantee that safe Rust programs are free of data races. Here is how the pieces fit together:

1. **Ownership ensures exclusive access.** A value has exactly one owner. Moving it to another thread transfers ownership – the original thread can no longer access it.

2. **Borrowing rules prevent conflicting access.** At any point, a value can have either one mutable reference or any number of immutable references, but not both. This eliminates the possibility of one thread writing while another reads.

3. **`Send` controls what can cross thread boundaries.** Types that are not safe to transfer (like `Rc<T>`) are not `Send`, so the compiler prevents you from moving them to another thread.

4. **`Sync` controls what can be shared.** Types that are not safe to share via references (like `Cell<T>`) are not `Sync`, so the compiler prevents you from sharing references to them across threads.

5. **`Mutex` and `RwLock` provide interior mutability with synchronization.** They are both `Send` and `Sync` (when their inner type is `Send`), so they can be shared across threads. But access to the inner data is gated by locking, which the type system enforces.

In Swift, data race safety is achieved through actors (runtime isolation), `Sendable` (compile-time transfer checks), and compiler-enforced isolation rules. Rust's approach pushes everything into the type system and the borrow checker, resulting in zero runtime cost but a steeper learning curve.

## Key differences and gotchas

- **No runtime isolation**: Rust has no actors or runtime concurrency manager. Thread safety is enforced entirely at compile time through the type system.
- **`Send` vs `Sendable`**: both serve the same purpose (marking types safe to transfer across concurrency boundaries), but Rust's `Send` is always enforced, while Swift's `Sendable` diagnostics depend on the language mode and compiler settings in use.
- **Data lives inside the lock**: `Mutex<T>` wraps the data it protects, so you cannot accidentally access the data without locking. In Swift, locks and the data they protect are typically separate.
- **Poisoned mutexes**: if a thread panics while holding a Rust `Mutex`, the mutex is poisoned and subsequent `lock()` calls return `Err`. Swift's `NSLock` has no equivalent mechanism.
- **`Arc` vs automatic ARC**: Rust requires you to explicitly opt into reference counting with `Arc<T>`. Swift applies automatic reference counting to all class instances.
- **Move semantics in channels**: sending a value through a Rust channel transfers ownership. The sender can no longer use the value. Swift copies value types and retains reference types.
- **No `async` needed for mutex access**: unlike Swift actors (which require `await`), Rust's `Mutex` works in synchronous code. The lock call blocks the thread rather than suspending a task.
- **Deadlocks are still possible**: Rust prevents data races at compile time, but it does not prevent deadlocks. You can still create deadlocks by acquiring multiple locks in inconsistent orders or by locking a non-reentrant mutex recursively.

## Further reading

- [Fearless Concurrency](https://doc.rust-lang.org/book/ch16-00-concurrency.html): The Rust Programming Language
- [`std::thread`](https://doc.rust-lang.org/std/thread/index.html): Rust standard library documentation
- [`std::sync`](https://doc.rust-lang.org/std/sync/index.html): `Mutex`, `RwLock`, `Arc`, and other synchronization primitives
- [`std::sync::mpsc`](https://doc.rust-lang.org/std/sync/mpsc/index.html): multi-producer, single-consumer channels
- [Send and Sync](https://doc.rust-lang.org/nomicon/send-and-sync.html): The Rustonomicon
- [Swift Sendable and Concurrency](https://developer.apple.com/documentation/swift/sendable): Apple Developer Documentation
