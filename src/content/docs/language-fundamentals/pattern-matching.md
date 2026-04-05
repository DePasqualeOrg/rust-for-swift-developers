---
title: Pattern Matching
sidebar:
  order: 8
---

Pattern matching is one of the areas where Swift and Rust feel most alike. Both languages have exhaustive `switch`/`match` statements, support destructuring, and use pattern matching to unwrap optional values. The syntax and terminology differ, but the underlying ideas are remarkably similar.

## `match` expressions

Rust's `match` is the direct counterpart to Swift's `switch`. Both require exhaustive handling of all possible cases – the compiler will reject code that does not cover every variant.

```swift
// Swift
enum Direction {
    case north, south, east, west
}

let heading: Direction = .north
switch heading {
    case .north:
        print("Going north")
    case .south:
        print("Going south")
    case .east:
        print("Going east")
    case .west:
        print("Going west")
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

let heading = Direction::North;
match heading {
    Direction::North => println!("Going north"),
    Direction::South => println!("Going south"),
    Direction::East => println!("Going east"),
    Direction::West => println!("Going west"),
}
```

### Syntax differences

- **Arm separator**: Rust uses `=>` between the pattern and the body; Swift uses `:`.
- **Commas**: Rust arms are separated by commas (optional after a block `{}`). Swift arms are separated by newlines.
- **No fallthrough**: Both languages avoid fallthrough by default. In Swift, you can opt into it with `fallthrough`. Rust has no fallthrough at all – each arm is independent.
- **Blocks**: If a `match` arm needs multiple statements, wrap them in braces. Swift `case` blocks do not need braces.

```rust
// Rust
enum TrafficLight {
    Red,
    Yellow,
    Green,
}

let light = TrafficLight::Red;
match light {
    TrafficLight::Red => {
        println!("Stop");
        println!("Wait for green");
    }
    TrafficLight::Yellow => println!("Caution"),
    TrafficLight::Green => println!("Go"),
}
```

## `match` as an expression

Since Rust is expression-based, `match` produces a value. All arms must return the same type:

```rust
// Rust
enum Coin {
    Penny,
    Nickel,
    Dime,
    Quarter,
}

fn value_in_cents(coin: &Coin) -> u32 {
    match coin {
        Coin::Penny => 1,
        Coin::Nickel => 5,
        Coin::Dime => 10,
        Coin::Quarter => 25,
    }
}
```

Swift added `switch` as an expression in Swift 5.9, so this capability is available in both languages. However, Rust has had it since the beginning, and the idiom is deeply embedded in Rust code.

## Exhaustiveness

Both languages enforce exhaustive matching. If you add a new variant to an enum, the compiler will flag every `match`/`switch` that does not handle it. This is one of the strongest guarantees both languages provide.

When you cannot or do not want to enumerate every case, both languages offer a wildcard. Swift uses `default:`; Rust uses `_`:

```swift
// Swift
let value = 42
switch value {
    case 0:
        print("Zero")
    case 1:
        print("One")
    default:
        print("Something else")
}
```

```rust
// Rust
let value = 42;
match value {
    0 => println!("Zero"),
    1 => println!("One"),
    _ => println!("Something else"),
}
```

The `_` wildcard matches any value and does not create a binding. You can also use a named binding to capture the value:

```rust
// Rust
let value = 42;
match value {
    0 => println!("Zero"),
    1 => println!("One"),
    other => println!("Got {other}"),
}
```

## Matching on multiple patterns

Both languages allow matching on multiple values in a single arm. Swift uses commas; Rust uses the pipe `|` operator:

```swift
// Swift
let code = 404
switch code {
    case 200, 201:
        print("Success")
    case 400, 404:
        print("Client error")
    case 500:
        print("Server error")
    default:
        print("Unknown")
}
```

```rust
// Rust
let code = 404;
match code {
    200 | 201 => println!("Success"),
    400 | 404 => println!("Client error"),
    500 => println!("Server error"),
    _ => println!("Unknown"),
}
```

## Matching on ranges

