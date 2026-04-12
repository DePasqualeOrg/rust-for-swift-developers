---
title: Traits
sidebar:
  order: 15
---

Traits are Rust's primary mechanism for defining shared behavior across types – they fill the same role as protocols in Swift. If you have used Swift protocols to define interfaces, provide default implementations, and constrain generics, you will find traits immediately familiar. The concepts map closely, but the rules around where and how you can implement them differ in important ways.

## Defining a trait

A Swift protocol declares a set of requirements that conforming types must satisfy. A Rust trait does the same:

```swift
// Swift
protocol Describable {
    func describe() -> String
}
```

```rust
// Rust
trait Describable {
    fn describe(&self) -> String;
}
```

The structure is nearly identical. The trait declares a method signature, and any type that implements the trait must provide a body for that method. In Rust, `&self` is the receiver – it borrows the value, similar to how Swift methods implicitly receive `self`.

Traits can also require associated constants and types, just as Swift protocols can require associated types and static properties. Associated types in traits are covered in the [Generics](../generics/) chapter.

## Implementing a trait for a type

In Swift, you conform to a protocol with an extension or directly in the type declaration:

```swift
// Swift
struct Circle {
    let radius: Double
}

extension Circle: Describable {
    func describe() -> String {
        "Circle with radius \(radius)"
    }
}
```

In Rust, you use an `impl Trait for Type` block:

```rust
// Rust
struct Circle {
    radius: f64,
}

impl Describable for Circle {
    fn describe(&self) -> String {
        format!("Circle with radius {}", self.radius)
    }
}
```

The `impl ... for ...` syntax separates the trait implementation from the type's inherent methods. You can have multiple `impl` blocks for the same type – one for each trait, plus one for methods that belong to the type itself:

```rust
// Rust
impl Circle {
    fn area(&self) -> f64 {
        std::f64::consts::PI * self.radius * self.radius
    }
}
```

This is similar to how Swift developers often put protocol conformances in separate extensions, keeping them organized by protocol.

## Default method implementations

Both languages let you provide default implementations in the trait or protocol itself. In Swift:

```swift
// Swift
protocol Greetable {
    var name: String { get }
    func greet() -> String
}

extension Greetable {
    func greet() -> String {
        "Hello, \(name)!"
    }
}
```

In Rust, you put the default body directly in the trait definition:

```rust
// Rust
trait Greetable {
    fn name(&self) -> &str;

    fn greet(&self) -> String {
        format!("Hello, {}!", self.name())
    }
}

struct User {
    name: String,
}

impl Greetable for User {
    fn name(&self) -> &str {
        &self.name
    }
    // greet() uses the default implementation
}

let user = User { name: String::from("Alice") };
user.greet(); // "Hello, Alice!"
```

Types can override the default by providing their own implementation in the `impl` block, just as Swift types can override default protocol implementations.

## Trait bounds on functions

When you want a function to accept any type that implements a trait, Rust uses trait bounds. This is the equivalent of Swift's constrained generics:

```swift
// Swift
func printDescription<T: Describable>(_ item: T) {
    print(item.describe())
}
```

```rust
// Rust
fn print_description(item: &impl Describable) {
    println!("{}", item.describe());
}
```

The `impl Trait` syntax in argument position is shorthand for a generic parameter with a trait bound. You can also write it explicitly:

```rust
// Rust
fn print_description<T: Describable>(item: &T) {
    println!("{}", item.describe());
}
```

Both forms compile to the same code. The explicit form is necessary when you need to refer to the type parameter `T` in multiple places or apply additional constraints.

For multiple trait bounds, Rust uses `+`:

```swift
// Swift
func process<T: Describable & Equatable>(_ item: T) { ... }
```

```rust
// Rust
fn process<T: Describable + PartialEq>(item: &T) {
    // ...
}
```

When bounds get complex, Rust offers a `where` clause that moves them after the parameter list. Swift has the same feature:

```swift
// Swift
func merge<A, B>(_ a: A, _ b: B) -> String
    where A: Describable, B: Describable
{
    a.describe() + " " + b.describe()
}
```

```rust
// Rust
fn merge<A, B>(a: &A, b: &B) -> String
where
    A: Describable,
    B: Describable,
{
    format!("{} {}", a.describe(), b.describe())
}
```

## Supertraits (trait inheritance)

A trait can require that implementors also implement another trait. This is Rust's version of protocol inheritance:

```swift
// Swift
protocol Named {
    var name: String { get }
}

protocol Printable: Named {
    func printInfo()
}
```

```rust
// Rust
trait Named {
    fn name(&self) -> &str;
}

trait Printable: Named {
    fn print_info(&self);
}

struct Employee {
    name: String,
    role: String,
}

impl Named for Employee {
    fn name(&self) -> &str {
        &self.name
    }
}

impl Printable for Employee {
    fn print_info(&self) {
        println!("{} ({})", self.name(), self.role);
    }
}

let emp = Employee {
    name: String::from("Alice"),
    role: String::from("Engineer"),
};
emp.print_info();
```

