---
title: Ownership Basics
sidebar:
  order: 12
---

Ownership is the concept that makes Rust fundamentally different from Swift. Both languages care deeply about memory safety, but they achieve it through opposite strategies. Swift uses Automatic Reference Counting – a runtime mechanism that tracks how many references point to an object and frees it when the count reaches zero. Rust uses ownership – a set of compile-time rules that determine when memory is allocated and freed, with no implicit runtime bookkeeping in the default case.

If you understand these rules, everything else about Rust's memory model will follow more naturally.

## The three ownership rules

Every value in Rust is governed by three rules:

1. Each value has exactly one *owner* – a variable that holds the value.
2. There can only be one owner at a time.
3. When the owner goes out of scope, the value is dropped (its memory is freed).

These rules are enforced entirely at compile time. In Rust's default ownership model there is no garbage collector and no implicit reference counting. The compiler inserts the deallocation code for you at exactly the right place.

In Swift, you rarely think about who "owns" a value because ARC manages the lifetime of reference types automatically, and value types present value semantics by default. In Rust, ownership is explicit and central to how you write code.

## Scope and dropping

The simplest way to see ownership in action is through scope:

```rust
// Rust
fn main() {
    {
        let s = String::from("hello"); // s owns the String
        println!("{s}");
    } // s goes out of scope; the String is dropped and its memory is freed
}
```

```swift
// Swift
func example() {
    let s = "hello" // String is a value-semantic type
    print(s)
} // s goes out of scope, memory is reclaimed
```

In Swift, when a class instance goes out of scope and no other references remain, ARC decrements the retain count and deallocates the object. In Rust, the drop happens deterministically at the closing brace – no counting involved.

## Move semantics

When you assign a value from one variable to another in Rust, ownership *moves*. The original variable becomes invalid and can no longer be used. This is the single biggest difference from Swift's behavior.

```rust
// Rust
let s1 = String::from("hello");
let s2 = s1; // ownership moves from s1 to s2

// println!("{s1}"); // compile error: value used after move
```

The compiler rejects the commented-out line with an error like:

```
error[E0382]: borrow of moved value: `s1`
 --> src/main.rs:5:20
  |
2 |     let s1 = String::from("hello");
  |         -- move occurs because `s1` has type `String`
3 |     let s2 = s1;
  |              -- value moved here
5 |     println!("{s1}");
  |                ^^ value borrowed here after move
```

This is unlike anything in Swift. In Swift, assigning a value type creates an independent copy, and assigning a reference type creates a new reference (incrementing the retain count). Neither invalidates the original variable:

```swift
// Swift – value types copy
var s1 = "hello"
var s2 = s1 // s2 is an independent copy
s1 += " world"
print(s1) // "hello world"
print(s2) // "hello"

// Swift – reference types share
class Box {
    var value: String
    init(_ value: String) { self.value = value }
}

let b1 = Box("hello")
let b2 = b1 // b2 points to the same object (retain count incremented)
b2.value = "world"
print(b1.value) // "world" – same object
```

In Rust, there is no implicit copying of heap-allocated data and no reference counting. The move is a shallow copy of the pointer, length, and capacity – the same bytes that sit on the stack – but the original variable is invalidated so there is only ever one owner of the heap data.

### Moves happen in function calls too

Passing a value to a function follows the same rule – ownership moves into the function parameter:

```rust
// Rust
fn takes_ownership(s: String) {
    println!("{s}");
} // s is dropped here

fn main() {
    let greeting = String::from("hello");
    takes_ownership(greeting);

    // println!("{greeting}"); // compile error: greeting was moved
}
```

The Swift equivalent has no such restriction:

```swift
// Swift
func takesValue(_ s: String) {
    print(s)
}

let greeting = "hello"
takesValue(greeting)
print(greeting) // works fine – String is a value type
```

If you need to keep using a value after passing it to a function in Rust, you have several options: pass a reference instead of the value (covered in [Chapter 13](../references-and-borrowing/)), clone the value, or have the function return the value back to you.

### Returning values transfers ownership out

```rust
// Rust
fn create_greeting() -> String {
    let s = String::from("hello");
    s // ownership moves to the caller
}

fn main() {
    let greeting = create_greeting(); // greeting now owns the String
    println!("{greeting}");
}
```

