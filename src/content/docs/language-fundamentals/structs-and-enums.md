---
title: Structs and Enums
sidebar:
  order: 7
---

Structs and enums are the fundamental building blocks of data modeling in both Swift and Rust. The two languages share the same core ideas – named fields, methods, associated functions, and enums with associated data – but organize them differently. The biggest structural difference is that Rust separates data definition from behavior: you define a struct's fields in one place and its methods in a separate `impl` block.

## Defining structs

Both languages define structs with named fields, but the syntax for instantiation differs:

```swift
// Swift
struct Point {
    var x: Double
    var y: Double
}

let origin = Point(x: 0.0, y: 0.0)
```

```rust
// Rust
struct Point {
    x: f64,
    y: f64,
}

let origin = Point { x: 0.0, y: 0.0 };
```

Swift uses a function-call-style initializer with parentheses, while Rust uses curly braces. Rust generates no automatic initializer – you always construct structs with the literal `StructName { field: value }` syntax.

### Field init shorthand

When a variable has the same name as a struct field, Rust lets you omit the `field: value` repetition:

```rust
// Rust
struct Point {
    x: f64,
    y: f64,
}

fn make_point(x: f64, y: f64) -> Point {
    Point { x, y } // shorthand for Point { x: x, y: y }
}
```

Swift does not have this shorthand – you always write the labels explicitly.

### Struct update syntax

Rust has a spread-like syntax for creating a new struct from an existing one, replacing only the fields you specify:

```rust
// Rust
struct Config {
    width: u32,
    height: u32,
    fullscreen: bool,
}

let default_config = Config {
    width: 1920,
    height: 1080,
    fullscreen: false,
};

let custom = Config {
    fullscreen: true,
    ..default_config
};
```

Swift does not have a built-in equivalent, though you can achieve a similar effect by copying a struct and modifying properties (since Swift structs are value types with `var` properties).

### Config struct pattern

Swift's memberwise initializers make it easy to call a function with many named options – you list the labels at the call site and omit any that have defaults. Rust functions have no argument labels and no parameter defaults, so as the number of arguments grows, call sites get harder to read. The idiomatic response is to group the options into a struct that implements `Default`, then let callers override only the fields they care about using struct update syntax:

```rust
// Rust
#[derive(Default)]
struct QueryOptions {
    limit: usize,
    offset: usize,
    include_archived: bool,
}

fn query(_opts: QueryOptions) {
    // ...
}

fn main() {
    query(QueryOptions {
        limit: 50,
        ..Default::default()
    });
}
```

The field names at the call site act like Swift's argument labels, and new options can be added to `QueryOptions` without breaking existing callers. This is the Rust counterpart to Swift's memberwise init with default values.

A config struct is not always the right tool. Reach for a builder when:

- **Construction is staged**: the caller configures the value across several scopes or functions before handing it off.
- **Some combinations of fields are invalid**: a builder can change its own type once a required field is set, letting the type system forbid ill-formed combinations.
- **Construction can fail**: if building up the value surfaces errors (validation, DNS resolution, I/O), a `build(self) -> Result<...>` method is clearer than populating a struct and validating after the fact.

The `reqwest::Client` and `tokio::runtime::Builder` APIs are canonical examples. Both exist because `Default` alone cannot express their construction semantics.

### Per-field defaults

Swift lets you attach defaults directly to stored properties: `var width: Int = 800`. Rust does not yet have this on stable, but there are several approximations.

The stable baseline is a hand-written `impl Default`. It is verbose, but every approach below compiles down to this:

```rust
// Rust
struct Window {
    width: u32,
    height: u32,
    title: String,
}

impl Default for Window {
    fn default() -> Self {
        Window {
            width: 800,
            height: 600,
            title: String::from("Untitled"),
        }
    }
}
```

`#[derive(Default)]` is stable and terse, but only works when every field's type already implements `Default` and you are happy with those defaults (`0` for integers, empty strings, `false` for booleans). The derive itself offers no way to customize individual fields:

```rust
// Rust
#[derive(Default)]
struct Window {
    width: u32,    // defaults to 0
    height: u32,   // defaults to 0
    title: String, // defaults to ""
}
```