When you implement `Printable`, you must also implement `Named`. The supertrait's methods are available within the subtrait's methods – `self.name()` works inside `print_info` because `Named` is a supertrait.

## Common standard library traits

Rust's standard library defines a rich set of traits that serve as the foundation for the type system. Many of these correspond to Swift protocols you already know.

### `Display` and `Debug`

`Display` controls how a type is formatted with `{}` in format strings. It corresponds to Swift's `CustomStringConvertible`:

```rust
// Rust
use std::fmt;

struct Point {
    x: f64,
    y: f64,
}

impl fmt::Display for Point {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "({}, {})", self.x, self.y)
    }
}

let p = Point { x: 1.0, y: 2.5 };
p.to_string(); // "(1, 2.5)"
```

`Debug` controls the `{:?}` format and is used for developer-facing output, similar to Swift's `CustomDebugStringConvertible`. Unlike `Display`, `Debug` can be automatically derived.

### `Default`

`Default` provides a default value for a type, similar to how Swift types can have default initializers:

```rust
// Rust
#[derive(Debug)]
struct Config {
    retries: u32,
    timeout: f64,
    verbose: bool,
}

impl Default for Config {
    fn default() -> Self {
        Config {
            retries: 3,
            timeout: 30.0,
            verbose: false,
        }
    }
}

let config = Config::default();
```

### `PartialEq`, `Eq`, and `Hash`

`PartialEq` enables `==` and `!=` comparisons, corresponding to Swift's `Equatable`. `Eq` is a marker trait (no additional methods) that signals the equality relation is total – it is reflexive for all values. Floating-point types implement `PartialEq` but not `Eq`, because `NaN != NaN`.

`Hash` corresponds to Swift's `Hashable` and is required for using a type as a key in a `HashMap`.

### `From` and `Into`

`From` and `Into` define type conversions. Implementing `From<A> for B` automatically provides `Into<B> for A`:

```rust
// Rust
struct Meters(f64);
struct Kilometers(f64);

impl From<Kilometers> for Meters {
    fn from(km: Kilometers) -> Self {
        Meters(km.0 * 1000.0)
    }
}

let distance = Kilometers(5.0);
let meters: Meters = distance.into(); // uses the auto-generated Into impl
```

There is no direct Swift equivalent, but it resembles defining `init` convenience initializers that convert from one type to another.

### Summary of correspondences

| Rust trait       | Swift protocol                   | Purpose                         |
|------------------|----------------------------------|---------------------------------|
| `Display`        | `CustomStringConvertible`        | User-facing string formatting   |
| `Debug`          | `CustomDebugStringConvertible`   | Developer-facing formatting     |
| `Default`        | (default `init()`)               | Default value construction      |
| `PartialEq`/`Eq` | `Equatable`                     | Equality comparison             |
| `PartialOrd`/`Ord` | `Comparable`                  | Ordering comparison             |
| `Hash`           | `Hashable`                       | Hash computation                |
| `Clone`          | (value semantics / `copy()`)     | Explicit duplication            |
| `Copy`           | (implicit for value types)       | Implicit bitwise copy           |
| `From`/`Into`    | (`init(from:)` patterns)         | Type conversion                 |
| `Iterator`       | `IteratorProtocol`               | Iteration                       |

## Deriving traits with `#[derive(...)]`

Many standard traits have mechanical implementations that the compiler can generate for you. Rust's `#[derive]` attribute is similar to how Swift automatically synthesizes `Equatable`, `Hashable`, and `Codable` conformances:

```swift
// Swift
struct Point: Equatable, Hashable, Codable {
    let x: Double
    let y: Double
    // Equatable, Hashable, and Codable are auto-synthesized
}
```

```rust
// Rust
#[derive(Debug, Clone, PartialEq)]
struct Point {
    x: f64,
    y: f64,
}

let p1 = Point { x: 1.0, y: 2.0 };
let p2 = p1.clone(); // Clone
format!("{:?}", p1); // Debug
p1 == p2; // PartialEq
```

Derivable standard traits include `Debug`, `Clone`, `Copy`, `PartialEq`, `Eq`, `Hash`, `PartialOrd`, `Ord`, and `Default`. The derive macro works only when all fields implement the trait being derived – the same rule that applies to Swift's automatic conformance synthesis.

You can also derive traits from external crates. For example, the `serde` crate provides `#[derive(Serialize, Deserialize)]`, which is Rust's equivalent of Swift's `Codable`.

## The orphan rule

This is one of the most important differences between Rust and Swift. Rust enforces the orphan rule: you can only implement a trait for a type if you own the trait or the type (or both). You cannot implement a foreign trait for a foreign type.

```rust
// Rust – this would NOT compile
// You don't own Display and you don't own Vec
// impl std::fmt::Display for Vec<i32> { ... }
```