This is how you "give back" ownership. No copies are made – the String's data stays on the heap, and the caller takes over responsibility for dropping it.

## Stack vs. heap

To understand why moves behave the way they do, it helps to know where values live in memory.

**Stack allocation**: fixed-size types like integers, floats, booleans, and tuples of fixed-size types live entirely on the stack. Copying them is trivial – it is just a `memcpy` of a few bytes. There is no heap data to worry about.

**Heap allocation**: types like `String` and `Vec<T>` store their data on the heap. The variable on the stack holds a pointer, a length, and a capacity. If Rust allowed you to simply copy the stack portion without doing anything about the heap data, you would end up with two variables pointing to the same heap allocation – and when both go out of scope, the memory would be freed twice. This is exactly the double-free bug that C and C++ developers dread.

Rust's solution is move semantics: when you assign a heap-owning value, the stack data is copied but the original is invalidated. Only one variable can drop the heap allocation.

Swift solves the same problem differently for reference types – ARC ensures the last reference triggers deallocation – and avoids it entirely for value types by making copies. Both approaches prevent double-free bugs, but Rust's has zero runtime cost.

## The `Copy` trait: types that are implicitly copied

Not all types move on assignment. Simple, fixed-size types implement the `Copy` trait, which means they are duplicated automatically:

```rust
// Rust
let x: i32 = 42;
let y = x; // x is copied, not moved
// both x and y are valid
```

Integers, floats, booleans, characters, and tuples of `Copy` types are all `Copy`. Assigning or passing them creates an independent copy, just like Swift's value types:

```swift
// Swift
let x = 42
let y = x // independent copy
print("x = \(x), y = \(y)") // both valid
```

The distinction in Rust is:

- **`Copy` types**: duplicated implicitly on assignment and function calls. Always stack-allocated, cheap to copy.
- **Non-`Copy` types**: moved on assignment and function calls. The original is invalidated.

In Swift, value types present copy semantics on assignment, often optimized with copy-on-write under the hood. Rust is more selective – a struct that contains a `String` cannot be `Copy`, because copying the struct would need to duplicate the heap-allocated string data, and Rust will not do that implicitly.

```rust
// Rust – this struct can be Copy because all fields are Copy
#[derive(Copy, Clone)]
struct Point {
    x: f64,
    y: f64,
}

let p1 = Point { x: 1.0, y: 2.0 };
let p2 = p1; // copied, not moved – both p1 and p2 are valid
```

```rust
// Rust – this struct cannot be Copy because String is not Copy
struct Person {
    name: String,
    age: u32,
}

let p1 = Person {
    name: String::from("Alice"),
    age: 30,
};
let p2 = p1; // moved, not copied

// println!("{}", p1.name); // compile error: p1 was moved
```

### Why `Copy` requires `Clone`

You will notice that deriving `Copy` always requires `Clone` as well (`#[derive(Copy, Clone)]`). `Copy` is a marker trait that tells the compiler "this type can be duplicated by copying bits." `Clone` provides the `.clone()` method for explicit duplication. Every `Copy` type is also `Clone`, but not every `Clone` type is `Copy`.

## The `Clone` trait: explicit deep copies

When you need a duplicate of a non-`Copy` type, you call `.clone()`:

```rust
// Rust
let s1 = String::from("hello");
let s2 = s1.clone(); // explicit deep copy – both s1 and s2 are valid
```

`.clone()` allocates new heap memory and copies the data into it. This is an explicit operation because it has real cost – Rust wants you to see where allocations happen.

In Swift, you rarely call anything like `.clone()` because the language copies value types automatically and uses copy-on-write optimization for types like `Array`, `String`, and `Dictionary`. The copy-on-write mechanism defers the actual duplication until one copy is mutated, making many copies effectively free. Rust does not have built-in copy-on-write – when you `.clone()`, the duplication happens immediately.

```swift
// Swift – copy-on-write
var a = [1, 2, 3]
var b = a // no copy yet – a and b share storage
b.append(4) // now a copy is made because b is being mutated
print(a) // [1, 2, 3]
print(b) // [1, 2, 3, 4]
```