Both languages support range patterns:

```swift
// Swift
let score = 85
switch score {
    case 90...100:
        print("A")
    case 80..<90:
        print("B")
    case 70..<80:
        print("C")
    default:
        print("Below C")
}
```

```rust
// Rust
let score = 85;
match score {
    90..=100 => println!("A"),
    80..90 => println!("B"),
    70..80 => println!("C"),
    _ => println!("Below C"),
}
```

The syntax mirrors the range operators covered in the previous chapter: Rust uses `..=` for inclusive ranges and `..` for exclusive ranges.

## Destructuring

Pattern matching becomes especially powerful when combined with destructuring – pulling apart compound values to extract their components.

### Destructuring tuples

```swift
// Swift
let point = (3, 7)
switch point {
    case (0, 0):
        print("Origin")
    case (let x, 0):
        print("On x-axis at \(x)")
    case (0, let y):
        print("On y-axis at \(y)")
    case (let x, let y):
        print("At (\(x), \(y))")
}
```

```rust
// Rust
let point = (3, 7);
match point {
    (0, 0) => println!("Origin"),
    (x, 0) => println!("On x-axis at {x}"),
    (0, y) => println!("On y-axis at {y}"),
    (x, y) => println!("At ({x}, {y})"),
}
```

In Rust, variable bindings in patterns do not need the `let` keyword – bare names like `x` and `y` automatically bind to the matched value. In Swift, you need `let` (or `var`) before each binding.

### Destructuring structs

```rust
// Rust
struct Point {
    x: i32,
    y: i32,
}

let p = Point { x: 5, y: -3 };

match p {
    Point { x: 0, y: 0 } => println!("Origin"),
    Point { x, y: 0 } => println!("On x-axis at {x}"),
    Point { x: 0, y } => println!("On y-axis at {y}"),
    Point { x, y } => println!("At ({x}, {y})"),
}
```

When the variable name matches the field name, you can use the shorthand `Point { x, y }` instead of `Point { x: x, y: y }`. You can also selectively destructure with `..` to ignore remaining fields:

```rust
// Rust
struct Config {
    width: u32,
    height: u32,
    fullscreen: bool,
    title: String,
}

let config = Config {
    width: 1920,
    height: 1080,
    fullscreen: true,
    title: String::from("My App"),
};

let Config { width, height, .. } = config;
println!("{width}x{height}");
```

Swift does not support destructuring structs in pattern matching. You would access fields individually after matching.

### Destructuring enums

Enum destructuring is where both languages truly shine, and where the syntax is most similar:

```swift
// Swift
enum Message {
    case text(String)
    case image(url: String, width: Int, height: Int)
    case quit
}

let msg: Message = .image(url: "photo.png", width: 800, height: 600)
switch msg {
    case .text(let content):
        print("Text: \(content)")
    case .image(let url, let width, let height):
        print("Image: \(url) (\(width)x\(height))")
    case .quit:
        print("Quit")
}
```

```rust
// Rust
enum Message {
    Text(String),
    Image { url: String, width: u32, height: u32 },
    Quit,
}

let msg = Message::Image {
    url: String::from("photo.png"),
    width: 800,
    height: 600,
};

match msg {
    Message::Text(content) => println!("Text: {content}"),
    Message::Image { url, width, height } => {
        println!("Image: {url} ({width}x{height})")
    }
    Message::Quit => println!("Quit"),
}
```

## `if let`

Both languages have `if let` for when you only care about one variant and want to ignore the rest. The syntax is very similar but with a subtle structural difference:

```swift
// Swift
let value: Int? = 42
if let value {
    print("Got \(value)")
}
```

```rust
// Rust
let value: Option<i32> = Some(42);
if let Some(v) = value {
    println!("Got {v}");
}
```

In Swift, the pattern is on the left and the value being matched is on the right of `=`. In Rust, the pattern is also on the left and the value on the right, but the pattern includes the enum variant (`Some(v)`) rather than just the binding name.

