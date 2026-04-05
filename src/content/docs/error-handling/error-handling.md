---
title: Error Handling
sidebar:
  order: 19
---

Rust has no exceptions. There is no `throw`, no `catch`, no invisible control flow that unwinds the stack when something goes wrong. Instead, errors are ordinary values – returned from functions, stored in variables, and transformed with combinators. If you have used Swift's `Result` type, you already understand the core idea. Rust takes that idea and makes it the only way to handle recoverable errors.

## Errors are values, not control flow

In Swift, the primary error handling mechanism uses `throws`, `try`, and `catch`. A function that can fail is marked `throws`, and calling it requires `try` inside a `do`/`catch` block:

```swift
// Swift
enum FileError: Error {
    case notFound
    case permissionDenied
}

func readFile(at path: String) throws -> String {
    throw FileError.notFound
}

do {
    let contents = try readFile(at: "/tmp/data.txt")
    print(contents)
} catch {
    print("Failed: \(error)")
}
```

Swift also has a `Result` type (`Result<Success, Failure>`), but most Swift code uses the `throws` syntax because it is more ergonomic and deeply integrated into the language.

Rust has no `throws` keyword. Instead, every fallible function returns `Result<T, E>`:

```rust
// Rust
use std::fmt;

#[derive(Debug)]
enum FileError {
    NotFound,
    PermissionDenied,
}

impl fmt::Display for FileError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            FileError::NotFound => write!(f, "file not found"),
            FileError::PermissionDenied => write!(f, "permission denied"),
        }
    }
}

fn read_file(path: &str) -> Result<String, FileError> {
    Err(FileError::NotFound)
}

fn main() {
    match read_file("/tmp/data.txt") {
        Ok(contents) => println!("{contents}"),
        Err(e) => println!("Failed: {e}"),
    }
}
```

`Result<T, E>` is an enum with two variants: `Ok(T)` for success and `Err(E)` for failure. Because it is a regular enum, you handle it with `match`, `if let`, or any of the other pattern matching tools you already know from [Chapter 8](../../language-fundamentals/pattern-matching/).

The implication is significant: you can always see from a function's signature whether it can fail and what kind of error it returns. There is no hidden `throws` effect, no unchecked exceptions, and no surprises at the call site.

## The `?` operator

Pattern matching every `Result` by hand would be exhausting. Rust's `?` operator provides the same convenience as Swift's `try` – it unwraps a success or returns the error early:

```swift
// Swift
func processFile(at path: String) throws -> Int {
    let contents = try readFile(at: path)
    return contents.count
}
```

```rust
// Rust
fn process_file(path: &str) -> Result<usize, FileError> {
    let contents = read_file(path)?;
    Ok(contents.len())
}

# use std::fmt;
#
# #[derive(Debug)]
# enum FileError {
#     NotFound,
#     PermissionDenied,
# }
#
# impl fmt::Display for FileError {
#     fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
#         match self {
#             FileError::NotFound => write!(f, "file not found"),
#             FileError::PermissionDenied => write!(f, "permission denied"),
#         }
#     }
# }
#
# fn read_file(path: &str) -> Result<String, FileError> {
#     Err(FileError::NotFound)
# }
#
fn main() {
    match process_file("/tmp/data.txt") {
        Ok(len) => println!("File has {len} bytes"),
        Err(e) => println!("Error: {e}"),
    }
}
```

The `?` after `read_file(path)` does the following: if the result is `Ok`, it unwraps the value and execution continues. If the result is `Err`, it returns the error from the enclosing function immediately. The function using `?` must itself return a `Result` (or `Option` – the operator works with both).

This is conceptually identical to Swift's `try`, but with an important difference: `?` is a postfix operator on the expression, while `try` is a prefix keyword. This means Rust's `?` can be chained naturally:

```rust
// Rust
fn first_line(path: &str) -> Result<String, std::io::Error> {
    let contents = std::fs::read_to_string(path)?;
    let line = contents.lines().next().ok_or(std::io::Error::new(
        std::io::ErrorKind::InvalidData,
        "file is empty",
    ))?;
    Ok(line.to_string())
}

fn main() {
    match first_line("/tmp/test.txt") {
        Ok(line) => println!("{line}"),
        Err(e) => println!("Error: {e}"),
    }
}
```

Notice how `?` works with both `Result` and `Option` (via `ok_or`, which converts an `Option` into a `Result`).

## Custom error types

A well-designed Rust library defines its own error type. The convention is to implement two traits: `std::fmt::Display` (for human-readable messages) and `std::error::Error` (which provides integration with the broader error ecosystem).

```rust
// Rust
use std::fmt;
use std::error::Error;

#[derive(Debug)]
enum ParseConfigError {
    MissingField(String),
    InvalidValue { field: String, value: String },
    IoError(std::io::Error),
}

impl fmt::Display for ParseConfigError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            ParseConfigError::MissingField(name) => {
                write!(f, "missing required field: {name}")
            }
            ParseConfigError::InvalidValue { field, value } => {
                write!(f, "invalid value '{value}' for field '{field}'")
            }
            ParseConfigError::IoError(e) => {
                write!(f, "I/O error: {e}")
            }
        }
    }
}

impl Error for ParseConfigError {
    fn source(&self) -> Option<&(dyn Error + 'static)> {
        match self {
            ParseConfigError::IoError(e) => Some(e),
            _ => None,
        }
    }
}

let error = ParseConfigError::MissingField("host".to_string());
```

The `source()` method returns the underlying cause of the error, forming a chain that callers can walk to understand the root problem. This is similar to Swift's pattern of wrapping errors with context, though Swift does not have a standardized error chain mechanism built into the `Error` protocol.

In Swift, you would typically define a similar error enum conforming to `Error` and optionally `LocalizedError`:

```swift
// Swift
enum ParseConfigError: LocalizedError {
    case missingField(String)
    case invalidValue(field: String, value: String)
    case ioError(underlying: Error)

    var errorDescription: String? {
        switch self {
        case .missingField(let name):
            return "Missing required field: \(name)"
        case .invalidValue(let field, let value):
            return "Invalid value '\(value)' for field '\(field)'"
        case .ioError(let underlying):
            return "I/O error: \(underlying.localizedDescription)"
        }
    }
}
```

## Converting between error types with `From`

When a function calls other functions that return different error types, you need a way to convert between them. Rust's `?` operator automatically calls `From::from()` on the error, so if you implement `From` for your error type, conversions happen transparently:

```rust
// Rust
use std::fmt;
use std::error::Error;
use std::num::ParseIntError;

#[derive(Debug)]
enum AppError {
    Io(std::io::Error),
    Parse(ParseIntError),
}

impl fmt::Display for AppError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            AppError::Io(e) => write!(f, "I/O error: {e}"),
            AppError::Parse(e) => write!(f, "parse error: {e}"),
        }
    }
}

impl Error for AppError {}

impl From<std::io::Error> for AppError {
    fn from(e: std::io::Error) -> Self {
        AppError::Io(e)
    }
}

impl From<ParseIntError> for AppError {
    fn from(e: ParseIntError) -> Self {
        AppError::Parse(e)
    }
}

fn read_count(path: &str) -> Result<i32, AppError> {
    let contents = std::fs::read_to_string(path)?; // io::Error -> AppError
    let count = contents.trim().parse::<i32>()?;    // ParseIntError -> AppError
    Ok(count)
}

fn main() {
    match read_count("/tmp/count.txt") {
        Ok(n) => println!("Count: {n}"),
        Err(e) => println!("Error: {e}"),
    }
}
```

The `?` operator in `read_count` handles two different error types because `AppError` implements `From` for both. This is the standard pattern for composing errors from multiple sources. Swift has no direct equivalent – you would typically catch and re-throw errors manually, or use a single broad error type.

## The `thiserror` crate: error types without boilerplate

Writing `Display`, `Error`, and `From` implementations by hand is tedious. The `thiserror` crate generates them from derive macros, and it is the standard choice for library error types:

```rust
// Rust
use thiserror::Error;

#[derive(Debug, Error)]
enum AppError {
    #[error("I/O error: {0}")]
    Io(#[from] std::io::Error),

    #[error("parse error: {0}")]
    Parse(#[from] std::num::ParseIntError),

    #[error("missing required field: {0}")]
    MissingField(String),
}

fn read_count(path: &str) -> Result<i32, AppError> {
    let contents = std::fs::read_to_string(path)?;
    let count = contents.trim().parse::<i32>()?;
    Ok(count)
}

fn main() {
    match read_count("/tmp/count.txt") {
        Ok(n) => println!("Count: {n}"),
        Err(e) => println!("Error: {e}"),
    }
}
```

The `#[error("...")]` attribute generates the `Display` implementation. The `#[from]` attribute generates the `From` implementation. This produces the same code as the manual version above, with far less boilerplate.

## The `anyhow` crate: flexible errors for applications

While `thiserror` is designed for libraries that need precise error types, `anyhow` is designed for applications where you care about the error message and context more than the specific error type. It provides `anyhow::Result<T>`, which is shorthand for `Result<T, anyhow::Error>`, where `anyhow::Error` can hold any error type:

```rust
// Rust
use anyhow::{Context, Result};

fn read_count(path: &str) -> Result<i32> {
    let contents = std::fs::read_to_string(path)
        .with_context(|| format!("failed to read {path}"))?;
    let count = contents
        .trim()
        .parse::<i32>()
        .with_context(|| format!("failed to parse contents of {path}"))?;
    Ok(count)
}

fn main() {
    match read_count("/tmp/count.txt") {
        Ok(n) => println!("Count: {n}"),
        Err(e) => println!("Error: {e:#}"),
    }
}
```

The `with_context` method attaches a human-readable message to the error. Printing with `{e:#}` shows the full chain of context. The `anyhow!` macro can also create ad-hoc errors:

```rust
// Rust
use anyhow::{anyhow, Result};

fn validate_port(port: u16) -> Result<u16> {
    if port < 1024 {
        return Err(anyhow!("port {port} is reserved"));
    }
    Ok(port)
}

fn main() {
    match validate_port(80) {
        Ok(p) => println!("Using port {p}"),
        Err(e) => println!("Error: {e}"),
    }
}
```

A useful rule of thumb: use `thiserror` when you are writing a library and callers need to match on specific error variants; use `anyhow` when you are writing an application and want to propagate errors with context.

## `unwrap()` and `expect()`

The `unwrap()` method extracts the value from `Ok` or panics if the result is `Err`. The `expect()` method does the same but lets you provide a custom panic message:

```rust
// Rust
fn main() {
    let value: Result<i32, &str> = Ok(42);
    println!("{}", value.unwrap()); // 42

    let config = std::fs::read_to_string("config.toml")
        .expect("config.toml must exist");
    println!("{config}");
}
```

In Swift, the equivalent is force-unwrapping an optional with `!` or calling `try!`:

```swift
// Swift
let value: Int = Int("42")! // crashes if nil
let config = try! String(contentsOfFile: "config.toml") // crashes if throws
```

The guidance is similar in both languages: avoid these in production code unless you can guarantee success. Legitimate uses include:

- **Tests and prototypes**: when a failure means the test setup is broken
- **Provably infallible operations**: when you know the value is valid but the type system cannot prove it (e.g., parsing a hardcoded string)
- **Program initialization**: when the program cannot meaningfully continue without the value

In Rust, `expect` is generally preferred over `unwrap` because the message documents your assumption: `expect("database URL must be set")` communicates intent, while a bare `unwrap()` just says "I did not handle this case."

## Panics vs. recoverable errors

Rust distinguishes between two categories of failure:

- **Recoverable errors**: represented by `Result<T, E>`. The caller decides how to handle them – retry, report to the user, use a default, or propagate upward with `?`.
- **Unrecoverable errors**: triggered by `panic!()`. The program prints an error message and unwinds the stack (or aborts, depending on configuration). This is comparable to Swift's `fatalError()` or a force-unwrap crash.

