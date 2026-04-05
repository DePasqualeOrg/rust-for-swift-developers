---
title: Async Rust
sidebar:
  order: 24
---

Both Swift and Rust have `async`/`await` syntax that looks deceptively similar. Underneath, the two languages take very different approaches. Swift ships a built-in cooperative thread pool and executor – when you write `async` in Swift, the runtime knows how to schedule and run your code. Rust has no built-in async runtime. The language provides the syntax and the `Future` trait, but you must bring your own executor.

## `async fn` and `.await`

The surface syntax is close to Swift's:

```swift
// Swift
func fetchData(from url: URL) async throws -> Data {
    let (data, _) = try await URLSession.shared.data(from: url)
    return data
}
```

```rust
// Rust (requires an async runtime to execute)
async fn fetch_data(url: &str) -> Result<String, reqwest::Error> {
    let body = reqwest::get(url).await?.text().await?;
    Ok(body)
}
```

The differences in syntax are small but consistent:

- Rust puts `async` before `fn`, while Swift puts `async` after the return type
- Rust uses `.await` as a postfix operator (with a dot), while Swift uses `await` as a prefix keyword
- Rust's `.await` chains naturally with `?` for error propagation: `something.await?`

## Futures: lazy vs eager

This is the most important conceptual difference between Swift and Rust async. In Swift, an async call does not produce a lazy future value that you can stash away unstarted. Once execution reaches the call, the callee begins running immediately until it either suspends or returns.

In Rust, calling an async function does nothing. It returns a `Future` – a value that represents a computation that has not started yet. No work happens until something polls the future:

```rust
// Rust
async fn compute() -> i32 {
    println!("computing...");
    42
}

// This does NOT print anything – it only creates a Future
// let future = compute();

// The future must be .awaited or spawned on an executor to run
// let result = future.await; // now it prints "computing..." and returns 42
```

This laziness has practical consequences:

- **No wasted work**: if you create a future but never poll it, no computation happens
- **Composability**: you can build up complex future pipelines before any execution begins
- **No implicit concurrency**: nothing runs in the background unless you explicitly spawn it

In Swift, ordinary async calls are not first-class lazy values. If you want laziness, you typically wrap the operation in a closure and invoke it later rather than storing an unstarted computation object.

## The `Future` trait

Rust's `Future` trait is the foundation of async:

```rust
// Rust – simplified for illustration (this is from the standard library)
trait Future {
    type Output;
    fn poll(self: Pin<&mut Self>, cx: &mut Context<'_>) -> Poll<Self::Output>;
}

enum Poll<T> {
    Ready(T),
    Pending,
}
```

When you write `async fn`, the compiler transforms it into a state machine that implements `Future`. Each `.await` point becomes a state transition. The executor repeatedly calls `poll` on the future: if it returns `Poll::Pending`, the executor parks the future and works on something else; if it returns `Poll::Ready(value)`, the future is complete.

Swift does not expose an equivalent trait. Async functions in Swift are opaque to the caller – the runtime handles all scheduling internally. This makes Swift's model simpler to use but less flexible to customize.

## Why Rust needs an explicit runtime

Swift ships a cooperative thread pool as part of the language runtime. When you `await` something in Swift, the runtime's executor manages suspension and resumption. You never think about it.

Rust's standard library intentionally does not include an async runtime. The reasoning:

- **Different use cases need different executors.** A web server wants a multi-threaded work-stealing scheduler. An embedded system wants a single-threaded executor with no heap allocation. A WebAssembly module may need an executor that integrates with the browser's event loop. A one-size-fits-all runtime would force tradeoffs on users who cannot afford them.
- **Zero-cost abstraction.** Rust's async/await compiles futures into state machines with no heap allocation for the futures themselves (unless you box them). An embedded runtime would impose overhead that some users do not want.
- **Ecosystem flexibility.** Libraries can be runtime-agnostic by programming against the `Future` trait rather than a specific executor.

The tradeoff is that getting started with async Rust requires choosing and configuring a runtime, which adds friction compared to Swift's batteries-included approach.

## Tokio: the most common async runtime

