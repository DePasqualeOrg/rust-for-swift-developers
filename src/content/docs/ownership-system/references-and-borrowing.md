---
title: References and Borrowing
sidebar:
  order: 13
---

The previous chapter showed that passing a value to a function moves ownership, which means the caller can no longer use it. This is safe but inconvenient – you would not want to return every value back just so the caller can keep using it. References solve this problem. A reference lets you access a value without taking ownership of it, a concept Rust calls *borrowing*.

Swift developers are familiar with reference semantics through classes and ARC, and with `inout` parameters for mutating value types across function boundaries. Rust's borrowing system looks superficially similar but works very differently. References in Rust are not counted, do not keep values alive, and are governed by strict compile-time rules that prevent data races and dangling pointers.

## Shared references with `&T`

A shared reference, written `&T`, gives you read-only access to a value without taking ownership:

```rust
// Rust
fn print_length(s: &String) {
    println!("{s} has length {}", s.len());
}

fn main() {
    let greeting = String::from("hello");
    print_length(&greeting); // borrow greeting
    println!("{greeting}"); // still valid – we only borrowed it
}
```

The `&` in `&greeting` creates a reference, and the parameter type `&String` indicates the function borrows a `String` rather than owning it. When `print_length` returns, the borrow ends and `greeting` is still fully owned by `main`.

In Swift, passing a value type to a function always copies it. Passing a reference type shares it via ARC. Rust's shared references are different from both – they are zero-cost pointers that the compiler statically verifies:

```swift
// Swift – value types preserve value semantics across the call
func printLength(_ s: String) {
    print("\(s) has \(s.count) characters")
}

let greeting = "hello"
printLength(greeting) // greeting is copied
print(greeting) // still valid (it was always a copy)
```

You can have multiple shared references to the same value at the same time:

```rust
// Rust
let s = String::from("hello");
let r1 = &s;
let r2 = &s;
let r3 = &s;
// all three references are valid
```

This is safe because none of them can modify the value. Shared references are `Copy` – you can freely pass them around, and they all point to the same data without any ownership transfer.

### A note on `&String` vs. `&str`

Idiomatic Rust functions accept `&str` (a string slice) rather than `&String`, because `&str` is more general – it can refer to a `String`, a string literal, or a substring. Rust automatically coerces `&String` to `&str`, so the more idiomatic version of the example above would be:

```rust
// Rust – idiomatic
fn print_length(s: &str) {
    println!("{s} has length {}", s.len());
}

fn main() {
    let greeting = String::from("hello");
    print_length(&greeting); // &String coerces to &str
    print_length("world"); // &str literal works directly
}
```

This is similar to how Swift functions often accept `some StringProtocol` or use `String` directly since Swift's `String` is a value type without this distinction.

## Mutable references with `&mut T`

A mutable reference, written `&mut T`, gives you the ability to modify the borrowed value:

```rust
// Rust
fn add_exclamation(s: &mut String) {
    s.push('!');
}

fn main() {
    let mut greeting = String::from("hello");
    add_exclamation(&mut greeting);
    println!("{greeting}"); // "hello!"
}
```

Three things are required for a mutable borrow:

1. The variable must be declared `mut`.
2. The reference must be created with `&mut`.
3. The parameter type must be `&mut T`.

This is more explicit than Swift's `inout`, which requires a single `&` at the call site:

```swift
// Swift
func addExclamation(_ s: inout String) {
    s.append("!")
}

var greeting = "hello"
addExclamation(&greeting)
print(greeting) // "hello!"
```

While the syntax looks similar, the semantics are different. Swift's `inout` works by copying the value in, letting the function modify the copy, and then copying it back out (conceptually – the compiler may optimize this). Rust's `&mut` is a genuine mutable pointer to the original value. No copying occurs, and the caller's variable is modified in place.

## The borrowing rules

Rust enforces two rules about references that together prevent data races at compile time:

1. You can have *any number* of shared references (`&T`) to a value, OR
2. You can have *exactly one* mutable reference (`&mut T`) to a value –

but never both at the same time.

This is the heart of Rust's safety guarantee. A data race requires three conditions: multiple accesses to the same data, at least one of which is a write, happening concurrently. By ensuring that you never have a mutable reference coexisting with any other reference, Rust eliminates data races structurally. Importantly, these borrowing rules are enforced even in single-threaded code, which also prevents aliasing bugs like iterator invalidation – where modifying a collection while iterating over it leads to undefined behavior in languages like C++.

