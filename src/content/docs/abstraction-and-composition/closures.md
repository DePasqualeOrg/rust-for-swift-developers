---
title: Closures
sidebar:
  order: 18
---

Closures – anonymous functions that capture values from their surrounding scope – are fundamental to both Swift and Rust. You use them for callbacks, iterator adapters, event handlers, and any situation where you need to pass behavior as a value. The basic concept is the same, but Rust closures interact with the ownership system in ways that require more explicit thinking about how captured values are used.

## Closure syntax

Swift closures use braces with parameter names before the `in` keyword:

```swift
// Swift
let add = { (a: Int, b: Int) -> Int in
    a + b
}
print(add(2, 3)) // 5
```

Rust closures use pipes (`|`) to delimit the parameters:

```rust
// Rust
let add = |a: i32, b: i32| -> i32 {
    a + b
};
add(2, 3) // 5
```

For single-expression closures, Rust lets you omit the braces and the return type:

```rust
// Rust
let add = |a: i32, b: i32| a + b;
add(2, 3) // 5
```

Swift has a similar shorthand with implicit returns and shorthand argument names (`$0`, `$1`):

```swift
// Swift
let add: (Int, Int) -> Int = { $0 + $1 }
```

Rust does not have shorthand argument names – you always name your parameters.

## Type inference

Both languages infer closure parameter and return types from context. In Swift:

```swift
// Swift
let numbers = [3, 1, 4, 1, 5]
let sorted = numbers.sorted { $0 < $1 }
```

In Rust:

```rust
// Rust
let mut numbers = vec![3, 1, 4, 1, 5];
numbers.sort_by(|a, b| a.cmp(b));
// numbers is now [1, 1, 3, 4, 5]
```

In the Rust example, the compiler infers that `a` and `b` are `&i32` based on the signature of `sort_by`. You do not need to annotate the types.

One important difference: once a Rust closure's types are inferred from its first use, they are fixed. You cannot use the same closure with different types:

```rust
// Rust – this would NOT compile
// fn main() {
//     let identity = |x| x;
//     let a = identity(5);       // infers x: i32
//     let b = identity("hello"); // error: expected i32, found &str
// }
```

This is because Rust closures are not generic. Each closure has a single concrete type determined at the point of definition. Swift closures have the same limitation.

## The three closure traits

This is where Rust diverges significantly from Swift. Rust classifies closures into three categories based on how they interact with captured values. These categories are represented by three traits:

- **`Fn`**: borrows captured values immutably. Can be called multiple times. The closure only reads from its environment.
- **`FnMut`**: borrows captured values mutably. Can be called multiple times, but requires exclusive (mutable) access. The closure may modify its environment.
- **`FnOnce`**: consumes captured values (takes ownership). Can be called only once, because the captured values are moved out.

These form a hierarchy: every `Fn` is also `FnMut`, and every `FnMut` is also `FnOnce`. A function that accepts `FnOnce` will accept any closure, while a function that requires `Fn` is the most restrictive.

```rust
// Rust
fn main() {
    // Fn – only reads captured value
    let name = String::from("Alice");
    let greet = || println!("Hello, {name}!");
    greet();
    greet(); // can call multiple times
    println!("{name}"); // name is still accessible

    // FnMut – modifies captured value
    let mut count = 0;
    let mut increment = || {
        count += 1;
        println!("count = {count}");
    };
    increment();
    increment();

    // FnOnce – consumes captured value
    let data = vec![1, 2, 3];
    let consume = || {
        let moved = data; // data is moved into this local
        println!("consumed: {moved:?}");
    };
    consume();
    // consume(); // error: closure cannot be called again
    // println!("{data:?}"); // error: data was moved
}
```

The compiler automatically determines which trait a closure implements based on what it does with its captures. You do not manually annotate closures with `Fn`, `FnMut`, or `FnOnce` – the compiler figures it out.

Swift does not have this distinction. Swift closures capture `var` variables by reference and `let` constants by value. All Swift closures can be called any number of times. A Swift closure that modifies a captured `var` simply mutates through the reference. The `Fn`/`FnMut`/`FnOnce` categorization is a direct consequence of Rust's ownership model.

## `move` closures

By default, Rust closures capture values in the least restrictive way possible – preferring to borrow rather than move. The `move` keyword forces all captures to be moved into the closure, transferring ownership:

```rust
// Rust
fn main() {
    let name = String::from("Alice");

    // Without move: closure borrows name
    let greet = || println!("Hello, {name}!");
    greet();
    println!("Still have: {name}"); // name is still accessible

    // With move: closure takes ownership of name
    let name = String::from("Bob");
    let greet = move || println!("Hello, {name}!");
    greet();
    // println!("{name}"); // error: name was moved into the closure
}
```

