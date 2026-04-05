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

- Rust puts `async` before `fn`, while Swift puts `async` after the parameter list and before `throws` and the return type.
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
- **Explicit concurrency**: combinators such as `join!` can poll several futures within one task; spawning creates a separately scheduled task.

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

An `async fn` produces a state machine implementing `Future`. Polling advances its work until it completes or must wait. Before returning `Poll::Pending`, a future must arrange for the current task’s waker to be notified when progress becomes possible. The executor can then poll it again; it need not busy-poll waiting futures. `Poll::Ready(value)` completes the operation.

Swift does not expose an equivalent trait. Async functions in Swift are opaque to the caller – the runtime handles all scheduling internally. This makes Swift's model simpler to use but less flexible to customize.

## Why Rust needs an explicit runtime

Swift supplies executors and an async runtime. You still need to consider actor isolation, blocking calls, and where work runs; the runtime does not make those design choices disappear.

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

Tokio requires a spawned future and its output to be `Send + 'static`. Swift task creation has different isolation and transfer rules: `Task { }` can inherit actor isolation, so it is not a direct equivalent of transferring a Rust future between worker threads.

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

## Task ownership and cancellation

An async operation has both a result and a lifetime. Decide who owns unfinished work and what happens when its result is no longer needed.

| Construct | Who owns the work? | What happens when the caller stops waiting? |
|---|---|---|
| Rust future awaited directly | The enclosing future owns it, unless it borrows an existing future | Dropping the owned future drops its suspended state. |
| `tokio::join!` | The current task polls all branches | It waits for every branch, including branches returning `Err` as a value. |
| `tokio::try_join!` | The current task polls all branches | On the first `Err`, it returns and drops the remaining owned branch futures. |
| `tokio::spawn` | The runtime owns a separately scheduled task | Dropping its `JoinHandle` detaches it; the task can continue. |
| Swift `async let` or task group | A structured scope owns child tasks | Children cannot outlive the scope; cancellation is cooperative, and the scope waits for them. |
| Swift `Task { }` | An unstructured task has its own lifetime | Discarding the handle does not cancel the task. |

`join!` gives concurrency within one task, not parallel execution on multiple worker threads. Spawning can permit parallelism on a suitable runtime, but it also creates a separate lifetime to manage. Swift’s structured child tasks are independently scheduled; joined Rust futures are not a direct scheduling equivalent.

### A failure that drops unfinished work

This complete example uses two one-shot channels, each of which sends a single value to an awaiting receiver, to make the sequence observable. One operation acquires a resource guard and signals that it has started. The other waits for that signal and then fails. The first operation remains pending, so its only cleanup path in this example is destruction of its future.

Create a Rust binary package and add these features to its manifest:

```toml
[dependencies]
tokio = { version = "1", features = ["macros", "rt", "sync"] }
```

Use this as `src/main.rs` and run it with `cargo run`:

```rust
use std::future::pending;
use tokio::sync::oneshot;

struct ResourceGuard {
    released: Option<oneshot::Sender<&'static str>>,
}

impl Drop for ResourceGuard {
    fn drop(&mut self) {
        if let Some(sender) = self.released.take() {
            // Cleanup must also work if the observer has gone away.
            let _ = sender.send("released");
        }
    }
}

async fn hold_resource(
    started: oneshot::Sender<()>,
    released: oneshot::Sender<&'static str>,
) -> Result<(), &'static str> {
    let _guard = ResourceGuard {
        released: Some(released),
    };
    started.send(()).expect("start observer is present");
    pending::<Result<(), &'static str>>().await
}

async fn fail_after_start(started: oneshot::Receiver<()>) -> Result<(), &'static str> {
    started.await.expect("worker signals before failing");
    Err("validation failed")
}

#[tokio::main(flavor = "current_thread")]
async fn main() {
    let (started_tx, started_rx) = oneshot::channel();
    let (released_tx, released_rx) = oneshot::channel();

    let outcome = tokio::try_join!(
        hold_resource(started_tx, released_tx),
        fail_after_start(started_rx),
    );

    assert_eq!(outcome, Err("validation failed"));
    assert_eq!(released_rx.await.unwrap(), "released");
    println!("The failed batch released its resource");
}
```

