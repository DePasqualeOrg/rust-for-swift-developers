---
title: Variables, Constants, and Types
sidebar:
  order: 5
---

Swift and Rust both use `let` to declare immutable bindings. Swift uses `var` for mutable bindings; Rust uses `let mut`.

## Immutable and mutable bindings

In Swift, you choose between `let` and `var`:

```swift
// Swift
let name = "Alice"   // immutable
var age = 30         // mutable
age = 31
```

In Rust, all bindings are immutable by default. You add `mut` when you need to reassign:

```rust
// Rust
let name = "Alice";   // immutable
let mut age = 30;     // mutable
age = 31;
```

Attempting to reassign an immutable binding is a compile-time error in both languages. The difference is purely syntactic: Swift uses two keywords (`let`/`var`), while Rust uses one keyword with an optional modifier (`let`/`let mut`).

Rust's design makes immutability the path of least resistance. You have to consciously decide to make a binding mutable, which encourages a style where most values never change.

## Constants and static storage

An immutable `let` binding can receive a value computed at runtime. Rust’s `const` has a different purpose: it names a value whose initializer must be evaluated at compile time. It requires a type annotation and conventionally uses `SCREAMING_SNAKE_CASE`.

```rust
const HEADER_BYTES: usize = 16;
const PAYLOAD_BYTES: usize = 64;
const PACKET_BYTES: usize = HEADER_BYTES + PAYLOAD_BYTES;

fn main() {
    let packet = [0_u8; PACKET_BYTES];
    let argument_count = std::env::args().count();
    assert_eq!(packet.len(), 80);
    println!("Started with {argument_count} arguments");
}
```

The array length needs a compile-time value. `argument_count` is immutable after initialization but depends on the process’s arguments. Swift’s `let` also means an immutable binding; it does not by itself require a compile-time initializer.

A `const` names a value, not one shared storage location. Separate uses need not have the same address. Use a `static` when the program needs a shared allocation with a lifetime covering the entire execution:

```rust
static MAGIC: [u8; 4] = *b"RUST";

fn main() {
    let first = &MAGIC;
    let second = &MAGIC;
    assert!(std::ptr::eq(first, second));
    assert_eq!(first, b"RUST");
}
```

A static initializer is also a constant expression. Its value is not dropped when the program exits. Shared statics must have a thread-safe type (`Sync`); later chapters explain this trait and synchronized mutation. Avoid `static mut` for ordinary application state. Use a mutex or atomic when mutation is required, rather than taking responsibility for global aliasing and synchronization yourself.

### `const fn`: usable during constant evaluation

Mark a function `const fn` when it should be callable in a constant expression. Its body must use operations permitted during constant evaluation. The same function can also be called with runtime inputs:

```rust
const fn packet_bytes(payload: usize) -> usize {
    16 + payload
}

const DEFAULT_BYTES: usize = packet_bytes(64);

fn main() {
    let payload = std::env::args()
        .nth(1)
        .and_then(|text| text.parse::<u16>().ok())
        .unwrap_or(64);
    let actual_bytes = packet_bytes(usize::from(payload));
    assert_eq!(DEFAULT_BYTES, 80);
    println!("Packet size: {actual_bytes}");
}
```

`const fn` permits compile-time evaluation; it does not force every call to happen at compile time. The compiler can optimize ordinary function calls too, but optimization is separate from whether an expression is legal in a `const` initializer.

### Runtime initialization of shared data

Some shared values need allocation or other work unavailable in a constant expression. `LazyLock` performs its initialization on first access, with synchronization for concurrent callers:

```rust
use std::sync::LazyLock;

static LABEL: LazyLock<String> = LazyLock::new(|| {
    println!("Initializing label");
    String::from("Rust for Swift Developers")
});

fn main() {
    assert_eq!(LABEL.as_str(), "Rust for Swift Developers");
    assert_eq!(LABEL.as_str(), "Rust for Swift Developers");
    // "Initializing label" prints once.
}
```

Swift’s stored type properties such as `static let label = makeLabel()` also initialize lazily. Rust makes the lazy storage explicit in the type. Use `OnceLock` instead when another part of the program supplies the value later; its `set` operation succeeds only once. These containers are useful when shared state is necessary, but passing an owned configuration value is often simpler.

| Declaration | Purpose | Initialization |
|---|---|---|
| `let value = compute();` | A local binding that cannot be reassigned | May run at runtime |
| `const VALUE: T = expression;` | A named compile-time value | Constant expression |
| `static VALUE: T = expression;` | One shared allocation | Constant expression |
| `static VALUE: LazyLock<T> = LazyLock::new(...);` | Shared data initialized on demand | The closure runs on first access |