Rust's `Rc<T>` (reference-counted pointer) and `Arc<T>` (atomic reference-counted pointer) provide shared ownership when you need it, but they are opt-in and explicit – covered in [Chapter 20](../../memory-and-smart-pointers/smart-pointers/).

## `String`: the canonical move type

`String` is the type you will encounter most often when learning ownership, because it combines heap allocation with common operations that would be confusing without understanding moves.

A Rust `String` is a growable, UTF-8 encoded string stored on the heap. The variable on the stack holds three values: a pointer to the heap buffer, the length of the string, and the buffer's capacity.

When you write `let s2 = s1;`, Rust copies those three stack values (pointer, length, capacity) to `s2` and marks `s1` as invalid. The heap data is not duplicated. This is a constant-time operation regardless of string length.

Compare this with Rust's string slice type, `&str`, which is a borrowed reference to string data and does not own the data it points to. String slices are covered in the next chapter.

Here is a complete example showing moves, clones, and function calls with `String`:

```rust
// Rust
fn print_length(s: String) -> String {
    println!("{s} has length {}", s.len());
    s // return ownership to the caller
}

fn main() {
    let original = String::from("ownership");
    let returned = print_length(original);
    // original is now invalid – it was moved into print_length
    // but print_length gave it back via the return value

    let cloned = returned.clone();
    println!("returned: {returned}");
    println!("cloned: {cloned}");
}
```

This pattern of passing ownership in and receiving it back is valid but verbose. In practice, you will usually pass a reference instead, which lets the function borrow the value without taking ownership. That is the subject of the next chapter.

## Key differences and gotchas

**Move by default vs. copy by default**: in Swift, assigning a struct or enum always copies the value. In Rust, it moves the value unless the type implements `Copy`. This is the most common source of confusion for Swift developers.

**No implicit copy-on-write**: Swift optimizes large value types like `Array` and `String` with copy-on-write. Rust does not do this automatically – copies are either trivial (`Copy` types) or explicit (`.clone()`).

**Ownership is not about pointers**: in Swift, the concept of "who owns this object" only applies to reference types and is managed by ARC. In Rust, *every* value has an owner, even simple integers. Ownership is a compile-time concept, not a runtime mechanism.

**You cannot use a value after it has been moved**: this is the rule that takes the most getting used to. The compiler tracks moves through assignments, function calls, and pattern matching. If a value has been moved, any attempt to use it is a compile error. The error messages are detailed and will tell you where the move happened.

**`Drop` is deterministic**: Rust values are dropped at the end of their scope, not at some indeterminate point during a GC cycle or when a retain count hits zero. This makes resource cleanup predictable – files are closed, locks are released, and memory is freed exactly when the owning variable goes out of scope. This is conceptually similar to Swift's `deinit`, which also runs deterministically when the last reference is released. The difference is that in Rust, the drop point is always visible at the closing brace of the owning scope, whereas in Swift, the last ARC release can be harder to predict when multiple references exist.

**Partial moves**: when you move a field out of a struct, the struct itself becomes partially moved and can no longer be used as a whole. This has no equivalent in Swift.

```rust
// Rust
struct Config {
    name: String,
    debug: bool,
}

let config = Config {
    name: String::from("app"),
    debug: true,
};

let name = config.name; // name field moved out
// println!("{}", config.name); // error: field was moved
// config.debug is still valid – bool is Copy
```

## Further reading

- [The Rust Programming Language – Understanding Ownership](https://doc.rust-lang.org/book/ch04-01-what-is-ownership.html): the official treatment of ownership
- [Rust by Example – Ownership and moves](https://doc.rust-lang.org/rust-by-example/scope/move.html): concise examples of move semantics
- [The `Copy` trait documentation](https://doc.rust-lang.org/std/marker/trait.Copy.html): which types implement `Copy` and why
- [The `Clone` trait documentation](https://doc.rust-lang.org/std/clone/trait.Clone.html): how `.clone()` works under the hood
- [Visualizing memory layout of Rust's data types](https://www.youtube.com/watch?v=rDoqT-a6UFg): a video walkthrough of stack and heap allocation in Rust
