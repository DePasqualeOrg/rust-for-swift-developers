---
title: Macros
sidebar:
  order: 27
---

Macros are one of the most distinctive features of Rust. They allow you to write code that generates other code at compile time – a form of metaprogramming that goes far beyond what Swift offers natively. If you have ever wished Swift's `Codable` synthesis or `Equatable` conformance worked for more cases, or wanted to reduce boilerplate in a way that protocols alone cannot, Rust's macro system is designed to solve exactly that class of problem.

Swift has recently introduced its own macro system (SE-0382 and related proposals), which brings some of the same capabilities. But Rust macros are more pervasive in the ecosystem – you will encounter them in virtually every Rust project, not as an advanced feature but as a routine part of writing Rust code. Understanding how they work is essential for reading and writing idiomatic Rust.

## Declarative macros with `macro_rules!`

The most common kind of Rust macro is the *declarative macro*, defined with `macro_rules!`. These macros work by pattern matching on syntax: you define patterns that match code fragments, and for each pattern, you specify what code to generate.

You have already been using declarative macros throughout this guide. `println!`, `vec!`, `assert_eq!`, and `format!` are all declarative macros – the `!` suffix indicates a macro invocation rather than a function call.

Here is a simple example:

```rust
macro_rules! say_hello {
    () => {
        println!("Hello, world!");
    };
    ($name:expr) => {
        println!("Hello, {}!", $name);
    };
}

fn main() {
    say_hello!();           // prints "Hello, world!"
    say_hello!("Alice");    // prints "Hello, Alice!"
}
```

The macro has two arms, separated by semicolons. Each arm has a pattern on the left (in parentheses) and an expansion on the right (in braces). `$name:expr` means "capture any expression and bind it to `$name`." When the macro is invoked, the compiler matches the invocation against the patterns and expands the matching arm.

Declarative macros can accept a variable number of arguments using repetition syntax:

```rust
macro_rules! sum {
    ($($x:expr),+ $(,)?) => {
        {
            let mut total = 0;
            $(total += $x;)+
            total
        }
    };
}

let result = sum!(1, 2, 3, 4, 5); // 15
```

The `$($x:expr),+` pattern means "one or more expressions separated by commas." The `$(,)?` allows an optional trailing comma. In the expansion, `$(total += $x;)+` repeats the statement for each captured expression.

Swift has no direct equivalent to `macro_rules!`. The closest Swift mechanism before Swift macros was using functions with variadic parameters, which is far more limited – you cannot generate arbitrary syntax, create new declarations, or transform code structure.

## Common standard library macros

You have seen most of these throughout the guide, but it is worth collecting them in one place to understand the pattern:

### `println!` and `print!`

```rust
fn main() {
    let name = "Alice";
    let age = 30;
    println!("Name: {name}, Age: {age}");  // with newline
    print!("No newline here");              // without newline
    println!();                             // just a newline
}
```

These are macros, not functions, because they need to parse the format string at compile time and verify that the placeholders match the provided arguments. A format mismatch is a compile error, not a runtime crash. Swift's `print()` is a function that uses string interpolation, which the compiler also checks at compile time – but the mechanism is different (string interpolation is a language feature in Swift, while format strings are a macro feature in Rust).

### `format!`

```rust
fn main() {
    let name = "Alice";
    let greeting = format!("Hello, {name}!");
    println!("{greeting}");
}
```

`format!` works like `println!` but returns a `String` instead of writing to stdout. This is the Rust equivalent of Swift's string interpolation for building strings dynamically:

```swift
// Swift
let name = "Alice"
let greeting = "Hello, \(name)!"
```

### `vec!`

```rust
let numbers = vec![1, 2, 3, 4, 5]; // [1, 2, 3, 4, 5]
let zeros = vec![0; 10]; // [0; 10]
```

`vec!` creates a `Vec<T>` from a list of elements. It is a macro because it accepts a variable number of arguments and also supports the `[value; count]` repeat syntax. In Swift, you would use an array literal:

```swift
// Swift
let numbers = [1, 2, 3, 4, 5]
let zeros = Array(repeating: 0, count: 10)
```