Swift has no such restriction. You can add protocol conformances to any type from any module using extensions:

```swift
// Swift – this compiles
protocol PrettyPrintable {
    var prettyDescription: String { get }
}

extension Array: PrettyPrintable where Element: CustomStringConvertible {
    var prettyDescription: String {
        "[" + map(\.description).joined(separator: ", ") + "]"
    }
}
```

The orphan rule exists to prevent conflicting implementations. If two crates could each implement the same trait for the same type, the compiler would not know which to use. Swift avoids this issue through its module system and conformance-checking rules, but it can still run into ambiguity at link time.

The common workaround in Rust is the newtype pattern: wrap the foreign type in your own struct and implement the trait on the wrapper:

```rust
// Rust
use std::fmt;

struct PrettyVec(Vec<i32>);

impl fmt::Display for PrettyVec {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        let items: Vec<String> = self.0.iter().map(|n| n.to_string()).collect();
        write!(f, "[{}]", items.join(", "))
    }
}

let v = PrettyVec(vec![1, 2, 3]);
v.to_string(); // "[1, 2, 3]"
```

## Extension trait pattern

The orphan rule permits one case that is especially useful: you can implement a trait you own for a type you do not own. This is the direct analog to Swift's `extension String { ... }` – you attach new behavior to a standard-library type by defining a trait and implementing it:

```rust
// Rust
trait Titlecase {
    fn titlecase(&self) -> String;
}

impl Titlecase for str {
    fn titlecase(&self) -> String {
        self.split_whitespace()
            .map(|word| {
                let mut chars = word.chars();
                match chars.next() {
                    Some(c) => c.to_uppercase().collect::<String>() + chars.as_str(),
                    None => String::new(),
                }
            })
            .collect::<Vec<_>>()
            .join(" ")
    }
}

fn main() {
    let heading = "hello world".titlecase();
    println!("{heading}"); // "Hello World"
}
```

Callers must import the trait into scope (`use your_crate::Titlecase`) before the method becomes visible. This differs from Swift, where extensions are visible as soon as the defining module is imported. The upside is that name collisions between multiple extension traits are resolved explicitly at the call site rather than silently at link time. Crates that publish a suite of extension traits often gather them in a `prelude` module so users can opt into the whole set with a single `use your_crate::prelude::*`.

### Blanket implementations

A blanket impl is an extension trait whose implementation applies to every type satisfying a bound. It is the Rust analog of Swift's `extension Protocol where Self: X { ... }`:

```rust
// Rust
use std::fmt::Display;

trait LoggedDisplay {
    fn log(&self);
}

impl<T: Display> LoggedDisplay for T {
    fn log(&self) {
        eprintln!("[LOG] {self}");
    }
}

fn main() {
    42.log();
    "hello".log();
}
```

Every type that implements `Display` automatically implements `LoggedDisplay`. The standard library uses this pattern extensively. For example, implementing `From<T> for U` automatically gives you `Into<U> for T`, courtesy of a blanket impl `impl<T, U: From<T>> Into<U> for T` in `core`.

## Key differences and gotchas

- **No stored properties in traits**: Rust traits cannot declare stored fields. Swift protocols can require properties, but only through getters (and optionally setters). In Rust, you define accessor methods instead.
- **No optional requirements**: Swift has `@objc optional` protocol requirements. Rust has no equivalent – every trait method must be implemented (or have a default).
- **Extension methods vs inherent methods**: In Swift, you can add methods to a type without any protocol using extensions. In Rust, you can add inherent methods with a plain `impl Type` block, but you cannot add methods to types you do not own without defining a trait.
- **The orphan rule**: You cannot implement a foreign trait for a foreign type. This is the biggest structural difference from Swift's open extension model.
- **Trait coherence**: Because of the orphan rule, Rust guarantees that there is at most one implementation of a trait for any given type. This eliminates ambiguity that can arise in Swift when multiple modules extend the same type with the same protocol conformance.
- **No class inheritance**: Rust has no class hierarchy. Supertraits define required capabilities, not an inheritance chain. There is no `override` keyword because there is no method dispatch through a class hierarchy.
- **`self` parameter styles**: Trait methods can take `&self` (borrow), `&mut self` (mutable borrow), or `self` (take ownership). The choice affects what the method can do with the value. Swift value type methods receive an implicit copy of `self` (or `inout self` for `mutating` methods), while class methods receive `self` by reference.

## Further reading

- [Traits: Defining Shared Behavior](https://doc.rust-lang.org/book/ch10-02-traits.html): The Rust Programming Language
- [Traits](https://doc.rust-lang.org/reference/items/traits.html): The Rust Reference
- [Derive](https://doc.rust-lang.org/reference/attributes/derive.html): The Rust Reference
- [Common Trait Implementations](https://doc.rust-lang.org/rust-by-example/trait.html): Rust by Example
- [The Orphan Rule](https://doc.rust-lang.org/reference/items/implementations.html#orphan-rules): The Rust Reference