The start signal proves that `_guard` exists before the failure. Once `try_join!` returns the error, its other owned future has been dropped, which runs the guard’s destructor. The release signal proves that cleanup occurred. The guard models synchronous resource release, such as returning a buffer or releasing a permit; it does not represent a database rollback or an async close operation.

Replacing `try_join!` with `join!` would wait indefinitely here: `join!` does not interpret a branch’s `Err` as a reason to stop its siblings. The pending operation would still need a completion or cancellation path.

### Spawning changes the cleanup responsibility

Keep the helper definitions above and replace `main` with this version to move the worker into a spawned task:

```rust
#[tokio::main(flavor = "current_thread")]
async fn main() {
    let (started_tx, started_rx) = oneshot::channel();
    let (released_tx, released_rx) = oneshot::channel();
    let worker = tokio::spawn(hold_resource(started_tx, released_tx));

    let failure = fail_after_start(started_rx).await;
    assert_eq!(failure, Err("validation failed"));

    worker.abort();
    let join_error = worker.await.unwrap_err();
    assert!(join_error.is_cancelled());
    assert_eq!(released_rx.await.unwrap(), "released");
    println!("The cancelled task released its resource");
}
```

The parent explicitly requests cancellation with `abort()` and awaits the handle to observe that the task has finished. Dropping `worker` instead would detach the task. Aborting is not an immediate interruption of arbitrary code: a task must return control to the runtime, and a `spawn_blocking` operation that has already started generally cannot be aborted.

The worker above cannot complete normally. With arbitrary tasks, completion can race an abort request, so awaiting the handle may instead return a successful result.

Be especially careful with `try_join!` over spawned handles. A `JoinHandle<Result<T, E>>` produces two layers: `Result<Result<T, E>, JoinError>`. An application error is an inner `Err`, while task cancellation or panic is an outer `Err`. Dropping a handle because another branch failed still does not cancel its task. Keep handles and explicitly cancel and join unfinished tasks, or use a task-owning abstraction such as `JoinSet` with a deliberate shutdown path.

### Cancellation is not rollback

Dropping a future does not undo a sent network request, restore bytes already written, or cancel a separate task it spawned. If shutdown needs async work, arrange a cooperative signal that lets the operation finish that work, then await its completion. `Drop` itself cannot await.

Likewise, `tokio::select!` drops losing futures that it owns, but polling `&mut handle` only borrows the handle. Selecting another branch does not cancel that spawned task. Even a directly awaited operation can lose partial progress when restarted; check its documented cancellation safety before placing it in a loop with `select!`.