`move` closures are essential when the closure needs to outlive the scope where it was created – for example, when passing a closure to another thread or returning it from a function. Without `move`, the closure would hold references to local variables that no longer exist.

This is conceptually similar to Swift's capture lists, but the mechanism is inverted. In Swift, closures capture by reference by default, and you use a capture list to capture by value:

```swift
// Swift
var name = "Alice"

// Default: captures name by reference
let greet = { print("Hello, \(name)!") }
name = "Bob"
greet() // prints "Hello, Bob!" – sees the mutation

// Capture list: captures name by value
let greetCopy = { [name] in print("Hello, \(name)!") }
name = "Charlie"
greetCopy() // prints "Hello, Bob!" – captured the value at creation time
```

In Rust, closures capture by reference by default (when possible), and `move` forces capture by value. The parallel is:

| Swift | Rust | Behavior |
|---|---|---|
| Default capture | Default capture | Borrows (Rust) / References (Swift) |
| `[name]` capture list | `move` closure | Copies/moves value into closure |

One important difference: Rust's `move` moves all captures, not specific ones. You cannot selectively move some captures and borrow others within a single closure. If you need that, you can create local references before the closure:

```rust
// Rust
fn main() {
    let owned = String::from("owned");
    let borrowed = String::from("borrowed");

    let borrowed_ref = &borrowed; // create a reference before the closure
    let closure = move || {
        // owned is moved, borrowed_ref (a reference) is copied
        println!("{owned}, {borrowed_ref}");
    };
    closure();
    // owned is no longer accessible here
    println!("{borrowed}"); // borrowed is still accessible
}
```

## Closures as function parameters

When writing functions that accept closures, you use trait bounds to specify what kind of closure is accepted:

```rust
// Rust
fn apply_twice<F: Fn(i32) -> i32>(f: F, value: i32) -> i32 {
    f(f(value))
}

let double = |x| x * 2;
apply_twice(double, 3) // 12
```

The choice of `Fn`, `FnMut`, or `FnOnce` determines what callers can pass and how the function can use the closure:

```rust
// Rust
// Accepts any closure (most flexible for callers)
fn call_once<F: FnOnce() -> String>(f: F) -> String {
    f()
}

// Requires a closure that can be called multiple times, may mutate
fn call_repeatedly<F: FnMut()>(mut f: F) {
    f();
    f();
    f();
}

// Requires a closure that can be called multiple times, read-only
fn call_many<F: Fn() -> i32>(f: F) -> i32 {
    f() + f() + f()
}

fn main() {
    let result = call_once(|| String::from("hello"));
    println!("{result}");

    let mut count = 0;
    call_repeatedly(|| {
        count += 1;
        println!("count = {count}");
    });

    let total = call_many(|| 10);
    println!("total = {total}");
}
```

In Swift, closures are passed as function types without distinguishing between these categories:

```swift
// Swift
func applyTwice(_ f: (Int) -> Int, to value: Int) -> Int {
    f(f(value))
}

let result = applyTwice({ $0 * 2 }, to: 3) // 12
```

Swift's `@escaping` annotation controls closure lifetime – whether a closure can outlive the function call. A non-escaping closure in Swift is guaranteed to not outlive the function that receives it, while an `@escaping` closure may be stored and called later. In Rust, this concern is handled through ownership (`move` closures) and lifetime bounds. A closure that needs to be stored or called later typically requires `'static` lifetime bounds or `move`.

## Closures as return types

Returning closures from functions requires specifying the return type. Since each closure has a unique, unnameable type, you use `impl Fn` to return a closure:

```rust
// Rust
fn make_adder(x: i32) -> impl Fn(i32) -> i32 {
    move |y| x + y
}

let add_five = make_adder(5);
add_five(3)  // 8
add_five(10) // 15
```

The `move` keyword is necessary here because the closure must own `x` – the local variable would otherwise be dropped when `make_adder` returns.

In Swift, returning closures is straightforward because closures are reference types:

```swift
// Swift
func makeAdder(_ x: Int) -> (Int) -> Int {
    { y in x + y }
}
```

If you need to return different closures from different branches (where the concrete types differ), you must use a trait object instead of `impl Fn`:

```rust
// Rust
fn make_operation(multiply: bool) -> Box<dyn Fn(i32) -> i32> {
    if multiply {
        Box::new(|x| x * 2)
    } else {
        Box::new(|x| x + 10)
    }
}

