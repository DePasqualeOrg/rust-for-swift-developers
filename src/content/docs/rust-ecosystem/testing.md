---
title: Testing
sidebar:
  order: 26
---

Rust has first-class testing support built into the language and toolchain. There is no separate testing framework to install, no additional test target to configure, and no special build scheme to set up. You write tests right next to your code, annotate them with an attribute, and run them with `cargo test`.

If you have used Swift Testing or XCTest, the model will feel familiar – but the ergonomics are different. Rust tests live inside the same source files as the code they test, which changes how you think about test organization and access to private internals.

## Your first test

In Swift Testing, you mark a function with `@Test`:

```swift
// Swift
import Testing

@Test func addition() {
    #expect(2 + 2 == 4)
}
```

In Rust, you mark a function with `#[test]`:

```rust
// Rust
#[test]
fn addition() {
    assert_eq!(2 + 2, 4);
}
```

Both approaches use an attribute to identify test functions. Neither requires inheriting from a base class or conforming to a protocol – any function with the right attribute is a test.

To run all tests:

```sh
# Rust
cargo test

# Swift
swift test
```

`cargo test` compiles your project in test mode, discovers all functions annotated with `#[test]`, runs them, and reports results. By default, tests run in parallel on multiple threads – similar to Swift Testing's default parallel execution.

## Assertion macros

Rust provides three primary assertion macros, all from the standard library:

```rust
#[test]
fn assertions_demo() {
    // assert! checks that a boolean expression is true
    assert!(2 + 2 == 4);

    // assert_eq! checks that two values are equal
    assert_eq!(4, 2 + 2);

    // assert_ne! checks that two values are not equal
    assert_ne!(3, 2 + 2);
}
```

All three macros accept an optional message as additional arguments:

```rust
#[test]
fn with_custom_message() {
    let result = 2 + 2;
    assert_eq!(result, 4, "Expected 2 + 2 to equal 4, got {result}");
}
```

When `assert_eq!` fails, it prints both values, which makes diagnosing failures straightforward. The values must implement the `Debug` and `PartialEq` traits – most standard types do, and you can derive both with `#[derive(Debug, PartialEq)]`.

Here is how these map to Swift's testing frameworks:

| Rust | Swift Testing | XCTest |
|---|---|---|
| `assert!(expr)` | `#expect(expr)` | `XCTAssertTrue(expr)` |
| `assert_eq!(a, b)` | `#expect(a == b)` | `XCTAssertEqual(a, b)` |
| `assert_ne!(a, b)` | `#expect(a != b)` | `XCTAssertNotEqual(a, b)` |

Swift Testing's `#expect` macro is more flexible than Rust's `assert!` – it captures subexpressions and produces rich diagnostics automatically. Rust's `assert_eq!` compensates by printing both sides of the comparison, but it does not decompose arbitrary expressions the way `#expect` does.

## The `#[cfg(test)]` module

One of Rust's most distinctive testing conventions is that unit tests live inside the same file as the code they test, wrapped in a conditionally compiled module:

```rust
// src/lib.rs

pub fn fahrenheit_to_celsius(f: f64) -> f64 {
    (f - 32.0) * 5.0 / 9.0
}

fn round_to(value: f64, places: u32) -> f64 {
    let factor = 10_f64.powi(places as i32);
    (value * factor).round() / factor
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_boiling_point() {
        assert_eq!(fahrenheit_to_celsius(212.0), 100.0);
    }

    #[test]
    fn test_freezing_point() {
        assert_eq!(fahrenheit_to_celsius(32.0), 0.0);
    }

    #[test]
    fn test_body_temperature() {
        let celsius = fahrenheit_to_celsius(98.6);
        let rounded = round_to(celsius, 1);
        assert_eq!(rounded, 37.0);
    }
}
```

The `#[cfg(test)]` attribute tells the compiler to include this module only when running `cargo test`. In a normal build, the test module and all its contents are excluded entirely – no binary bloat, no unused code warnings.

The `use super::*;` import brings everything from the parent module into scope, including *private* functions. In the example above, `round_to` is not `pub`, but the test module can still call it because it is a child module of the same file.

This is a significant difference from Swift's testing model. In Swift, tests live in a separate target:

```
Sources/
  MyLibrary/
    Temperature.swift
Tests/
  MyLibraryTests/
    TemperatureTests.swift
```

The test target depends on the library target and can only access public (or `@testable import`-exposed internal) symbols. In Rust, unit tests have unrestricted access to the module's internals because they are part of the same module.

Whether this is an advantage or a disadvantage depends on your testing philosophy. Having access to private functions makes it easy to test implementation details, which can lead to brittle tests that break when you refactor. On the other hand, it lets you thoroughly test complex internal logic without exposing it publicly.