Swift 5.7 introduced the shorthand `if let value` (omitting `= value`), which is equivalent to `if let value = value`. Rust does not have this shorthand.

### `if let` with `else`

Both languages support an `else` branch:

```rust
// Rust
let value: Option<i32> = None;
if let Some(v) = value {
    println!("Got {v}");
} else {
    println!("No value");
}
```

### `if let` with enums beyond `Option`

`if let` works with any enum, not just `Option`:

```rust
// Rust
enum Command {
    Run { program: String },
    Stop,
    Pause,
}

let cmd = Command::Run {
    program: String::from("server"),
};

if let Command::Run { program } = cmd {
    println!("Running: {program}");
}
```

### Swift's `guard let` vs Rust

Swift has `guard let` for early exits:

```swift
// Swift
func process(value: Int?) {
    guard let value else {
        print("No value")
        return
    }
    print("Processing \(value)")
}
```

Rust does not have a `guard let` keyword, but you can achieve the same pattern with `if let` and an early return, or more idiomatically with `let-else` (stabilized in Rust 1.65):

```rust
// Rust
fn process(value: Option<i32>) {
    let Some(v) = value else {
        println!("No value");
        return;
    };
    println!("Processing {v}");
}

fn main() {
    process(Some(42));
    process(None);
}
```

The `let-else` syntax mirrors Swift's `guard let` almost exactly: bind the value or execute a diverging block (one that returns, breaks, continues, or panics).

## `while let`

Both languages support `while let` for looping as long as a pattern matches:

```swift
// Swift
var stack = [1, 2, 3]
while let top = stack.popLast() {
    print(top)
}
```

```rust
// Rust
let mut stack = vec![1, 2, 3];
while let Some(top) = stack.pop() {
    println!("{top}");
}
```

In Rust, `Vec::pop` returns `Option<T>`, so `while let Some(top)` keeps looping as long as there are elements.

## Nested patterns

Patterns can be nested to match complex structures:

```rust
// Rust
enum Expr {
    Num(f64),
    Add(Box<Expr>, Box<Expr>),
    Neg(Box<Expr>),
}

fn simplify(expr: &Expr) -> String {
    match expr {
        Expr::Num(n) => format!("{n}"),
        Expr::Add(left, right) => {
            format!("({} + {})", simplify(left), simplify(right))
        }
        Expr::Neg(inner) => match inner.as_ref() {
            Expr::Neg(double_neg) => simplify(double_neg),
            other => format!("-{}", simplify(other)),
        },
    }
}

let expr = Expr::Neg(Box::new(Expr::Neg(Box::new(Expr::Num(5.0)))));
simplify(&expr); // 5
```

You can also nest patterns directly without a second `match`:

```rust
// Rust
let values: (Option<i32>, Option<i32>) = (Some(1), Some(2));
match values {
    (Some(a), Some(b)) => println!("Both: {a} and {b}"),
    (Some(a), None) => println!("Only first: {a}"),
    (None, Some(b)) => println!("Only second: {b}"),
    (None, None) => println!("Neither"),
}
```

## Match guards

Both languages support adding conditions to pattern arms. Swift uses `where`; Rust uses `if`:

```swift
// Swift
let value = 15
switch value {
    case let x where x < 0:
        print("Negative")
    case let x where x > 10:
        print("Big: \(x)")
    default:
        print("Other")
}
```

```rust
// Rust
let value = 15;
match value {
    x if x < 0 => println!("Negative"),
    x if x > 10 => println!("Big: {x}"),
    _ => println!("Other"),
}
```

Match guards are especially useful with enums:

```rust
// Rust
enum Temperature {
    Celsius(f64),
    Fahrenheit(f64),
}

fn describe(temp: &Temperature) -> &str {
    match temp {
        Temperature::Celsius(c) if *c > 40.0 => "Extremely hot",
        Temperature::Celsius(c) if *c > 30.0 => "Hot",
        Temperature::Celsius(_) => "Moderate or cold",
        Temperature::Fahrenheit(f) if *f > 104.0 => "Extremely hot",
        Temperature::Fahrenheit(f) if *f > 86.0 => "Hot",
        Temperature::Fahrenheit(_) => "Moderate or cold",
    }
}
```

