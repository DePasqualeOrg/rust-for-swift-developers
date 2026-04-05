---
title: Generics
sidebar:
  order: 16
---

Generics let you write code that works across multiple types while preserving type safety. Swift developers use generics constantly – from `Array<Element>` and `Result<Success, Failure>` to custom data structures and protocol-constrained functions. Rust's generics serve the same purpose and follow a similar syntax, but the way you constrain them uses traits rather than protocols, and the compilation model has some interesting implications for performance.

## Generic functions

In Swift, you write a generic function by placing type parameters in angle brackets:

```swift
// Swift
func largest<T: Comparable>(_ a: T, _ b: T) -> T {
    a > b ? a : b
}
```

Rust uses the same angle-bracket syntax, with trait bounds replacing protocol constraints:

```rust
// Rust
fn largest<T: PartialOrd>(a: T, b: T) -> T {
    if a > b { a } else { b }
}
```

`Comparable` in Swift maps most closely to `Ord` in Rust (total ordering). Rust also has `PartialOrd` for types without a total ordering, such as floating-point numbers. The type parameter `T` must satisfy the bound, or the code will not compile.

One difference is ownership. In the Rust function above, `a` and `b` are moved into the function. If `T` does not implement `Copy`, calling `largest` consumes the values. Swift's value types are implicitly copyable, so this is not something Swift developers typically think about.

## Generic structs and enums

Both languages let you define generic data structures:

```swift
// Swift
struct Pair<A, B> {
    let first: A
    let second: B
}

let pair = Pair(first: "hello", second: 42)
```

```rust
// Rust
struct Pair<A, B> {
    first: A,
    second: B,
}

let pair = Pair { first: "hello", second: 42 };
```

Generic enums work the same way. Rust's `Option<T>` and `Result<T, E>` are the canonical examples:

```rust
// Rust
enum Shape<T> {
    Circle { radius: T },
    Rectangle { width: T, height: T },
}

fn main() {
    let s: Shape<f64> = Shape::Circle { radius: 5.0 };
    match s {
        Shape::Circle { radius } => println!("Circle with radius {radius}"),
        Shape::Rectangle { width, height } => {
            println!("Rectangle {width} x {height}")
        }
    }
}
```

## Trait bounds

Trait bounds constrain what a generic type can do. Without bounds, you can only perform operations that work on any type – essentially, you can move it, drop it, and not much else. Bounds unlock the methods defined by traits.

### Single bounds

```swift
// Swift
func printItem<T: CustomStringConvertible>(_ item: T) {
    print(item.description)
}
```

```rust
// Rust
use std::fmt::Display;

fn print_item<T: Display>(item: &T) {
    println!("{item}");
}

print_item(&42);
print_item(&"hello");
```

### Multiple bounds

When you need a type to satisfy multiple traits, use `+` in Rust. Swift uses `&`:

```swift
// Swift
func process<T: Equatable & CustomStringConvertible>(_ item: T) {
    print(item.description)
}
```

```rust
// Rust
use std::fmt::{Debug, Display};

fn process<T: Display + Debug>(item: &T) {
    println!("display: {item}, debug: {item:?}");
}

process(&42);
```

### `where` clauses

When bounds become complex, both languages let you move them to a `where` clause for readability:

```swift
// Swift
func combine<A, B>(_ a: A, _ b: B) -> String
    where A: CustomStringConvertible, B: CustomStringConvertible
{
    "\(a) and \(b)"
}
```

```rust
// Rust
use std::fmt::Display;

fn combine<A, B>(a: &A, b: &B) -> String
where
    A: Display,
    B: Display,
{
    format!("{a} and {b}")
}
```

`where` clauses are especially useful when bounds involve associated types or relationships between type parameters. In Rust, you will see them frequently in standard library signatures.

### The `impl Trait` shorthand

For simple cases, Rust offers `impl Trait` in argument position as a shorthand for a trait-bounded generic:

```rust
// Rust
use std::fmt::Display;

// These two signatures are equivalent
fn print_a<T: Display>(item: &T) {
    println!("{item}");
}

fn print_b(item: &impl Display) {
    println!("{item}");
}

print_a(&42);
print_b(&42);
```

The `impl Trait` form is concise, but it creates an anonymous type parameter that you cannot name elsewhere in the signature. Use the explicit `<T: Trait>` form when you need the same type in multiple positions:

```rust
// Rust
use std::fmt::Display;

// T ensures both parameters and the return value are the same type
fn pick<T: Display>(a: T, b: T, first: bool) -> T {
    if first { a } else { b }
}
```

## Generic `impl` blocks

You can implement methods on a generic type by parameterizing the `impl` block:

```rust
// Rust
struct Wrapper<T> {
    value: T,
}

impl<T> Wrapper<T> {
    fn new(value: T) -> Self {
        Wrapper { value }
    }

    fn into_inner(self) -> T {
        self.value
    }
}
```

You can also write `impl` blocks that only apply when `T` meets certain bounds. This is similar to conditional conformance in Swift:

```swift
// Swift
extension Array: CustomStringConvertible where Element: CustomStringConvertible {
    public var description: String {
        "[" + map(\.description).joined(separator: ", ") + "]"
    }
}
```

```rust
// Rust
use std::fmt;

struct Wrapper<T> {
    value: T,
}

impl<T: fmt::Display> fmt::Display for Wrapper<T> {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "Wrapped({})", self.value)
    }
}

impl<T: Default> Wrapper<T> {
    fn new_default() -> Self {
        Wrapper { value: T::default() }
    }
}
```

The `Display` implementation only exists for `Wrapper<T>` when `T` itself implements `Display`. The `new_default` method only exists when `T` implements `Default`. The compiler enforces these constraints at each call site.

## Monomorphization

Rust monomorphizes generic code – the compiler generates a specialized copy of the function or type for each concrete type it is used with. When you call `largest(3, 7)` and `largest(2.5, 1.8)`, the compiler generates two functions: one for `i32` and one for `f64`.

This means generic code has zero runtime overhead. The compiled output is identical to what you would get if you had written separate functions by hand.

```rust
// Rust
// The compiler turns this:
fn add<T: std::ops::Add<Output = T>>(a: T, b: T) -> T {
    a + b
}

let x = add(1_i32, 2_i32);
let y = add(1.0_f64, 2.0_f64);

// Into something equivalent to:
// fn add_i32(a: i32, b: i32) -> i32 { a + b }
// fn add_f64(a: f64, b: f64) -> f64 { a + b }
```

Swift can also specialize generic code when the optimizer has visibility into concrete types, but its model also relies on type metadata and witness tables, especially across module boundaries. Rust generic type parameters are monomorphized – there is no separate runtime-dispatch path for them.

The tradeoff is compile time and binary size. If you instantiate a generic function with many different types, the compiler generates many copies. In practice this is rarely a problem, but it explains why Rust compile times can be longer than expected for heavily generic code.

## Const generics

Rust supports const generics, which let you parameterize types over constant values – typically array sizes. This is a feature Swift does not have:

```rust
// Rust
#[derive(Debug)]
struct Matrix<const ROWS: usize, const COLS: usize> {
    data: [[f64; COLS]; ROWS],
}

impl<const ROWS: usize, const COLS: usize> Matrix<ROWS, COLS> {
    fn new() -> Self {
        Matrix {
            data: [[0.0; COLS]; ROWS],
        }
    }

    fn rows(&self) -> usize {
        ROWS
    }

    fn cols(&self) -> usize {
        COLS
    }
}
```

The size is part of the type: `Matrix<3, 4>` and `Matrix<2, 2>` are different types. The compiler verifies size constraints at compile time and can optimize accordingly. Const generics are most commonly used with arrays, since Rust's array type `[T; N]` requires a compile-time-known length.

Swift uses runtime values for collection sizes. The closest Swift equivalent would be generic types constrained to fixed-size tuples, but there is no general const generics feature.

## Key differences and gotchas

- **Ownership in generics**: In Swift, passing a value type to a generic function copies it implicitly. In Rust, the value is moved unless the type implements `Copy`. You often take generic parameters by reference (`&T`) to avoid consuming them.
- **No implicit copyability**: A generic `T` in Rust cannot be copied unless you add a `Copy` or `Clone` bound. In Swift, all value types are implicitly copyable (with some recent exceptions under the noncopyable types proposal).
- **Rust generic parameters are monomorphized**: this differs from Swift, which can specialize generic code but also relies on witness tables and metadata in many cases. (For runtime dispatch, Rust uses trait objects, covered in the [next chapter](../trait-objects/).)
- **No specialization** (stable): Rust does not yet have stable specialization – you cannot provide a more specific implementation of a generic function for a particular type. Swift allows this through overloading and conditional conformances.
- **Bounds are required, not inferred**: Rust requires you to explicitly state every trait bound. If your generic function calls `.to_string()` on a value of type `T`, you must add `T: ToString` as a bound. The compiler does not infer bounds from usage, unlike Swift, which can sometimes resolve protocol requirements through associated types.
- **`where` clause placement**: In Rust, the `where` clause comes after the return type but before the opening brace. In Swift, it comes after the return type and before the opening brace as well – the placement is the same.
- **Const generics are limited**: Currently, const generic parameters must be integers, `bool`, or `char`. More complex types are not yet supported on stable Rust.

## Further reading

- [Generic Types, Traits, and Lifetimes](https://doc.rust-lang.org/book/ch10-00-generics.html): The Rust Programming Language
- [Generic Data Types](https://doc.rust-lang.org/book/ch10-01-syntax.html): The Rust Programming Language
- [Const Generics](https://doc.rust-lang.org/reference/items/generics.html#const-generics): The Rust Reference
- [Monomorphization](https://rustc-dev-guide.rust-lang.org/backend/monomorph.html): Rust Compiler Development Guide