### `todo!`, `unimplemented!`, and `unreachable!`

```rust
fn work_in_progress() -> i32 {
    todo!("implement the calculation logic")
}

fn legacy_path() -> i32 {
    unimplemented!("this code path is not supported")
}

fn process(value: i32) -> &'static str {
    match value {
        1 => "one",
        2 => "two",
        _ => unreachable!("value is always 1 or 2"),
    }
}

```

All three macros cause a panic when reached at runtime, but they signal different intent:

- **`todo!`**: marks code that needs to be written. The program compiles but panics if this path is executed. Useful as a placeholder during development.
- **`unimplemented!`**: marks functionality that is intentionally not implemented. Similar to `todo!`, but signals a permanent omission rather than pending work.
- **`unreachable!`**: marks code that should never be reached. If it executes, it indicates a logic error.

Swift has `fatalError()` which serves all three purposes, but without the semantic distinction:

```swift
// Swift
func workInProgress() -> Int {
    fatalError("implement the calculation logic")
}
```

### `dbg!`

```rust
fn main() {
    let x = 5;
    let y = dbg!(x * 2) + 1; // prints: [src/main.rs:3:13] x * 2 = 10
    println!("{y}"); // 11
}
```

`dbg!` prints the expression, its value, and the file/line location to stderr, then returns the value. This makes it easy to insert into the middle of an expression chain without restructuring your code. It is a debugging aid meant to be removed before committing.

Swift does not have a direct equivalent, though `print()` with `#file` and `#line` serves a similar purpose with more ceremony.

## Derive macros

Derive macros are a form of *procedural macro* (covered later in this chapter) that generate trait implementations automatically. You apply them with the `#[derive(...)]` attribute on structs and enums:

```rust
#[derive(Debug, Clone, PartialEq)]
struct Point {
    x: f64,
    y: f64,
}

```

The `#[derive(Debug, Clone, PartialEq)]` attribute tells the compiler to generate implementations of the `Debug`, `Clone`, and `PartialEq` traits for `Point`. Without derive, you would need to write each implementation by hand.

This is directly analogous to Swift's automatic protocol conformance synthesis:

```swift
// Swift
struct Point: Equatable, CustomStringConvertible {
    var x: Double
    var y: Double

    var description: String {
        "Point(x: \(x), y: \(y))"
    }
}
```

Swift automatically synthesizes `Equatable` (and `Hashable`) conformance when all stored properties conform. Rust's derive does the same thing – it generates the implementation based on the fields.

Here are the most common derivable traits and their Swift counterparts:

| Rust derive | What it provides | Swift equivalent |
|---|---|---|
| `Debug` | Developer-facing string representation (`{:?}`) | `CustomDebugStringConvertible` |
| `Clone` | Explicit deep copy via `.clone()` | Implicit for value types |
| `Copy` | Implicit bitwise copy (for simple types) | Implicit for value types |
| `PartialEq` | Equality comparison with `==` | `Equatable` (auto-synthesized) |
| `Eq` | Marker for total equality (extends `PartialEq`) | No separate equivalent |
| `Hash` | Hashing for use in `HashMap`/`HashSet` | `Hashable` (auto-synthesized) |
| `Default` | Default value via `Default::default()` | No direct equivalent |
| `PartialOrd` / `Ord` | Ordering comparison | `Comparable` |

A few notes on the differences:

- Swift synthesizes `Equatable` and `Hashable` automatically when you declare conformance and all stored properties already conform. In Rust, you must explicitly write `#[derive(PartialEq, Hash)]` – nothing is derived unless you ask for it.
- Most Swift value types (`struct`, `enum`) are copyable by default, though modern Swift also has noncopyable types. In Rust, types are moved by default. You need `#[derive(Clone)]` for explicit copying and `#[derive(Copy, Clone)]` for implicit copying (only available for types where all fields are `Copy`).
- Third-party crates can define their own derive macros. `serde`'s `#[derive(Serialize, Deserialize)]` is the most prominent example – it generates serialization code the way Swift's `Codable` synthesis does.

## Attribute macros