### Violations the compiler catches

```rust
// Rust – does not compile
let mut s = String::from("hello");

let r1 = &s; // shared borrow
let r2 = &mut s; // mutable borrow – error!

// println!("{r1}, {r2}");
```

The compiler reports:

```
error[E0502]: cannot borrow `s` as mutable because it is also borrowed as immutable
 --> src/main.rs:5:14
  |
4 |     let r1 = &s;
  |              -- immutable borrow occurs here
5 |     let r2 = &mut s;
  |              ^^^^^^ mutable borrow occurs here
6 |
7 |     println!("{r1}, {r2}");
  |                -- immutable borrow later used here
```

Similarly, you cannot have two mutable references at the same time:

```rust
// Rust – does not compile
let mut s = String::from("hello");

let r1 = &mut s;
let r2 = &mut s; // error: second mutable borrow

// println!("{r1}, {r2}");
```

### Non-Lexical Lifetimes (NLL)

The compiler is smart about when borrows end. A reference's borrow does not necessarily last until the end of its scope – it ends at the point of its last use. This feature, called Non-Lexical Lifetimes, makes the borrowing rules more ergonomic:

```rust
// Rust – this compiles
let mut s = String::from("hello");

let r1 = &s;
let r2 = &s;
println!("{r1}, {r2}"); // r1 and r2 are last used here

let r3 = &mut s; // no conflict – r1 and r2 are no longer in use
r3.push('!');
println!("{r3}");
```

This is valid because `r1` and `r2` are not used after the first `println!`, so the compiler ends their borrows before `r3` is created.

### Comparison with Swift

Swift does not have these aliasing restrictions in the same form. You can have multiple references to the same class instance, and any of them can mutate it at any time:

```swift
// Swift – multiple mutable references are allowed
class Counter {
    var count = 0
}

let a = Counter()
let b = a // same object
a.count += 1
b.count += 1
print(a.count) // 2
```

Swift catches some aliasing issues with its *exclusivity enforcement* for value types (introduced in Swift 4), which prevents overlapping `inout` accesses to the same variable. But this is narrower than Rust's system and does not cover reference types at all.

## Dangling reference prevention

Rust's borrowing rules prevent dangling references – pointers to memory that has been freed. The compiler ensures that references never outlive the data they point to:

```rust
// Rust – does not compile
fn dangling() -> &String {
    let s = String::from("hello");
    &s // error: s is dropped at the end of this function
}
```

The compiler reports:

```
error[E0106]: missing lifetime specifier
 --> src/main.rs:1:19
  |
1 | fn dangling() -> &String {
  |                   ^ expected named lifetime parameter
```

The underlying issue is that `s` is dropped when `dangling` returns, so the reference would point to freed memory. Rust refuses to compile this. The fix is to return the owned value instead:

```rust
// Rust – return the owned value
fn not_dangling() -> String {
    let s = String::from("hello");
    s // ownership moves to the caller
}

fn main() {
    let s = not_dangling();
    println!("{s}");
}
```

In Swift, this scenario cannot occur for reference types because ARC keeps the object alive as long as any reference exists. For value types, the value is copied on return, so there is nothing to dangle. Rust achieves the same safety without any runtime mechanism.

## Reborrowing

When you have a mutable reference, you can create a temporary shared reference from it. This is called *reborrowing*, and it happens implicitly:

```rust
// Rust
fn print_value(s: &str) {
    println!("{s}");
}

fn modify_and_print(s: &mut String) {
    s.push('!');
    print_value(s); // implicit reborrow: &mut String -> &String -> &str
    s.push('?');
}

fn main() {
    let mut greeting = String::from("hello");
    modify_and_print(&mut greeting);
    println!("{greeting}"); // "hello!?"
}
```

When `print_value(s)` is called, Rust temporarily reborrows the `&mut String` as a `&String` (which then coerces to `&str`). During this reborrow, the mutable reference is "frozen" – you cannot use it until the shared borrow ends. After `print_value` returns, the mutable reference becomes usable again.

You can also explicitly reborrow a mutable reference as another mutable reference:

```rust
// Rust
fn append_world(s: &mut String) {
    s.push_str(" world");
}

fn main() {
    let mut s = String::from("hello");
    let r = &mut s;
    append_world(&mut *r); // explicit reborrow of the mutable reference
    r.push('!');
    println!("{r}"); // "hello world!"
}
```

