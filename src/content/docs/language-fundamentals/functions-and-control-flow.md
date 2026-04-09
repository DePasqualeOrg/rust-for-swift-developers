---
title: Functions and Control Flow
sidebar:
  order: 6
---

Rust and Swift take a similar approach to control flow, with pattern matching, expression-based constructs, and an emphasis on exhaustiveness. But Rust takes the "everything is an expression" philosophy further than Swift does.

## Function syntax

The structure of a function declaration is similar in both languages. Swift uses `func`; Rust uses `fn`. Both place parameters in parentheses and use `->` to denote the return type.

```swift
// Swift
func add(a: Int, b: Int) -> Int {
    return a + b
}

let sum = add(a: 5, b: 3)
```

```rust
// Rust
fn add(a: i32, b: i32) -> i32 {
    a + b
}

let sum = add(5, 3);
```

You'll notice two differences:

- **No argument labels**: Rust does not have Swift's argument label system. In Swift, you call `add(a: 5, b: 3)`. In Rust, you call `add(5, 3)`. There is no concept of external parameter names.
- **No `return` needed for the last expression**: The last expression in a Rust function body is its return value, without a `return` keyword and without a semicolon. Adding a semicolon turns the expression into a statement that returns `()`.

### Functions with no return value

When a function does not return a meaningful value, Swift uses `Void` (or omits the return type), and Rust implicitly returns `()`:

```swift
// Swift
func greet(name: String) {
    print("Hello, \(name)!")
}
```

```rust
// Rust
fn greet(name: &str) {
    println!("Hello, {name}!");
}
```

In both cases, omitting the return type means the function returns the unit type.

## Expression-based language

Rust is an expression-based language, meaning that most constructs produce a value. In Swift, `if`/`else` became usable as expressions for assignments in Swift 5.9, but Rust has been expression-based from the start. This distinction affects how you write everything from simple conditionals to complex blocks.

### Blocks as expressions

In Rust, a block `{ ... }` evaluates to the value of its last expression (without a semicolon). This means you can use a block anywhere you need a value:

```rust
// Rust
let description = {
    let x = 5;
    let y = 10;
    if x + y > 10 {
        "big"
    } else {
        "small"
    }
};
```

In Swift, you would typically compute this with a separate variable or an immediately-invoked closure:

```swift
// Swift
let description: String = {
    let x = 5
    let y = 10
    if x + y > 10 {
        return "big"
    } else {
        return "small"
    }
}()
```

Or, since Swift 5.9, using `if`/`else` as an expression:

```swift
// Swift (5.9+)
let x = 5
let y = 10
let description = if x + y > 10 {
    "big"
} else {
    "small"
}
```

## Conditionals

### `if` / `else`

The basic `if`/`else` syntax is similar. Rust conditions do not use parentheses – they are optional and conventionally omitted. The braces, however, are always required (even for single-line bodies):

```swift
// Swift
let temperature = 35
if temperature > 30 {
    print("Hot")
} else if temperature > 20 {
    print("Warm")
} else {
    print("Cool")
}
```

```rust
// Rust
let temperature = 35;
if temperature > 30 {
    println!("Hot");
} else if temperature > 20 {
    println!("Warm");
} else {
    println!("Cool");
}
```

### `if` as an expression

In Rust, `if`/`else` is always an expression and can be used to produce a value. Both branches must return the same type:

```rust
// Rust
let temperature = 35;
let label = if temperature > 30 {
    "hot"
} else {
    "not hot"
};
```

Swift added this capability in 5.9, but it is limited to certain contexts such as assignments, return statements, and variable declarations. In Rust, you can use `if` expressions anywhere – as function arguments, inside other expressions, and in return position.

### No ternary operator

Rust does not have a ternary operator (`? :`). Since `if`/`else` is already an expression, the ternary operator would be redundant:

```swift
// Swift
let label = temperature > 30 ? "hot" : "cool"
```

```rust
// Rust
let temperature = 35;
let label = if temperature > 30 { "hot" } else { "cool" };
```

### Conditions must be `bool`

Unlike C, but like Swift, Rust requires conditions to be explicitly `bool`. You cannot use an integer or pointer as a condition:

```rust
// Rust – this does not compile
// fn main() {
//     let count = 1;
//     if count { // error: expected `bool`, found integer
//         println!("truthy");
//     }
// }
```

## Loops

Rust has three loop constructs: `loop`, `while`, and `for`. Swift has `while`, `for-in`, and `repeat-while`. The mapping is not one-to-one.

### `loop`: infinite loops

Rust has a dedicated `loop` keyword for infinite loops. Swift uses `while true` for the same purpose:

```swift
// Swift
while true {
    // runs forever
    break
}
```

```rust
// Rust
loop {
    // runs forever
    break;
}
```

Using `loop` instead of `while true` is not just convention – it gives the compiler useful information. The compiler knows a `loop` never terminates naturally, which enables better type checking and control-flow analysis.

### `loop` as an expression

Since Rust is expression-based, `loop` can return a value via `break`:

```rust
// Rust
let mut counter = 0;
let result = loop { // 20
    counter += 1;
    if counter == 10 {
        break counter * 2;
    }
};
```

Swift has no equivalent – you cannot return a value from a `while` or `repeat-while` loop.

### `while` loops

`while` loops work the same way in both languages:

```swift
// Swift
var n = 5
while n > 0 {
    print(n)
    n -= 1
}
```