Attribute macros are procedural macros that attach to items (functions, structs, modules) and can transform or augment them. You have already seen several:

```rust
// The #[test] attribute marks a function as a test
#[test]
fn it_works() {
    assert_eq!(2 + 2, 4);
}
```

```rust
// Fragment – #[tokio::main] transforms main into an async entry point
#[tokio::main]
async fn main() {
    println!("running in tokio");
}
```

The `#[tokio::main]` attribute macro rewrites your `async fn main()` into a regular `fn main()` that creates a tokio runtime and blocks on the async function. Without it, you would need to write the runtime setup manually:

```rust
// What #[tokio::main] expands to, roughly:
fn main() {
    tokio::runtime::Runtime::new()
        .unwrap()
        .block_on(async {
            println!("running in tokio");
        });
}
```

Other common attribute macros you will encounter:

- **`#[derive(...)]`**: technically an attribute macro itself, though it is used so frequently that it is often discussed separately
- **`#[cfg(...)]`**: conditional compilation (e.g., `#[cfg(test)]`, `#[cfg(target_os = "macos")]`)
- **`#[allow(...)]`** and **`#[warn(...)]`**: suppress or enable specific compiler warnings
- **`#[inline]`**: suggests that the compiler inline a function
- **`#[must_use]`**: warns if the return value is discarded. Swift warns on all unused return values by default and uses `@discardableResult` to suppress the warning; Rust does not warn by default and uses `#[must_use]` to opt into the warning

In Swift, attributes like `@Test`, `@main`, `@available`, and `@discardableResult` serve similar roles. Swift's attribute macros (introduced in SE-0389) can also transform declarations, bringing Swift closer to Rust's model.

## Function-like procedural macros

Function-like procedural macros look like function calls but with the `!` suffix. They take arbitrary token input and produce code as output. Unlike `macro_rules!` macros, procedural macros are written as separate Rust programs that run at compile time – they receive a stream of tokens and return a new stream of tokens.