## Integration tests

For tests that exercise your library's public API from the outside – as a real consumer would – Rust uses a separate `tests/` directory at the project root:

```
my_project/
  Cargo.toml
  src/
    lib.rs
  tests/
    integration_test.rs
```

Each file in `tests/` is compiled as a separate crate that depends on your library. This means integration tests can only access your public API, just like any other consumer:

```rust
// tests/integration_test.rs
use my_project::fahrenheit_to_celsius;

#[test]
fn boiling_point_from_public_api() {
    assert_eq!(fahrenheit_to_celsius(212.0), 100.0);
}
```

No `#[cfg(test)]` is needed here – files in the `tests/` directory are only compiled during `cargo test` by default.

This two-tier model maps to Swift's testing patterns:

| Test type | Rust | Swift |
|---|---|---|
| Unit tests (access to internals) | `#[cfg(test)] mod tests` in source files | Test target with `@testable import` |
| Integration tests (public API only) | Files in `tests/` directory | Test target without `@testable import` |

In practice, most Swift projects use `@testable import` for all tests, which gives them access to `internal` symbols. Rust's unit test module goes further by also exposing private symbols.

## Test organization

### Filtering tests by name

You can run a subset of tests by passing a filter string to `cargo test`:

```sh
# Run only tests whose name contains "celsius"
cargo test celsius

# Run only tests in the "tests::test_boiling_point" path
cargo test tests::test_boiling_point
```

Swift Testing offers similar filtering with `swift test --filter`.

### Submodules for grouping

Within a `#[cfg(test)]` module, you can create submodules to organize related tests:

```rust
#[cfg(test)]
mod tests {
    use super::*;

    mod conversion {
        use super::*;

        #[test]
        fn boiling_point() {
            assert_eq!(fahrenheit_to_celsius(212.0), 100.0);
        }

        #[test]
        fn absolute_zero() {
            let celsius = fahrenheit_to_celsius(-459.67);
            assert!((celsius - (-273.15)).abs() < 1e-10);
        }
    }

    mod rounding {
        use super::*;

        #[test]
        fn two_decimal_places() {
            assert_eq!(round_to(3.14159, 2), 3.14);
        }
    }
}
```

These submodules show up in test output with their full path (e.g., `tests::conversion::boiling_point`), making it easy to identify which group a test belongs to. This is similar to organizing Swift tests into different test classes or using Swift Testing's `@Suite`.

## `#[should_panic]`: testing for panics

To verify that code panics under certain conditions, use the `#[should_panic]` attribute:

```rust
#[test]
#[should_panic]
fn divide_by_zero_panics() {
    let _ = divide(10, 0);
}

fn divide(a: i32, b: i32) -> i32 {
    if b == 0 {
        panic!("division by zero");
    }
    a / b
}
```

You can also assert on the panic message:

```rust
#[test]
#[should_panic(expected = "division by zero")]
fn divide_by_zero_has_correct_message() {
    let _ = divide(10, 0);
}
```

The test passes only if the panic message contains the `expected` string. This is analogous to Swift Testing's `#expect(throws:)`:

```swift
// Swift
@Test func divideByZeroPanics() {
    #expect(throws: DivisionError.divideByZero) {
        try divide(10, by: 0)
    }
}
```

The key difference is that Rust's `#[should_panic]` works with panics (which are unrecoverable in normal code flow), while Swift Testing's `#expect(throws:)` works with thrown errors. In Rust, recoverable errors use `Result`, and you test those differently – see the section on testing with `Result` below.

## `#[ignore]`: skipping expensive tests

Some tests are slow – they might hit the network, process large datasets, or perform heavy computation. You can mark them with `#[ignore]` so they do not run by default:

```rust
#[test]
#[ignore]
fn slow_integration_test() {
    // This test takes a long time
    let result = expensive_computation();
    assert!(result > 0);
}
```

Ignored tests are skipped during a normal `cargo test` run. To include them explicitly:

```sh
# Run only ignored tests
cargo test -- --ignored

# Run all tests, including ignored ones
cargo test -- --include-ignored
```

In Swift Testing, the equivalent is the `.disabled()` trait or a runtime condition with `.enabled(if:)`:

```swift
// Swift
@Test(.disabled("Takes too long for CI"))
func slowIntegrationTest() {
    // ...
}
```

The difference is that Rust's `#[ignore]` has a dedicated flag to run ignored tests, making it easy to include them in a separate CI step. Swift Testing's `.disabled()` tests cannot be selectively re-enabled from the command line in the same way.

## Testing with `Result`

Test functions can return `Result<(), E>` instead of using assertions, where `E` is any type that implements the `Debug` trait. If the function returns `Err`, the test fails and the error is displayed:

```rust
#[test]
fn parse_valid_number() -> Result<(), std::num::ParseIntError> {
    let n: i32 = "42".parse()?;
    assert_eq!(n, 42);
    Ok(())
}
```

This is particularly useful when the code under test returns `Result` and you want to use the `?` operator to propagate errors concisely rather than writing `.unwrap()` on every call:

```rust
#[test]
fn read_and_validate_config() -> Result<(), Box<dyn std::error::Error>> {
    let content = std::fs::read_to_string("tests/fixtures/config.toml")?;
    assert!(content.contains("name"));
    Ok(())
}
```

Using `Box<dyn std::error::Error>` as the error type lets you propagate any error type with `?`, which is convenient for tests that interact with multiple error-producing APIs.

In Swift, test functions can be marked `throws` for the same purpose:

```swift
// Swift
@Test func parseValidNumber() throws {
    let n = try Int("42", format: .number)
    #expect(n == 42)
}
```

## Test output and `cargo test` options

By default, `cargo test` captures stdout from passing tests. If a test fails, the captured output is displayed. To see output from all tests, including passing ones:

```sh
cargo test -- --nocapture
```

Other useful options:

```sh
# Run tests sequentially (single-threaded)
cargo test -- --test-threads=1

# Show the list of all test names without running them
cargo test -- --list

# Run a specific test binary (useful in workspaces)
cargo test --package my_crate

# Run only doc tests
cargo test --doc
```

The `--` separator is important: arguments before `--` go to Cargo (the build tool), and arguments after `--` go to the test binary itself.

## Doc tests

As mentioned in the previous chapter, code examples in `///` doc comments are compiled and executed during `cargo test`:

```rust
/// Doubles a number.
///
/// # Examples
///
/// ```
/// assert_eq!(my_crate::double(3), 6);
/// ```
pub fn double(n: i32) -> i32 {
    n * 2
}
```

Running `cargo test` will compile this example as a standalone program and verify that it runs without panicking. This ensures documentation stays in sync with code – a stale example is a test failure, not just misleading text.

Swift's DocC does not have an equivalent built-in mechanism for testing code snippets in documentation. You can create code snippet files that are syntax-checked, but they are not executed as tests automatically.

## Key differences and gotchas

**Tests live in the same file**: Rust's convention of putting unit tests in a `#[cfg(test)]` module inside the source file is the opposite of Swift's separate test target model. This means you do not need to manage visibility (`@testable import`) – tests have full access to the module's internals. It also means your source files are longer, since they include test code.

**No test classes or test suites**: Rust tests are standalone functions, not methods on a class. There is no `setUp` or `tearDown` equivalent. If you need shared setup, use a helper function and call it at the beginning of each test. Some crates like `rstest` provide fixtures, but the standard library keeps things simple.

**Parallel by default**: Rust tests run in parallel on multiple threads by default. If your tests share state (files, global variables), they may interfere with each other. Use `--test-threads=1` to run sequentially, or design your tests to use isolated state.

**`panic` vs `Result` in tests**: tests can fail either by panicking (a failed assertion or explicit `panic!`) or by returning `Err`. The idiomatic choice depends on what you are testing: use assertions for checking conditions, and return `Result` when you want to use `?` for clean error propagation.

**No async test support in std**: the standard test framework does not support `async` test functions directly. If you need async tests, you typically use `#[tokio::test]` from the tokio crate, which provides its own test macro that sets up an async runtime:

```rust
// Fragment – requires tokio dependency with "macros" and "rt" features
#[tokio::test]
async fn async_operation() {
    let result = fetch_data().await;
    assert!(result.is_ok());
}
```

In Swift, `@Test` functions can be `async` natively because the async runtime is part of the language.

**No built-in mocking**: Rust's standard library does not include mocking utilities. The community has crates like `mockall` for mock generation, but many Rust developers prefer designing with trait-based dependency injection and using manual test doubles. This is similar to the Swift ecosystem, where mocking frameworks exist but are not part of the standard tooling.

## Further reading

- [The Rust Programming Language – Writing Tests](https://doc.rust-lang.org/book/ch11-01-writing-tests.html): comprehensive guide to testing in Rust
- [The Rust Programming Language – Test Organization](https://doc.rust-lang.org/book/ch11-03-test-organization.html): unit vs integration test structure
- [Rust By Example – Testing](https://doc.rust-lang.org/rust-by-example/testing.html): hands-on examples
- [The `cargo test` command](https://doc.rust-lang.org/cargo/commands/cargo-test.html): full reference for test invocation options
- [rstest](https://docs.rs/rstest): parameterized tests and fixtures for Rust
- [mockall](https://docs.rs/mockall): a popular mocking library