```rust
// Rust
let mut n = 5;
while n > 0 {
    println!("{n}");
    n -= 1;
}
```

Swift's `repeat-while` (do-while in other languages) does not have a direct Rust equivalent. You can achieve the same behavior with `loop` and a conditional `break` at the end of the body:

```swift
// Swift
var input = fetchInput()
repeat {
    process(input)
    input = fetchInput()
} while input != "quit"
```

```rust
// Rust
let mut input = fetch_input();
loop {
    process(input);
    input = fetch_input();
    if input == "quit" {
        break;
    }
}
```

### `for` loops and ranges

Both languages use `for-in` syntax for iterating over sequences, but the range syntax differs:

```swift
// Swift
for i in 0..<5 {
    print(i)      // 0, 1, 2, 3, 4
}

for i in 0...5 {
    print(i)      // 0, 1, 2, 3, 4, 5
}
```

```rust
// Rust
for i in 0..5 {
    println!("{i}");  // 0, 1, 2, 3, 4
}

for i in 0..=5 {
    println!("{i}");  // 0, 1, 2, 3, 4, 5
}
```

| Swift   | Rust    | Meaning                   |
|---------|---------|---------------------------|
| `0..<5` | `0..5`  | Half-open (excludes end)  |
| `0...5` | `0..=5` | Closed (includes end)     |

Rust's `for` loop works with anything that implements the `IntoIterator` trait – arrays, vectors, ranges, and custom types. This is similar to how Swift's `for-in` works with anything conforming to `Sequence`.

```rust
// Rust
let names = ["Alice", "Bob", "Charlie"];
for name in names {
    println!("Hello, {name}!");
}
```

### Loop labels

Rust supports labeling loops, which is useful for breaking out of nested loops. Swift has a similar feature:

```swift
// Swift
outer: for i in 0..<5 {
    for j in 0..<5 {
        if i + j == 6 {
            break outer
        }
    }
}
```

```rust
// Rust
'outer: for i in 0..5 {
    for j in 0..5 {
        if i + j == 6 {
            break 'outer;
        }
    }
}
```

Rust labels start with a single quote (`'outer`), while Swift labels use a bare identifier followed by a colon (`outer:`).

## Early returns

Both languages use `return` for early exits from functions:

```rust
// Rust
fn classify(n: i32) -> &'static str {
    if n < 0 {
        return "negative";
    }
    if n == 0 {
        return "zero";
    }
    "positive" // last expression, no return needed
}
```

The convention in Rust is to use `return` only for early exits. When the last expression in a function is the return value, you omit both `return` and the semicolon. Adding an explicit `return` and semicolon on the last expression works but is not idiomatic.

### The semicolon trap

One of the most common mistakes for newcomers is accidentally adding a semicolon to the last expression:

```rust
// Rust – this does not compile
// fn double(x: i32) -> i32 {
//     x * 2;  // semicolon turns this into a statement returning ()
// }
```

The semicolon converts the expression `x * 2` into a statement, so the function body returns `()` instead of `i32`. The compiler will report a type mismatch. Remove the semicolon to fix it:

```rust
// Rust
fn double(x: i32) -> i32 {
    x * 2
}
```

## Diverging functions

Rust has a special return type `!` (pronounced "never") for functions that never return. These are called diverging functions:

```rust
// Rust
fn forever() -> ! {
    loop {
        // this function never returns
    }
}
```

Common uses include functions that always panic, run an infinite event loop, or call `std::process::exit`. The `!` type is useful because it can coerce to any other type, which allows you to use a diverging call in contexts that expect a specific type:

```rust
// Rust
fn get_value(opt: Option<i32>) -> i32 {
    match opt {
        Some(v) => v,
        None => panic!("no value"), // panic! returns !, which coerces to i32
    }
}
```

Swift has a similar concept with the `Never` type (used as the return type of `fatalError`, `preconditionFailure`, and similar functions), but you rarely write `-> Never` in your own Swift code. In Rust, `-> !` appears more frequently because the type system uses it for type coercion in match arms and other contexts.

## Key differences and gotchas

- **No argument labels**: Rust functions do not have external parameter names. All calls are positional.
- **Semicolons matter**: Omitting the semicolon on the last expression makes it the return value. Adding a semicolon makes it a statement that returns `()`.
- **Braces are always required**: Even single-line `if` bodies need braces in Rust.
- **No ternary operator**: Use `if`/`else` as an expression instead.
- **`loop` vs `while true`**: Prefer `loop` for infinite loops in Rust – it is not just convention, it helps the compiler.
- **Range syntax differs**: `0..<5` in Swift is `0..5` in Rust. `0...5` in Swift is `0..=5` in Rust.
- **Loop labels**: Rust uses `'label` (with a single quote prefix); Swift uses `label:`.
- **`return` convention**: Use `return` only for early exits. The last expression in a block is its value.
- **No `repeat-while`**: Rust does not have a do-while construct. Use `loop` with a conditional `break`.

## Further reading

- [Functions](https://doc.rust-lang.org/book/ch03-03-how-functions-work.html): The Rust Programming Language
- [Control Flow](https://doc.rust-lang.org/book/ch03-05-control-flow.html): The Rust Programming Language
- [Expressions](https://doc.rust-lang.org/reference/expressions.html): The Rust Reference
- [The never type](https://doc.rust-lang.org/std/primitive.never.html): Rust standard library documentation