```rust
// Rust
fn divide(a: f64, b: f64) -> Result<f64, String> {
    if b == 0.0 {
        Err("division by zero".to_string())
    } else {
        Ok(a / b)
    }
}

fn main() {
    // Recoverable: the caller handles it
    match divide(10.0, 0.0) {
        Ok(result) => println!("Result: {result}"),
        Err(e) => println!("Error: {e}"),
    }

    // Unrecoverable: the program crashes
    // panic!("something went catastrophically wrong");
}
```

The rule of thumb: use `Result` when the caller can reasonably handle the failure. Use `panic!` for bugs – situations that indicate a programming error, like an index out of bounds or a violated invariant. The Rust standard library follows this convention: `Vec::get()` returns `Option` (recoverable), while `vec[index]` panics on out-of-bounds access (a bug).

Swift's model is similar in practice, though the line is drawn differently. Swift uses `throws` for recoverable errors and `fatalError()` / `preconditionFailure()` for bugs, but it also uses `nil` returns and optionals extensively where Rust might use `Result`.

## `Result` combinators

Like `Option`, Rust's `Result` has a rich set of combinators for transforming values without explicit `match`:

```rust
// Rust
let result: Result<i32, String> = Ok(42);

// map: transform the success value
let doubled = result.map(|v| v * 2); // Ok(84)

// and_then: chain fallible operations (flatMap in Swift)
let chained = result.and_then(|v| {
    if v > 0 {
        Ok(v.to_string())
    } else {
        Err("must be positive".to_string())
    }
}); // Ok("42")

// unwrap_or: provide a default
let value = Err::<i32, &str>("oops").unwrap_or(0); // 0

// unwrap_or_else: compute a default lazily
let value = Err::<i32, &str>("oops").unwrap_or_else(|_| 99); // 99
```

If you have used Swift's `map`, `flatMap`, and `??` on `Optional` or `Result`, these will be familiar. The names differ (`and_then` instead of `flatMap`, `unwrap_or` instead of `??`), but the patterns are the same.

## Key differences and gotchas

- **No exceptions**: Rust has no `throw`/`catch`. All recoverable errors use `Result<T, E>`. This makes error paths explicit in the type signature.
- **`?` vs `try`**: Rust's `?` is postfix; Swift's `try` is prefix. Both propagate errors to the caller, but `?` also performs `From` conversion automatically.
- **Error types must be explicit**: In Swift, `throws` historically did not specify the error type. Swift 6 added typed throws (`throws(MyError)`), bringing it closer to Rust's model, but untyped `throws` (effectively `throws(any Error)`) remains the dominant pattern in the Swift ecosystem. Rust always requires you to name the error type in `Result<T, E>`.
- **No `do`/`catch` blocks**: Rust does not have a dedicated syntax for error handling blocks. You handle errors at each call site with `?`, `match`, or combinators. If you need to handle a group of operations together, you extract them into a function that returns `Result`.
- **`panic!` is not an exception**: A panic is not caught by normal error handling. It is closer to Swift's `fatalError()`. While you can catch panics with `std::panic::catch_unwind`, this is rare and intended for FFI boundaries or test harnesses, not normal control flow.
- **`Option` and `Result` interop**: Rust's `?` works with both `Option` and `Result`, but you cannot mix them freely in the same function. Use `ok_or` to convert `Option` to `Result`, or `ok()` to go the other direction.

## Further reading

- [Error Handling](https://doc.rust-lang.org/book/ch09-00-error-handling.html): The Rust Programming Language
- [std::result](https://doc.rust-lang.org/std/result/): standard library documentation
- [std::error::Error](https://doc.rust-lang.org/std/error/trait.Error.html): the `Error` trait
- [thiserror](https://docs.rs/thiserror): derive macros for library error types
- [anyhow](https://docs.rs/anyhow): flexible error handling for applications
- [Error Handling in a Correctness-Critical Rust Project](https://sled.rs/errors.html): practical guidance on Rust error design