The `&mut *r` syntax dereferences `r` and then takes a new mutable reference, creating a temporary reborrow. In practice, Rust often inserts reborrows automatically, so you rarely need to write this explicitly.

## Borrowing in data structures

References can appear as fields in structs, but this requires lifetime annotations – a topic covered in the [next chapter](../lifetimes/). For now, here is a brief preview:

```rust
// Rust
struct Excerpt<'a> {
    text: &'a str,
}

let novel = String::from("Call me Ishmael. Some years ago...");
let first_sentence = &novel[..16];

let excerpt = Excerpt {
    text: first_sentence,
};
// excerpt.text is "Call me Ishmael."
```

The `'a` annotation tells the compiler that the `Excerpt` struct cannot outlive the data its `text` field references. Lifetimes are Rust's way of encoding the relationship between a reference and the data it borrows – more on this in Chapter 14.

## Patterns for working with the borrow checker

When you are starting out, you will occasionally write code that the borrow checker rejects. Here are some common patterns and their solutions.

### Splitting borrows on different fields

The borrow checker can track borrows at the field level for structs:

```rust
// Rust
struct Player {
    name: String,
    score: u32,
}

let mut player = Player {
    name: String::from("Alice"),
    score: 0,
};

let name_ref = &player.name; // borrow one field
player.score += 10; // mutate a different field – this is fine
// name_ref is still valid because score is a disjoint field
```

This works because the compiler can see that `name_ref` borrows `player.name` while the mutation touches `player.score` – they are disjoint.

### Clone to break borrow conflicts

When restructuring code is not practical, cloning can resolve borrow conflicts:

```rust
// Rust
let mut data = vec![String::from("a"), String::from("b"), String::from("c")];
let first = data[0].clone(); // clone to avoid borrowing data
data.push(String::from("d")); // now we can mutate data
// first is "a", data.len() is 4
```

Without the `.clone()`, `data[0]` would borrow `data` immutably, preventing the mutable `push`. Cloning creates an independent copy, so `data` is free to be mutated. This has a runtime cost, but it is explicit and clear.

### Scoping borrows

Sometimes you can fix borrow conflicts by narrowing the scope of a reference:

```rust
// Rust
let mut scores = vec![10, 20, 30];

{
    let first = &scores[0];
    // use first here
} // first goes out of scope, borrow ends

scores.push(40); // now safe to mutate
```

## Key differences and gotchas

**References are not pointers in the Swift/C sense**: Rust references are always valid (non-null) and always point to valid data. You cannot have a null reference in safe Rust, and you cannot have a reference to freed memory.

**`&mut` is not just "mutable pointer"**: `&mut T` means *exclusive* access. It is more like a lock than a pointer – while a mutable reference exists, nothing else can access the value. This exclusivity is what makes Rust's concurrency safety possible.

**Swift's `inout` is not Rust's `&mut`**: Swift's `inout` conceptually copies in and copies out. Rust's `&mut` is a direct mutable pointer with enforced exclusivity. The call-site syntax (`&` in Swift, `&mut` in Rust) is similar, but the underlying mechanics are different.

**Borrowing does not extend lifetime**: in Swift, holding a reference (via ARC) keeps the object alive. In Rust, a reference does not keep the value alive – the value's owner controls its lifetime, and references must not outlive the owner. This is enforced at compile time through lifetimes.

**The borrow checker is not an obstacle**: it can feel that way at first, but the borrow checker is catching real bugs – use-after-free, data races, iterator invalidation. When the borrow checker rejects your code, it is often pointing to a design issue that would cause a subtle bug in a language without these checks.

## Further reading

- [The Rust Programming Language – References and Borrowing](https://doc.rust-lang.org/book/ch04-02-references-and-borrowing.html): the official chapter on borrowing
- [The Rust Reference – Expressions: Borrow operators](https://doc.rust-lang.org/reference/expressions/operator-expr.html#borrow-operators): formal specification of borrow operators
- [Rust by Example – Borrowing](https://doc.rust-lang.org/rust-by-example/scope/borrow.html): hands-on borrowing examples
- [The Rustonomicon – References](https://doc.rust-lang.org/nomicon/references.html): advanced details on reference semantics
- [Non-Lexical Lifetimes RFC](https://rust-lang.github.io/rfcs/2094-nll.html): the design behind NLL