Note that match guards affect exhaustiveness checking. The compiler cannot always tell whether guards cover all cases, so you may still need a wildcard arm.

## `@` bindings

Sometimes you want to both test a value against a pattern and capture it in a variable. Rust uses `@` for this:

```rust
// Rust
fn classify_age(age: u32) -> &'static str {
    match age {
        0 => "newborn",
        infant @ 1..=2 => {
            println!("Infant age: {infant}");
            "infant"
        }
        3..=12 => "child",
        teen @ 13..=19 => {
            println!("Teen age: {teen}");
            "teenager"
        }
        _ => "adult",
    }
}
```

The `@` binding lets you name the matched value while simultaneously checking it against a pattern. This is useful when you need both the value and a structural constraint.

Swift achieves a similar effect using `where` clauses or `case let` patterns, but does not have a direct `@` equivalent:

```swift
// Swift
let age = 15
switch age {
    case 0:
        print("Newborn")
    case let infant where (1...2).contains(infant):
        print("Infant age: \(infant)")
    case 3...12:
        print("Child")
    case let teen where (13...19).contains(teen):
        print("Teen age: \(teen)")
    default:
        print("Adult")
}
```

`@` bindings also work with enum patterns:

```rust
// Rust
#[derive(Debug)]
enum Action {
    Move { x: i32, y: i32 },
    Write(String),
    Quit,
}

fn handle(action: &Action) {
    match action {
        m @ Action::Move { x, y } if *x == 0 && *y == 0 => {
            println!("No-op move: {m:?}");
        }
        Action::Move { x, y } => println!("Move to ({x}, {y})"),
        Action::Write(text) => println!("Write: {text}"),
        Action::Quit => println!("Quit"),
    }
}
```

To use `{m:?}` for debug printing, the enum needs `#[derive(Debug)]`.

## `matches!` macro

Rust provides a convenient `matches!` macro for checking whether a value matches a pattern without destructuring:

```rust
// Rust
enum Status {
    Active,
    Inactive,
    Suspended,
}

let s = Status::Active;

let is_available = matches!(s, Status::Active | Status::Inactive);
```

This is roughly equivalent to Swift's pattern matching with `if case` or checking membership, but more concise for simple pattern checks.

## Key differences and gotchas

- **`match` vs `switch`**: Rust uses `match`; Swift uses `switch`. Both require exhaustive handling.
- **Arm syntax**: Rust uses `pattern => expression`; Swift uses `case pattern:`.
- **No fallthrough in Rust**: Swift has an opt-in `fallthrough` keyword; Rust has no fallthrough at all.
- **No `let` in patterns**: Rust patterns create bindings without `let`. In Swift, you write `case let x`; in Rust, you just write `x`.
- **Multiple patterns**: Rust uses `|`; Swift uses `,`.
- **Match guards**: Rust uses `if` after the pattern; Swift uses `where`.
- **`@` bindings**: Rust has `@` for naming a value while matching it. Swift has no direct equivalent.
- **`let-else`**: Rust's `let-else` is the closest equivalent to Swift's `guard let`.
- **`match` is an expression**: It produces a value. All arms must return the same type.
- **`_` is a pattern, not `default`**: While `_` serves the same role as Swift's `default`, it is a general-purpose wildcard pattern that can also be used inside other patterns (e.g., `Some(_)` to ignore the inner value).

## Further reading

- [The `match` Control Flow Construct](https://doc.rust-lang.org/book/ch06-02-match.html): The Rust Programming Language
- [Concise Control Flow with `if let`](https://doc.rust-lang.org/book/ch06-03-if-let.html): The Rust Programming Language
- [Patterns and Matching](https://doc.rust-lang.org/book/ch19-00-patterns.html): The Rust Programming Language
- [`matches!` macro](https://doc.rust-lang.org/std/macro.matches.html): Rust standard library documentation