Third-party crates like [`smart-default`](https://docs.rs/smart-default) extend `#[derive(Default)]` with per-field attributes:

```rust
// Rust
use smart_default::SmartDefault;

#[derive(SmartDefault)]
struct Window {
    #[default = 800]
    width: u32,
    #[default = 600]
    height: u32,
    #[default(_code = "String::from(\"Untitled\")")]
    title: String,
}
```

This matches the Swift ergonomics today at the cost of an extra dependency. `smart-default` itself is stable but low-activity; before reaching for it in a long-lived project, check current releases and consider `derive-new` as a closer alternative, or a full builder crate like `bon` if you also want builder-style construction.

**On the horizon.** Rust has an accepted RFC, [RFC 3681 "Default field values"](https://github.com/rust-lang/rfcs/blob/master/text/3681-default-field-values.md), that will eventually let you write defaults directly in the struct definition:

```rust
// Rust, nightly only
#![feature(default_field_values)]

struct Window {
    width: u32 = 800,
    height: u32 = 600,
}

fn main() {
    let w = Window { width: 1024, .. };
    let _ = w;
}
```

This is currently usable only on the nightly compiler behind `#![feature(default_field_values)]`. Defaults must be const-evaluable today, which rules out things like `String::from("...")` – that restriction may relax before stabilization. The tracking issue is [rust-lang/rust#132162](https://github.com/rust-lang/rust/issues/132162). No stabilization release has been assigned, so check the current status before relying on it.

### Tuple structs

Rust also supports tuple structs – structs with unnamed fields accessed by index. These are useful for creating distinct types around a single value (the newtype pattern):

```rust
// Rust
struct Meters(f64);
struct Seconds(f64);

let distance = Meters(100.0);
let duration = Seconds(9.58);
```

Swift does not have tuple structs, but you can achieve the same effect with a regular struct that has a single property.

### Unit structs

Rust supports unit structs – structs with no fields at all. They occupy zero bytes and are useful as marker types or when implementing traits:

```rust
// Rust
struct Marker;

let _m = Marker;
```

## Methods and `impl` blocks

In Swift, methods are defined inside the type's body. In Rust, methods are defined in a separate `impl` (implementation) block:

```swift
// Swift
struct Circle {
    var radius: Double

    func area() -> Double {
        return .pi * radius * radius
    }

    mutating func scale(by factor: Double) {
        radius *= factor
    }
}
```

```rust
// Rust
struct Circle {
    radius: f64,
}

impl Circle {
    fn area(&self) -> f64 {
        std::f64::consts::PI * self.radius * self.radius
    }

    fn scale(&mut self, factor: f64) {
        self.radius *= factor;
    }
}

fn main() {
    let mut c = Circle { radius: 5.0 };
    println!("Area: {}", c.area());
    c.scale(2.0);
    println!("Scaled area: {}", c.area());
}
```

### The `self` parameter

In Swift, `self` is implicitly available in all methods. In Rust, the first parameter of a method must be `self` in one of these forms:

- **`&self`**: borrows the value immutably (like a non-mutating method in Swift)
- **`&mut self`**: borrows the value mutably (like a `mutating` method in Swift)
- **`self`**: takes ownership of the value (consumes it – the caller can no longer use it)

```rust
// Rust
struct Ticket {
    id: u32,
    description: String,
}

impl Ticket {
    fn summary(&self) -> String {
        format!("#{}: {}", self.id, self.description)
    }

    fn update_description(&mut self, new_desc: String) {
        self.description = new_desc;
    }

    fn into_description(self) -> String {
        self.description // takes ownership, Ticket is consumed
    }
}

fn main() {
    let mut ticket = Ticket {
        id: 1,
        description: String::from("Fix login bug"),
    };

    println!("{}", ticket.summary());
    ticket.update_description(String::from("Fix auth bug"));
    println!("{}", ticket.summary());

    let desc = ticket.into_description();
    // ticket is no longer usable here – it was moved
    println!("Description: {desc}");
}
```

The `self` (by value) form has no direct Swift equivalent. In Swift, structs are value types and do not have the concept of ownership transfer. Methods cannot consume the instance. In Rust, `self` by value means the method takes ownership and the original is moved. This is part of the ownership system covered in [Part III](../../ownership-system/ownership-basics/).

### Fluent method chaining

Taking `self` by value and returning `Self` lets a method produce a modified copy of the receiver. Chaining these calls gives Rust the same feel as SwiftUI's view modifiers:

```rust
// Rust
struct RequestConfig {
    url: String,
    timeout_secs: u32,
    retries: u32,
}

impl RequestConfig {
    fn new(url: &str) -> Self {
        RequestConfig {
            url: url.to_string(),
            timeout_secs: 30,
            retries: 0,
        }
    }

    fn timeout(mut self, seconds: u32) -> Self {
        self.timeout_secs = seconds;
        self
    }

    fn retries(mut self, count: u32) -> Self {
        self.retries = count;
        self
    }
}

fn main() {
    let config = RequestConfig::new("https://example.com")
        .timeout(5)
        .retries(3);
    let _ = config;
}
```

This style is widely used in configuration-heavy crates – `reqwest::ClientBuilder`, `tokio::runtime::Builder`, and `clap::Command` all use variations of it. Some libraries prefer `&mut self -> &mut Self` for the same effect without moving the value; both forms chain identically at the call site.

Chaining carries real API-design cost. Each method must take ownership of `self` (or borrow it mutably); when setters depend on each other, call order becomes part of the public API contract; and adding new configuration later is harder than adding a field to a config struct. Reach for chaining when the fluent call site is a genuine readability win; otherwise a config struct with `..Default::default()` is usually simpler.

### Multiple `impl` blocks

Rust allows multiple `impl` blocks for the same type. This is sometimes used to organize related methods or to separate trait implementations from inherent methods:

```rust
// Rust
struct Rectangle {
    width: f64,
    height: f64,
}

impl Rectangle {
    fn area(&self) -> f64 {
        self.width * self.height
    }
}

impl Rectangle {
    fn perimeter(&self) -> f64 {
        2.0 * (self.width + self.height)
    }
}
```

Swift uses extensions for a similar purpose – splitting method definitions across multiple blocks. The difference is that in Rust, both inherent `impl` blocks and separate `impl` blocks are the same construct.

## Associated functions

Functions in an `impl` block that do not take `self` as their first parameter are called associated functions. They are called on the type itself, not on an instance – similar to `static` methods in Swift:

```swift
// Swift
struct Color {
    var r: UInt8
    var g: UInt8
    var b: UInt8

    static func red() -> Color {
        Color(r: 255, g: 0, b: 0)
    }
}

let red = Color.red()
```

```rust
// Rust
struct Color {
    r: u8,
    g: u8,
    b: u8,
}

impl Color {
    fn red() -> Color {
        Color { r: 255, g: 0, b: 0 }
    }
}
```

Note the syntax: Rust calls associated functions with `::` (double colon), while Swift uses `.` (dot). In Rust, `.` is reserved for method calls on instances; `::` is used for associated functions, module paths, and enum variants.

The most common associated function is `new`, which serves as a conventional constructor. Rust does not have a language-level `init` like Swift – `new` is just a naming convention:

```rust
// Rust
struct Player {
    name: String,
    score: u32,
}

impl Player {
    fn new(name: String) -> Player {
        Player { name, score: 0 }
    }
}
```

## Enums

Both languages support enums, and both go far beyond C-style enumerations. Swift and Rust enums can carry associated data, have methods, and be used in pattern matching. The terminology and syntax differ slightly.

### Simple enums

```swift
// Swift
enum Direction {
    case north
    case south
    case east
    case west
}
```

```rust
// Rust
enum Direction {
    North,
    South,
    East,
    West,
}

fn main() {
    let heading = Direction::North;
    match heading {
        Direction::North => println!("Going north"),
        Direction::South => println!("Going south"),
        Direction::East => println!("Going east"),
        Direction::West => println!("Going west"),
    }
}
```

Swift refers to values with `Direction.north` (or just `.north` when the type is known). Rust uses `Direction::North` (double colon, and variants are `PascalCase` by convention).

### Enum variants with data

Both languages support enums where each variant can carry different data. Swift calls this "associated values"; Rust calls them "tuple variants" and "struct variants."

**Tuple variants** (unnamed fields):

```swift
// Swift
enum Shape {
    case circle(radius: Double)
    case rectangle(width: Double, height: Double)
}
```

```rust
// Rust
enum Shape {
    Circle(f64),
    Rectangle(f64, f64),
}

fn area(shape: &Shape) -> f64 {
    match shape {
        Shape::Circle(radius) => std::f64::consts::PI * radius * radius,
        Shape::Rectangle(width, height) => width * height,
    }
}
```

**Struct variants** (named fields):

```rust
// Rust
enum Event {
    Click { x: i32, y: i32 },
    KeyPress { code: u32, shift: bool },
    Quit,
}

fn describe(event: &Event) -> String {
    match event {
        Event::Click { x, y } => format!("Click at ({x}, {y})"),
        Event::KeyPress { code, shift } => {
            format!("Key {code}, shift: {shift}")
        }
        Event::Quit => String::from("Quit"),
    }
}
```

Rust's struct variants are similar to Swift's associated values with labels, but the syntax mirrors struct definitions. A Rust enum can mix unit variants (no data), tuple variants (positional data), and struct variants (named data) in the same enum.

### Methods on enums

Both languages let you add methods to enums. In Rust, you use an `impl` block, just as with structs:

```swift
// Swift
enum Coin {
    case penny, nickel, dime, quarter

    func value() -> Int {
        switch self {
        case .penny: 1
        case .nickel: 5
        case .dime: 10
        case .quarter: 25
        }
    }
}
```

```rust
// Rust
enum Coin {
    Penny,
    Nickel,
    Dime,
    Quarter,
}

impl Coin {
    fn value(&self) -> u32 {
        match self {
            Coin::Penny => 1,
            Coin::Nickel => 5,
            Coin::Dime => 10,
            Coin::Quarter => 25,
        }
    }
}
```

## `Option<T>` and `Result<T, E>`

Two of the most important types in Rust's standard library are enums: `Option<T>` and `Result<T, E>`. `Option<T>` closely corresponds to Swift optionals. `Result<T, E>` plays a similar role to Swift's fallible functions, but Rust represents success or failure as an explicit enum rather than with `throws` syntax.

### `Option<T>`

Swift represents the absence of a value with optionals (`T?`), which is syntactic sugar for `Optional<T>`. Rust uses `Option<T>`, which is defined as:

```rust
// Rust (standard library definition)
enum Option<T> {
    Some(T),
    None,
}
```

Usage comparison:

```swift
// Swift
func find(name: String, in list: [String]) -> Int? {
    list.firstIndex(of: name)
}

let index = find(name: "Alice", in: ["Bob", "Alice", "Charlie"])
if let index {
    print("Found at \(index)")
}
```

```rust
// Rust
fn find(name: &str, list: &[&str]) -> Option<usize> {
    list.iter().position(|&item| item == name)
}

fn main() {
    let names = ["Bob", "Alice", "Charlie"];
    let index = find("Alice", &names);
    if let Some(i) = index {
        println!("Found at {i}");
    }
}
```

`Some` and `None` are so common in Rust that they are included in the prelude – you can use them without the `Option::` prefix.

### `Result<T, E>`

Swift usually marks a function that can fail with `throws`, while Rust usually returns `Result<T, E>` directly. Swift also has a standard library `Result<Success, Failure>` type, but idiomatic Swift APIs more often use `throws` for fallible functions. `Result<T, E>` is an enum:

```rust
// Rust (standard library definition)
enum Result<T, E> {
    Ok(T),
    Err(E),
}
```

Usage comparison:

```swift
// Swift
enum ParseError: Error {
    case invalidInput(String)
}

func parseAge(_ input: String) throws -> Int {
    guard let age = Int(input) else {
        throw ParseError.invalidInput(input)
    }
    return age
}
```

```rust
// Rust
use std::num::ParseIntError;

fn parse_age(input: &str) -> Result<i32, ParseIntError> {
    input.parse::<i32>()
}

fn main() {
    match parse_age("25") {
        Ok(age) => println!("Age: {age}"),
        Err(e) => println!("Error: {e}"),
    }
}
```

The key difference in philosophy: Swift hides the error handling mechanism behind `try`/`catch` syntax, making it look similar to exceptions (though it is not exception-based). Rust makes the `Result` type explicit in the function signature and requires the caller to handle it. Error handling is covered in depth in [Part V](../../error-handling/error-handling/).

## Visibility

By default, struct fields and enum variants have different visibility rules:

- **Struct fields** are private by default. Even if the struct is public, its fields are private unless explicitly marked `pub`.
- **Enum variants** inherit the visibility of the enum. If the enum is `pub`, all its variants are automatically public.

```rust
// Rust
pub struct User {
    pub name: String,     // public
    email: String,        // private – not accessible outside this module
}

pub enum Status {
    Active,     // public because Status is public
    Inactive,   // also public
}
```

In Swift, struct properties and enum cases follow the type's access level by default, and you can override individual members with access modifiers like `private` or `internal`.

## Key differences and gotchas

- **Separate `impl` blocks**: Rust separates data (struct/enum definition) from behavior (`impl` block). Swift defines methods inside the type body.
- **No automatic initializers**: Rust does not generate memberwise initializers. You either use struct literal syntax or write an associated function like `new`.
- **`self` must be explicit**: Rust methods must declare `self` as a parameter (`&self`, `&mut self`, or `self`). The choice between these forms affects ownership and borrowing.
- **`::` vs `.`**: Associated functions use `::` (`Color::red()`); methods use `.` (`circle.area()`). In Swift, both use `.`.
- **Enum variant casing**: Rust enum variants are `PascalCase` (`Direction::North`). Swift enum cases are `camelCase` (`Direction.north`).
- **Enum variant access**: Rust uses `EnumName::Variant`; Swift uses `EnumName.case` or shorthand `.case`.
- **No `init`**: Rust has no initializer syntax. The `new` convention is just an associated function.
- **Struct fields are private by default**: In Rust, marking a struct as `pub` does not make its fields public. Each field must be individually marked `pub`.
- **`Option` and `Result` are regular enums**: They are not language-level syntax. You interact with them through pattern matching, method calls, and combinators.

## Further reading

- [Structs](https://doc.rust-lang.org/book/ch05-00-structs.html): The Rust Programming Language
- [Enums and Pattern Matching](https://doc.rust-lang.org/book/ch06-00-enums.html): The Rust Programming Language
- [`Option` documentation](https://doc.rust-lang.org/std/option/enum.Option.html): Rust standard library
- [`Result` documentation](https://doc.rust-lang.org/std/result/enum.Result.html): Rust standard library