[Tokio](https://tokio.rs) is the most widely used async runtime in Rust. It provides a multi-threaded executor, async I/O, timers, channels, and other utilities. Here is a minimal example:

```rust
// Rust
// [dependencies]
// tokio = { version = "1", features = ["full"] }

#[tokio::main]
async fn main() {
    let result = fetch().await;
    println!("{result}");
}

async fn fetch() -> &'static str {
    // In a real application, this would do async I/O
    "hello from async"
}
```

The `#[tokio::main]` attribute macro transforms `main` into a synchronous function that creates a tokio runtime and blocks on the async body. It roughly desugars to:

```rust
// Rust
fn main() {
    let rt = tokio::runtime::Runtime::new().unwrap();
    rt.block_on(async {
        let result = fetch().await;
        println!("{result}");
    });
}

async fn fetch() -> &'static str {
    "hello from async"
}
```

Swift has no equivalent ceremony – your `@main` app or function can simply be `async`:

```swift
// Swift
@main
struct MyApp {
    static func main() async {
        let result = await fetch()
        print(result)
    }

    static func fetch() async -> String {
        "hello from async"
    }
}
```

### Spawning tasks with tokio

Tokio's `tokio::spawn` is the closest equivalent to Swift's `Task { }`. It schedules a future on the runtime and returns a `JoinHandle`:

```rust
// Rust
#[tokio::main]
async fn main() {
    let handle = tokio::spawn(async {
        // this runs concurrently
        expensive_computation().await
    });

    // do other work...

    let result = handle.await.unwrap();
    println!("{result}");
}

async fn expensive_computation() -> i32 {
    42
}
```

Compare with Swift:

```swift
// Swift
let task = Task {
    await expensiveComputation()
}

// do other work...

let result = await task.value
```

The structure is similar, but note that `tokio::spawn` requires the future to be `Send` (since it may be executed on a different thread), while Swift's `Task` requires its closure to be `@Sendable`.

Tokio also provides `tokio::spawn_blocking` for running synchronous, blocking code on a dedicated thread pool without blocking the async executor:

```rust
// Rust
#[tokio::main]
async fn main() {
    let result = tokio::task::spawn_blocking(|| {
        // CPU-intensive or blocking I/O work
        std::thread::sleep(std::time::Duration::from_secs(1));
        42
    }).await.unwrap();

    println!("{result}");
}
```

## `async` blocks

Rust has `async` blocks, which create anonymous futures inline:

```rust
// Rust
#[tokio::main]
async fn main() {
    let future_a = async {
        println!("Task A");
        1
    };

    let future_b = async {
        println!("Task B");
        2
    };

    // Run both concurrently
    let (a, b) = tokio::join!(future_a, future_b);
    println!("{a} + {b} = {}", a + b);
}
```

These are similar to creating a `Task` closure in Swift, but with a difference: async blocks in Rust are lazy. They produce a `Future` that does nothing until awaited or spawned. In Swift, wrapping code in `Task { }` starts it immediately.

### `tokio::join!` and `tokio::select!`

Tokio provides macros for common concurrency patterns:

- **`tokio::join!`**: runs multiple futures concurrently and waits for all of them (like Swift's `async let` or `withTaskGroup`)
- **`tokio::select!`**: waits for the first of several futures to complete (similar to racing concurrent tasks in Swift using task groups with cancellation)

```rust
// Rust
use tokio::time::{sleep, Duration};

#[tokio::main]
async fn main() {
    // Run concurrently, wait for both
    let (a, b) = tokio::join!(
        async { sleep(Duration::from_millis(100)).await; 1 },
        async { sleep(Duration::from_millis(200)).await; 2 },
    );
    println!("join: {a}, {b}");

    // Wait for the first to complete
    tokio::select! {
        val = async { sleep(Duration::from_millis(100)).await; "fast" } => {
            println!("select: {val}");
        }
        val = async { sleep(Duration::from_millis(500)).await; "slow" } => {
            println!("select: {val}");
        }
    }
}
```

The Swift equivalents:

```swift
// Swift
// Concurrent execution with async let
async let a = delayedValue(1, for: .milliseconds(100))
async let b = delayedValue(2, for: .milliseconds(200))
let (resultA, resultB) = await (a, b)

func delayedValue(_ value: Int, for duration: Duration) async -> Int {
    try? await Task.sleep(for: duration)
    return value
}
```

## The `Stream` trait

Rust's `Stream` trait (from the `futures` crate, with plans for eventual inclusion in the standard library) is the async equivalent of `Iterator`. It produces a sequence of values over time, similar to Swift's `AsyncSequence`:

```swift
// Swift
func numbers() -> AsyncStream<Int> {
    AsyncStream { continuation in
        for i in 0..<5 {
            continuation.yield(i)
        }
        continuation.finish()
    }
}

for await n in numbers() {
    print(n)
}
```

```rust
// Rust
// [dependencies]
// tokio-stream = "0.1"
// tokio = { version = "1", features = ["full"] }

use tokio_stream::StreamExt;

#[tokio::main]
async fn main() {
    let mut stream = tokio_stream::iter(0..5);

    // Note: tokio::pin! is not needed here because tokio_stream::iter
    // returns a type that implements Unpin. For streams that are not
    // Unpin (e.g., those produced by async_stream), you would need to
    // pin them with tokio::pin!(stream) before calling .next().

    while let Some(n) = stream.next().await {
        println!("{n}");
    }
}
```

The `Stream` trait mirrors `Future` in structure:

```rust
// Rust – from the futures crate (simplified)
trait Stream {
    type Item;
    fn poll_next(self: Pin<&mut Self>, cx: &mut Context<'_>) -> Poll<Option<Self::Item>>;
}
```

Each call to `poll_next` returns `Poll::Ready(Some(item))` for the next value, `Poll::Ready(None)` when the stream is exhausted, or `Poll::Pending` when no value is available yet.

The `tokio-stream` crate provides utilities for working with streams, including `StreamExt` (which adds `next()`, `map()`, `filter()`, and other combinators) and adapters for converting between channels and streams.

Tokio also provides async channels that work well as stream producers:

```rust
// Rust
use tokio::sync::mpsc;
use tokio_stream::wrappers::ReceiverStream;
use tokio_stream::StreamExt;

#[tokio::main]
async fn main() {
    let (tx, rx) = mpsc::channel(32);

    tokio::spawn(async move {
        for i in 0..5 {
            tx.send(i).await.unwrap();
        }
    });

    let mut stream = ReceiverStream::new(rx);

    while let Some(value) = stream.next().await {
        println!("{value}");
    }
}
```

## Pinning

You may have noticed `Pin<&mut Self>` in the `Future` and `Stream` trait definitions. Pinning is a concept unique to Rust – it guarantees that a value will not be moved in memory after it has been pinned.

Why does this matter? When the compiler transforms an async function into a state machine, the resulting `Future` may contain self-referential data – fields that point to other fields within the same struct. If the future were moved to a different memory location, those internal pointers would become dangling. `Pin` prevents this by making it a compile-time error to move a pinned value.

In practice, you rarely interact with `Pin` directly:

- `.await` handles pinning automatically
- `tokio::pin!` pins a local future or stream on the stack
- `Box::pin(future)` pins a future on the heap (useful for returning `Pin<Box<dyn Future>>`)

```rust
// Rust
use std::pin::Pin;
use std::future::Future;

fn make_future() -> Pin<Box<dyn Future<Output = i32> + Send>> {
    Box::pin(async {
        42
    })
}

#[tokio::main]
async fn main() {
    let result = make_future().await;
    println!("{result}");
}
```

Swift has no equivalent to `Pin` because Swift's async functions are not compiled into self-referential state machines in the same way. The Swift runtime manages async frame storage separately.

## Async and WebAssembly

Rust's async story intersects with WebAssembly in interesting ways. Historically, running async Rust in Wasm has been challenging because Wasm modules run single-threaded and have no built-in event loop. You would use `wasm-bindgen-futures` to bridge Rust futures with JavaScript promises in the browser, or implement a custom single-threaded executor.

The landscape is evolving:

- **WASI 0.2** introduced the component-model foundation that newer async designs build on
- **WASI 0.3** is the effort aimed at adding native async concepts to the component model
- **Stack switching** is a WebAssembly proposal that would allow efficient coroutine-style suspension at the Wasm level, which could eventually make async Rust in Wasm as natural as async on native platforms

For now, when targeting Wasm, you should be aware that the async runtime you use must support the target environment. Tokio's full runtime is not generally the right fit for browser Wasm or today's component-model workflows; instead, you would use target-specific tools like `wasm-bindgen-futures` (for the browser) or follow the still-emerging WASI 0.3 async work for component-based environments.

## Key differences and gotchas

- **Lazy vs eager**: Rust futures do nothing until polled. Swift tasks start immediately. This is the single most common source of confusion for Swift developers learning async Rust.
- **No built-in runtime**: you must choose an async runtime (tokio, async-std, smol, etc.) and add it as a dependency. Swift's runtime is always available.
- **`Send` bounds on spawned tasks**: `tokio::spawn` requires the future to be `Send`, since it may run on any thread. This can cause friction when working with non-`Send` types. Swift's `Task` has similar `@Sendable` requirements but they can be less visible.
- **Pinning**: Rust requires futures to be pinned before polling because they may be self-referential. This is invisible when using `.await` but surfaces when storing futures in collections or returning them as trait objects.
- **No `async let`**: Rust does not have Swift's `async let` syntax for structured concurrency. Instead, you use `tokio::join!` or spawn tasks manually.
- **Cancellation**: in Swift, structured tasks are automatically cancelled when their parent scope exits. In Rust, dropping a future cancels it (no more polling), but there is no built-in structured cancellation hierarchy. Tokio provides `CancellationToken` and `JoinHandle::abort()` for explicit cancellation.
- **Colored functions**: both languages have the "colored function" property – you can only call async functions from async contexts (or by using a blocking bridge like `block_on`). This is often called the "function coloring problem."
- **No `actor` keyword**: Rust has no built-in actor abstraction. You build actor patterns manually using channels and `tokio::spawn`, or use a crate like `actix`.
- **Streams are not yet in `std`**: unlike Swift's `AsyncSequence` (which is in the standard library), Rust's `Stream` trait lives in the `futures` crate. There are plans to stabilize it in `std`, but as of now it requires a dependency.

## Further reading

- [Asynchronous Programming in Rust](https://rust-lang.github.io/async-book/): the official async Rust book
- [Tokio Tutorial](https://tokio.rs/tokio/tutorial): getting started with the most popular runtime
- [The `Future` trait](https://doc.rust-lang.org/std/future/trait.Future.html): standard library documentation
- [Pin and Unpin](https://doc.rust-lang.org/std/pin/index.html): standard library documentation on pinning
- [futures crate](https://docs.rs/futures/latest/futures/): utilities for working with futures and streams
- [tokio-stream](https://docs.rs/tokio-stream/latest/tokio_stream/): stream utilities for tokio
- [WASI 0.3 Async](https://github.com/WebAssembly/WASI/blob/main/wasip3/README.md): the WASI async proposal