A prominent example is `sqlx::query!` from the [sqlx](https://docs.rs/sqlx) crate:

```rust
// Fragment – requires sqlx dependency and a database connection
let query = sqlx::query!("SELECT * FROM users WHERE id = $1", user_id);
```

This macro checks your SQL query against your database schema *at compile time*. If the query is malformed or references a column that does not exist, you get a compilation error rather than a runtime crash. This level of compile-time validation is something that Rust's macro system enables but that has no equivalent in standard Swift.

Other examples of function-like procedural macros:

- **`serde_json::json!`**: constructs JSON values with a JSON-like syntax
- **`lazy_static!`** (now largely superseded by `std::sync::LazyLock`): defines lazily initialized statics
- **`include_str!`** and **`include_bytes!`**: embed file contents as a string or byte array at compile time

## How Rust macros compare to Swift macros

Swift introduced expression macros, declaration macros, and attached macros starting in Swift 5.9 (SE-0382, SE-0389, and related proposals). The two systems share some goals but differ significantly in design:

| Aspect | Rust macros | Swift macros |
|---|---|---|
| Prevalence | Ubiquitous – used in almost every project | Still emerging – adoption is growing |
| Declarative pattern matching | `macro_rules!` – lightweight, no separate crate | Not available – all Swift macros are procedural |
| Procedural macros | Written as separate crates, operate on token streams | Written as separate modules, operate on SwiftSyntax ASTs |
| Derive/attached macros | `#[derive(Trait)]` for automatic trait implementations | `@attached(member)`, `@attached(extension)` for conformances |
| Compile-time code execution | Procedural macros are Rust programs that run during compilation | Swift macros are Swift programs that run during compilation |
| Hygiene | `macro_rules!` macros are partially hygienic (local variables do not leak) | Swift macros are fully hygienic by design |
| Built-in macros | `println!`, `vec!`, `format!`, `assert!`, etc. | `#expect`, `#stringify`, `#Predicate`, etc. |

The most important takeaway for Swift developers is this: many things that are language features or protocol conformances in Swift are macros in Rust. Swift has built-in string interpolation; Rust uses `format!`. Swift has array literals; Rust uses `vec!`. Swift auto-synthesizes `Equatable`; Rust uses `#[derive(PartialEq)]`. The boundary between "language feature" and "macro" is drawn differently in Rust, and macros carry more of the weight.

## Writing procedural macros: a brief overview

Writing your own procedural macros is an advanced topic. Procedural macros must be defined in a separate crate with a specific crate type (`proc-macro`), and they depend on the `proc_macro` API from the standard library (plus typically the `syn` and `quote` crates for parsing and generating token streams).

Here is a sketch of what a derive macro implementation looks like:

```rust
// In a separate crate: my_derive/src/lib.rs
// This is a high-level sketch – the actual implementation
// uses the syn and quote crates for parsing and code generation
use proc_macro::TokenStream;

#[proc_macro_derive(MyTrait)]
pub fn derive_my_trait(input: TokenStream) -> TokenStream {
    // 1. Parse the input tokens into a syntax tree (using syn)
    // 2. Extract the struct name and fields
    // 3. Generate the trait implementation (using quote)
    // 4. Return the generated tokens
    todo!()
}
```

And the usage:

```rust
// In your main crate
use my_derive::MyTrait;

#[derive(MyTrait)]
struct Config {
    name: String,
    verbose: bool,
}
```

This is conceptually similar to how Swift macros work – you write a Swift program that uses SwiftSyntax to transform or generate code, and the compiler invokes it during compilation. The tooling differs, but the mental model of "a program that writes code" is the same.

For most Rust developers, *using* derive and attribute macros is routine. *Writing* them is less common and typically done by library authors who want to provide ergonomic APIs for their users. If you are interested in writing procedural macros, the `syn`, `quote`, and `proc-macro2` crates form the standard toolkit, and the [Rust Reference chapter on procedural macros](https://doc.rust-lang.org/reference/procedural-macros.html) covers the details.

## Key differences and gotchas

**The `!` is significant**: in Rust, `println()` (without `!`) would be a function call. `println!()` (with `!`) is a macro invocation. If you forget the `!`, the compiler will tell you that the function does not exist. This distinction does not exist in Swift – there is no syntactic marker for macro invocations beyond the `#` or `@` prefixes.

**Macros must be in scope**: declarative macros defined with `macro_rules!` follow specific scoping rules. A macro defined in a module is only available in that module and its children unless you export it with `#[macro_export]`. Third-party macros need to be imported via `use`.

**Compile-time cost**: macros expand during compilation, and heavy macro usage can increase compile times. Derive macros in particular add compilation overhead for each type they are applied to. In large projects, this is usually not a problem, but it is worth being aware of if build times become an issue.

**Error messages can be opaque**: when a macro expansion produces invalid code, the compiler error points to the macro invocation rather than the generated code. This can make debugging difficult. The `cargo expand` command (from the `cargo-expand` crate) lets you see the fully expanded code, which is invaluable for understanding what a macro actually generates.

**`macro_rules!` is not Turing-complete but is surprisingly capable**: declarative macros support recursion, repetition, and multiple match arms. You can implement surprisingly complex code generation with `macro_rules!` alone, without resorting to procedural macros. However, `macro_rules!` cannot inspect types or perform semantic analysis – it operates purely on syntax patterns.

## Further reading

- [The Rust Programming Language – Macros](https://doc.rust-lang.org/book/ch20-06-macros.html): introduction to macros
- [The Rust Reference – Macros](https://doc.rust-lang.org/reference/macros.html): formal specification of `macro_rules!`
- [The Rust Reference – Procedural Macros](https://doc.rust-lang.org/reference/procedural-macros.html): the procedural macro API
- [The Little Book of Rust Macros](https://veykril.github.io/tlborm/): in-depth guide to `macro_rules!` patterns
- [Procedural Macros Workshop](https://github.com/dtolnay/proc-macro-workshop): hands-on exercises for learning to write procedural macros
- [syn](https://docs.rs/syn): the standard crate for parsing Rust syntax in procedural macros
- [quote](https://docs.rs/quote): the standard crate for generating Rust tokens in procedural macros
- [cargo-expand](https://github.com/dtolnay/cargo-expand): view the expanded output of macros