In Swift, leaving an `async let` scope cancels unfinished children and waits for them. A throwing task group also waits for its children when unwinding; cancellation merely requests that they stop. Child code must react through cancellation-aware APIs or explicit checks. Calling `Task.cancel()` on an unstructured task requests cancellation, but discarding its handle does not. These lifetime rules are documented in Swift’s [concurrency chapter](https://docs.swift.org/swift-book/documentation/the-swift-programming-language/concurrency/).

### State can change across suspension

A lock or actor protects access to state; it does not automatically make a multi-step operation transactional. Suppose an operation checks that one seat remains, awaits payment, and then books the seat. Another operation can book it while the first is suspended. Swift actors allow this interleaving at suspension points. Rust code can have the same logic bug if it releases a mutex before awaiting and later acts on the old value.

Reserve the seat before suspension, or recheck the state when committing the result. Define what happens to a reservation if payment fails or the task is canceled. Holding an async mutex across the whole operation can serialize access, but increases contention and may introduce deadlocks; holding a blocking mutex across `.await` can block the executor. Choose the invariant and cancellation behavior before choosing the synchronization primitive.

See Tokio’s documentation for [`try_join!`](https://docs.rs/tokio/latest/tokio/macro.try_join.html), [`JoinHandle`](https://docs.rs/tokio/latest/tokio/task/struct.JoinHandle.html), and [`select!` cancellation safety](https://docs.rs/tokio/latest/tokio/macro.select.html#cancellation-safety).

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

The `Future` and `Stream` polling signatures use `Pin<&mut Self>`. For a type that is not `Unpin`, this restricts moving the pointee after it has been pinned. The pointer itself can move, and `Unpin` types can be moved even through a pinned pointer.

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

Choose an executor and I/O integration for the exact Wasm environment. Browser code commonly uses `wasm-bindgen-futures` to integrate with JavaScript promises; component code needs bindings and a host supporting its chosen interfaces. A native Tokio configuration is not automatically portable to either environment.

The [WASI chapter](../../rust-and-webassembly/wasi/) explains host interfaces, and the [dated status appendix](../../appendices/wasm-status/) separates current async support from proposals. The ownership questions in this chapter still apply: identify who polls the operation, who owns unfinished work, and what cancellation can actually stop.

## Key differences and gotchas

- **Lazy futures and scheduled tasks**: an `async fn` body starts when its returned future is polled. Creating a Swift `Task` schedules work; calling a Swift async function with `await` runs in the current task. Arbitrary Rust functions returning futures may also do synchronous work before returning them.
- **No built-in runtime**: choose an executor suited to the environment, such as Tokio for native async I/O or a browser integration for Wasm. Swift includes its concurrency runtime.
- **`Send` bounds on spawned tasks**: `tokio::spawn` requires the future and its output to be `Send`, since the task may run on another thread. Swift task creation follows actor-isolation and transfer rules: a `Task` can inherit its surrounding actor isolation, and [`sending` parameters](https://github.com/swiftlang/swift-evolution/blob/main/proposals/0430-transferring-parameters-and-results.md) allow safe transfers of some non-`Sendable` values. These rules are not a direct equivalent of Rust's `Send` bound.
- **Pinning**: Rust requires futures to be pinned before polling because they may be self-referential. This is invisible when using `.await` but surfaces when storing futures in collections or returning them as trait objects.
- **No `async let`**: Rust does not have Swift's `async let` syntax for structured concurrency. Instead, you use `tokio::join!` or spawn tasks manually.
- **Cancellation**: dropping an uncompleted future stops polling it and drops its state, but does not necessarily undo external work it started. Dropping a Tokio `JoinHandle` detaches the task rather than canceling it; use `abort()` or cooperative cancellation such as `tokio_util::sync::CancellationToken`. Swift structured scopes await their children, with cancellation depending on the scope and exit path; cancellation is cooperative.
- **Async contexts**: Rust permits calling `async fn` from synchronous code to create a future. Awaiting it requires an async context, or a bridge such as `block_on` to drive it from synchronous code.
- **No `actor` keyword**: Rust has no built-in actor abstraction. You build actor patterns manually using channels and `tokio::spawn`, or use a crate like `actix`.
- **Streams are not yet in `std`**: unlike Swift's `AsyncSequence` (which is in the standard library), Rust's `Stream` trait lives in the `futures` crate. There are plans to stabilize it in `std`, but as of now it requires a dependency.

## Further reading

- [Asynchronous Programming in Rust](https://rust-lang.github.io/async-book/): the official async Rust book
- [Tokio Tutorial](https://tokio.rs/tokio/tutorial): getting started with the most popular runtime
- [The `Future` trait](https://doc.rust-lang.org/std/future/trait.Future.html): standard library documentation
- [Pin and Unpin](https://doc.rust-lang.org/std/pin/index.html): standard library documentation on pinning
- [futures crate](https://docs.rs/futures/latest/futures/): utilities for working with futures and streams
- [tokio-stream](https://docs.rs/tokio-stream/latest/tokio_stream/): stream utilities for tokio
- [WASI 0.3 Async](https://github.com/WebAssembly/WASI): the WASI async proposal