let op = make_operation(true);
op(5) // 10
```

This parallels the distinction between `some Protocol` and `any Protocol` in Swift – `impl Fn` is a single opaque type, while `Box<dyn Fn>` is an existential that can hold different concrete types.

## Closures and ownership

Rust's closure system is deeply integrated with ownership and borrowing. Understanding how closures capture values is essential for writing correct code.

### Capture modes

The compiler determines the capture mode for each variable independently:

```rust
// Rust
fn main() {
    let name = String::from("Alice");   // will be borrowed
    let mut scores = vec![90, 85, 95];  // will be mutably borrowed

    let mut process = || {
        println!("Processing {name}");  // immutable borrow of name
        scores.push(100);               // mutable borrow of scores
    };

    // scores cannot be used here because the closure
    // holds a mutable borrow of it
    process();
    process();

    // After the closure is no longer used, borrows are released
    println!("{name}: {scores:?}");
}
```

The closure borrows `name` immutably and `scores` mutably. Because it holds a mutable borrow of `scores`, the closure itself is `FnMut`. Rust's borrow checker ensures no other code accesses `scores` while the closure could be called.

### Closures that consume values

When a closure moves a value out of its capture, it becomes `FnOnce`:

```rust
// Rust
let items = vec![1, 2, 3];

let closure = || {
    drop(items); // consumes items
};

closure();
// closure(); // error: cannot call FnOnce closure twice
```

### `move` with `Copy` types

For types that implement `Copy` (like integers and booleans), `move` copies the value rather than moving it. The original remains usable:

```rust
// Rust
fn main() {
    let x = 42;
    let closure = move || println!("{x}");
    closure();
    println!("{x}"); // x is still accessible because i32 implements Copy
}
```

This is similar to how Swift's capture lists copy value types.

## Closures and iterators

Closures are used extensively with iterator adapters. This is one of the most common places you will write closures in Rust, just as in Swift:

```swift
// Swift
let numbers = [1, 2, 3, 4, 5]
let doubled = numbers.map { $0 * 2 }
let evens = numbers.filter { $0 % 2 == 0 }
let sum = numbers.reduce(0) { $0 + $1 }
```

```rust
// Rust
let numbers = vec![1, 2, 3, 4, 5];
let doubled: Vec<i32> = numbers.iter().map(|x| x * 2).collect();
let evens: Vec<&i32> = numbers.iter().filter(|x| *x % 2 == 0).collect();
let sum: i32 = numbers.iter().sum();
// doubled is [2, 4, 6, 8, 10], evens is [2, 4], sum is 15
```

Notice that `filter` passes references to the closure (`&&i32` in this case, since `iter()` already yields references), so you dereference with `*x`. This is a common source of confusion for newcomers.

## Key differences and gotchas

- **Three closure traits**: Rust closures are categorized as `Fn`, `FnMut`, or `FnOnce` based on how they use captured values. Swift closures have no such distinction – they are all reference-capturing and always callable multiple times.
- **Capture by borrowing vs by reference**: Rust closures borrow captured values by default (with the borrow checked at compile time). Swift closures capture by reference, and mutations to captured variables are visible both inside and outside the closure.
- **`move` is all-or-nothing**: Rust's `move` keyword applies to all captures. Swift's capture lists let you select specific variables to capture by value.
- **Each closure has a unique type**: Two closures with the same signature have different types in Rust. You cannot store them in a variable with a named type – you must use generics, `impl Fn`, or `Box<dyn Fn>`.
- **No `@escaping`**: Rust does not have an `@escaping` annotation. Instead, escaping behavior is controlled by ownership: if a closure needs to outlive the current scope, it must own its captures (via `move`) and the function accepting it uses `'static` bounds or `Box<dyn Fn>`.
- **No shorthand arguments**: Rust does not have Swift's `$0`, `$1` shorthand. You always name closure parameters.
- **Iterator closures receive references**: When using `iter()`, closures receive `&T`. When using `into_iter()`, they receive `T` (owned). This affects whether you need to dereference inside the closure.
- **Closures can implement traits**: Because each closure has a unique anonymous type that implements `Fn`, `FnMut`, or `FnOnce`, closures integrate with the trait system. A function that accepts `impl Fn(i32) -> i32` is generic over all closures with that signature, and the call is monomorphized (zero overhead).

## Further reading

- [Closures: Anonymous Functions that Capture Their Environment](https://doc.rust-lang.org/book/ch13-01-closures.html): The Rust Programming Language
- [Closure Types](https://doc.rust-lang.org/reference/types/closure.html): The Rust Reference
- [Fn](https://doc.rust-lang.org/std/ops/trait.Fn.html), [FnMut](https://doc.rust-lang.org/std/ops/trait.FnMut.html), [FnOnce](https://doc.rust-lang.org/std/ops/trait.FnOnce.html): Rust standard library documentation
- [Processing a Series of Items with Iterators](https://doc.rust-lang.org/book/ch13-02-iterators.html): The Rust Programming Language
