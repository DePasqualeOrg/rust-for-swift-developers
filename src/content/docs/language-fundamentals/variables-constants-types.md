---
title: Variables, Constants, and Types
sidebar:
  order: 5
---

Swift and Rust both use `let` to declare values – but the keyword means something different in each language. In Swift, `let` creates an immutable binding and `var` creates a mutable one. In Rust, `let` creates an immutable binding too, but you opt into mutability with `let mut` rather than a separate keyword.

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

## Scalar types

### Integers

Swift has a default integer type, `Int`, which is platform-sized (64 bits on modern Apple hardware). You can also use explicit sizes like `Int8`, `Int16`, `Int32`, `Int64`, and their unsigned counterparts `UInt8` through `UInt64`.

Rust has no default integer type in the same sense. Instead, you choose an explicit size whenever you annotate a type. The naming convention is shorter: `i8`, `i16`, `i32`, `i64`, `i128` for signed integers, and `u8`, `u16`, `u32`, `u64`, `u128` for unsigned. Rust also provides `isize` and `usize`, which match the width of a pointer on the target platform – 64 bits on 64-bit systems, 32 bits on 32-bit systems. These are the Rust equivalents of Swift's `Int` and `UInt`.

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

Rust also has 128-bit integers (`i128`/`u128`), which Swift does not offer natively.

### Integer overflow

Swift traps on integer overflow by default in both debug and optimized builds unless you explicitly opt into wrapping with operators like `&+`, `&-`, and `&*`. Rust makes a different tradeoff: integer overflow checks panic in debug builds and wrap in release builds. For explicit wrapping, Rust provides `wrapping_add`, `wrapping_sub`, and related methods, as well as the `Wrapping<T>` type:

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

Rust has a `char` type that represents a single Unicode scalar value. Swift's nearest counterpart is `Character`, which represents an extended grapheme cluster. In Swift, character literals use double quotes. In Rust, character literals use single quotes – double quotes are for string slices.

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

Note that shadowing creates a new binding – it does not mutate the original. The old value is simply no longer accessible by that name (and will be dropped if nothing else references it).

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

- **Mutability keyword**: Swift uses `var` for mutable bindings; Rust uses `let mut`. Rust's `let` alone is immutable.
- **Default integer type**: Swift defaults to `Int` (pointer-sized); Rust defaults to `i32` (32-bit).
- **Integer sizes**: Rust names are shorter (`i32` vs `Int32`) and include 128-bit types.
- **Shadowing**: Rust allows redeclaring a variable in the same scope with `let`, even changing its type. Swift only allows shadowing across different scopes.
- **String literals**: In Swift, a string literal produces a `String`. In Rust, a string literal produces a `&str` (a borrowed reference). This is covered in detail in the [Strings](../strings/) chapter.
- **Character literals**: Rust uses single quotes for `char` and double quotes for strings. Swift uses double quotes for both.
- **Named tuple fields**: Swift supports them; Rust does not. Use a struct in Rust when you need named fields.
- **No implicit conversions**: Neither language performs implicit numeric conversions. You must explicitly cast with `as` in Rust or initializers in Swift. Rust uses `value as f64`; Swift uses `Double(value)`.

## Further reading

- [Variables and Mutability](https://doc.rust-lang.org/book/ch03-01-variables-and-mutability.html): The Rust Programming Language
- [Data Types](https://doc.rust-lang.org/book/ch03-02-data-types.html): The Rust Programming Language
- [Primitive Types](https://doc.rust-lang.org/std/index.html#primitives): Rust standard library documentation