See the Rust Reference for [constants](https://doc.rust-lang.org/reference/items/constant-items.html), [statics](https://doc.rust-lang.org/reference/items/static-items.html), and [constant evaluation](https://doc.rust-lang.org/reference/const_eval.html).

## Scalar types

### Integers

Swift has a default integer type, `Int`, which is platform-sized (64 bits on modern Apple hardware). You can also use explicit sizes like `Int8`, `Int16`, `Int32`, `Int64`, and their unsigned counterparts `UInt8` through `UInt64`.

Rust’s explicit integer types encode width and signedness: `i8`, `i16`, `i32`, `i64`, `i128`, and their unsigned `u` counterparts. An unconstrained integer literal falls back to `i32`. `isize` and `usize` have the target’s pointer width, making them closer to Swift’s `Int` and `UInt`.

```swift
// Swift
let count: Int = 42
let byte: UInt8 = 255
let big: Int64 = 1_000_000
```

```rust
// Rust
let count: i32 = 42;
let byte: u8 = 255;
let big: i64 = 1_000_000;
```

When you write an integer literal without a type annotation, Rust infers `i32` by default – not a pointer-sized type. This is a common surprise for Swift developers who expect the default to be platform-sized.

| Swift     | Rust    | Size           |
|-----------|---------|----------------|
| `Int8`    | `i8`    | 8-bit signed   |
| `Int16`   | `i16`   | 16-bit signed  |
| `Int32`   | `i32`   | 32-bit signed  |
| `Int64`   | `i64`   | 64-bit signed  |
| `Int`     | `isize` | Pointer-sized  |
| `UInt8`   | `u8`    | 8-bit unsigned |
| `UInt16`  | `u16`   | 16-bit unsigned|
| `UInt32`  | `u32`   | 32-bit unsigned|
| `UInt64`  | `u64`   | 64-bit unsigned|
| `UInt`    | `usize` | Pointer-sized  |

Rust's `i128` and `u128` correspond to Swift's `Int128` and `UInt128`, introduced in Swift 6.

### Integer overflow

Swift traps on integer overflow by default in both debug and optimized builds unless you explicitly opt into wrapping with operators like `&+`, `&-`, and `&*`. For ordinary Rust addition, subtraction, and multiplication, Cargo’s default debug profile checks overflow and its release profile wraps. The `overflow-checks` profile setting can change that behavior; it is separate from the numeric-cast rules below. For explicit wrapping, Rust provides `wrapping_add`, `wrapping_sub`, and related methods, as well as the `Wrapping<T>` type:

```rust
// Rust
let x: u8 = 255;
let y = x.wrapping_add(1); // 0, no panic
```

### Floating-point numbers

Both languages have 32-bit and 64-bit floating-point types. Swift uses `Float` (32-bit) and `Double` (64-bit), with `Double` being the default for float literals. Rust uses `f32` and `f64`, with `f64` as the default.

```swift
// Swift
let pi: Double = 3.14159
let approx: Float = 3.14
```

```rust
// Rust
let pi: f64 = 3.14159;
let approx: f32 = 3.14;
```

### Booleans

Both languages have a boolean type. Swift calls it `Bool`; Rust calls it `bool` (lowercase, following Rust's convention for primitive types).

```swift
// Swift
let isReady: Bool = true
```

```rust
// Rust
let is_ready: bool = true;
```

### Characters

Rust’s `char` represents a Unicode scalar value, corresponding to Swift’s `Unicode.Scalar`. Swift’s usual `Character` instead represents an extended grapheme cluster. In Swift, character literals use double quotes. In Rust, character literals use single quotes – double quotes are for string slices.

```swift
// Swift
let letter: Character = "A"
let emoji: Character = "🦀"
```

```rust
// Rust
let letter: char = 'A';
let emoji: char = '🦀';
```

Rust's `char` is always 4 bytes and represents a Unicode scalar value (U+0000 to U+D7FF and U+E000 to U+10FFFF). Swift's `Character` represents an extended grapheme cluster, which can contain multiple Unicode scalars. This means a Swift `Character` like "👨‍👩‍👧" (a family emoji composed of multiple scalars joined by zero-width joiners) is a single character, while Rust would need a `&str` or `String` to represent it.

## Converting between types

Rust does not implicitly widen one numeric type to another. The conversion you choose tells readers whether information can be lost and how failure is handled.

### `From` and `Into`: infallible conversions

Use `From` when a conversion is defined for every value of the source type:

```rust
fn main() {
    let small: u8 = 200;
    let wide = u32::from(small);
    let also_wide: u32 = small.into();
    assert_eq!(wide, 200);
    assert_eq!(wide, also_wide);

    let name = String::from("Ada");
    let another_name: String = "Ada".into();
    assert_eq!(name, another_name);
}
```

`From<Source>` is implemented on the destination type. That implementation also provides `Into<Destination>` for the source, so these are two spellings of the same conversion. `Destination::from(value)` makes the destination explicit; `.into()` needs enough type context to infer it. When defining your own conversion, normally implement `From` rather than `Into` directly. A `From` implementation should not fail or silently discard meaningful information.

### `TryFrom` and `TryInto`: conversions that can fail

Narrowing an integer can exceed the destination’s range. `TryFrom` returns a `Result` so the caller can handle that case:

```rust
fn main() {
    let accepted = u8::try_from(200_u16);
    let rejected = u8::try_from(300_u16);
    assert_eq!(accepted, Ok(200));
    assert!(rejected.is_err());

    let converted: Result<u8, _> = 300_u16.try_into();
    assert!(converted.is_err());
}
```

`TryInto` is the corresponding method form, provided by a `TryFrom` implementation. You can match the result, supply a fallback, or propagate the error with `?` as shown in the [error-handling chapter](../../error-handling/error-handling/). Swift’s `UInt8(exactly: value)` serves a similar purpose but returns an optional; `UInt8(value)` instead traps if the integer is out of range.

### Numeric `as` casts: know what is discarded

`as` is not shorthand for a checked conversion. Narrowing an integer truncates its high bits, and changing signedness can reinterpret the retained bits. These casts do not panic merely because the value is out of range, in either debug or release builds:

```rust
fn main() {
    let too_large = 300_u16;
    let negative = -1_i16;
    assert_eq!(too_large as u8, 44);
    assert_eq!(negative as u8, 255);

    assert_eq!(3.9_f64 as i32, 3);
    assert_eq!(f64::INFINITY as i32, i32::MAX);
    assert_eq!(f64::NEG_INFINITY as i32, i32::MIN);
    assert_eq!(f64::NAN as i32, 0);
}
```

A float-to-integer cast truncates toward zero and saturates at the destination’s limits; NaN converts to zero. Integer-to-float and narrowing float conversions can round. Swift’s ordinary floating-point-to-integer initializer also truncates, but traps for NaN or an unrepresentable result. Swift’s `truncatingIfNeeded:` integer initializer is closer to Rust’s truncating integer cast.

Clippy warns about the explicit NaN cast in this example. The assertion demonstrates its defined result; an application should reject NaN if zero would hide invalid input.

Not every pair of numeric types has a `From` or `TryFrom` implementation. In particular, `TryFrom` does not provide a general checked float-to-integer conversion. Decide whether your API should reject fractional values, round them, or clamp them, then implement that policy explicitly. For input lengths, indices, and other range-sensitive integer values, prefer `try_from` over a potentially lossy `as`.

The [conversion traits](https://doc.rust-lang.org/std/convert/) describe API-level conversions; the [numeric cast rules](https://doc.rust-lang.org/reference/expressions/operator-expr.html#numeric-cast) specify `as` behavior. String parsing is separate: use `"42".parse::<u32>()`, which can fail on invalid text.

## Type inference

Both languages have strong type inference. In most cases, you can omit the type annotation and the compiler will figure it out:

```swift
// Swift
let name = "Alice"       // String
let count = 42           // Int
let ratio = 3.14         // Double
let flag = true          // Bool
```

```rust
// Rust
let name = "Alice";      // &str (string slice, not String)
let count = 42;          // i32 (not isize)
let ratio = 3.14;        // f64
let flag = true;         // bool
```

Two differences to note: First, Rust infers string literals as `&str` (a borrowed string slice), not `String`. This distinction matters and is covered in the [Strings](../strings/) chapter. Second, as mentioned earlier, integer literals default to `i32`, not a pointer-sized integer.

Rust's type inference is also context-sensitive. It can infer types based on how a value is used later in the function:

```rust
// Rust
let mut numbers = Vec::new(); // type not yet known
numbers.push(5_u64);          // now inferred as Vec<u64>
```

Swift does the same when it can, but Rust's inference is particularly effective with generic collections and iterators.

## Type annotations

When inference is not sufficient or when you want to be explicit, both languages let you annotate types.

```swift
// Swift
let count: Int = 42
let name: String = "Alice"
```

```rust
// Rust
let count: i32 = 42;
let name: String = String::from("Alice");
```

For numeric literals in Rust, you can also use a type suffix instead of an annotation:

```rust
// Rust
let count = 42_i64;
let size = 1024_usize;
```

Swift does not have type suffixes for literals.

## Shadowing

This is one of the larger behavioral differences between the two languages. Rust allows you to redeclare a variable with the same name in the same scope – this is called shadowing. The new binding replaces the old one:

```rust
// Rust
let x = 5;
let x = x + 1;       // shadows the first x
let x = x * 2;       // x is now 12
```

Swift does not allow shadowing in the same scope. This code would be a compiler error:

```swift
// Swift
let x = 5
let x = x + 1 // error: invalid redeclaration of 'x'
```

Swift does allow shadowing across scopes (e.g., a local variable can shadow a parameter, and an inner scope can shadow an outer one), but Rust allows it within the same scope too.

Shadowing also lets you change the type of a binding, which is useful when a value goes through a transformation and the original is no longer needed. By reusing the name, you ensure the old value can no longer be accessed by mistake:

```rust
// Rust
let input = "42";
let input: i32 = input.parse().expect("not a number");
```

Here, `input` starts as a `&str` and is shadowed by a new binding of type `i32`. In Swift, you would need a different variable name since you cannot redeclare the same name or change its type.

Shadowing creates a new binding; it does not mutate or immediately drop the original value. If the old value was not moved, it is normally dropped at the end of its scope even though its name now refers to the new binding.

## Tuples

Both languages support tuples – anonymous groupings of values. The syntax is nearly identical:

```swift
// Swift
let point: (Int, Int) = (10, 20)
let x = point.0
let y = point.1
```

```rust
// Rust
let point: (i32, i32) = (10, 20);
let x = point.0;
let y = point.1;
```

Both languages support destructuring tuples:

```swift
// Swift
let (x, y) = (10, 20)
```

```rust
// Rust
let (x, y) = (10, 20);
```

Tuples can contain mixed types in both languages:

```rust
// Rust
let record: (i32, f64, bool) = (42, 3.14, true);
let (id, score, active) = record;
```

One difference: Swift supports named tuple elements (`let point: (x: Int, y: Int) = (x: 10, y: 20)`), while Rust does not. If you need named fields in Rust, use a struct.

## The unit type

Rust has a type called the unit type, written `()`. It is a tuple with zero elements, and it represents the absence of a meaningful value. Functions that do not return anything implicitly return `()`.

```rust
// Rust
fn greet(name: &str) {
    println!("Hello, {name}!");
    // implicitly returns ()
}

fn greet_explicit(name: &str) -> () {
    println!("Hello, {name}!");
}

fn main() {
    greet("Alice");
    greet_explicit("Bob");
}
```

In Swift, the equivalent is `Void`, which is actually a type alias for the empty tuple `()`:

```swift
// Swift
func greet(name: String) {
    print("Hello, \(name)!")
    // implicitly returns Void
}

func greetExplicit(name: String) -> Void {
    print("Hello, \(name)!")
}
```

The parallel is exact: both languages use the empty tuple as their "nothing" return type, and both let you omit it from function signatures.

## Type aliases

Both languages let you create new names for existing types:

```swift
// Swift
typealias UserID = Int
typealias Coordinate = (Double, Double)

let id: UserID = 42
let location: Coordinate = (37.7749, -122.4194)
```

```rust
// Rust
type UserId = i32;
type Coordinate = (f64, f64);

let id: UserId = 42;
let location: Coordinate = (37.7749, -122.4194);
```

Swift uses `typealias`; Rust uses `type`. In both languages, a type alias does not create a new distinct type – it is just an alternative name for the same type. Values of the alias type and the original type are interchangeable.

## Key differences and gotchas

- **Constants are not immutable locals**: `const` requires a compile-time initializer; `let` can receive a runtime value. `static` supplies shared storage, and `LazyLock` allows deferred runtime initialization.
- **Mutability keyword**: Swift uses `var` for mutable bindings; Rust uses `let mut`. Rust's `let` alone is immutable.
- **Default integer type**: Swift defaults to `Int` (pointer-sized); Rust defaults to `i32` (32-bit).
- **Integer sizes**: Rust names are shorter (`i32` vs `Int32`) and include 128-bit types.
- **Shadowing**: Rust allows redeclaring a variable in the same scope with `let`, even changing its type. Swift only allows shadowing across different scopes.
- **String literals**: In Swift, a string literal produces a `String`. In Rust, a string literal produces a `&str` (a borrowed reference). This is covered in detail in the [Strings](../strings/) chapter.
- **Character literals**: Rust uses single quotes for `char` and double quotes for strings. Swift uses double quotes for both.
- **Named tuple fields**: Swift supports them; Rust does not. Use a struct in Rust when you need named fields.
- **Conversion policy**: use `From`/`Into` for infallible conversions and `TryFrom`/`TryInto` for supported fallible conversions. Numeric `as` casts can discard information without reporting an error.

## Further reading

- [Variables and Mutability](https://doc.rust-lang.org/book/ch03-01-variables-and-mutability.html): The Rust Programming Language
- [Data Types](https://doc.rust-lang.org/book/ch03-02-data-types.html): The Rust Programming Language
- [Primitive Types](https://doc.rust-lang.org/std/index.html#primitives): Rust standard library documentation
