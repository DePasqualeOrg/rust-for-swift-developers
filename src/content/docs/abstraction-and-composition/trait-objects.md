---
title: Trait Objects and Dynamic Dispatch
sidebar:
  order: 17
---

The previous two chapters covered traits and generics – Rust's system for writing abstract, reusable code that the compiler monomorphizes into specialized implementations. But sometimes you need to work with values of different types through a single interface at runtime, without knowing the concrete type at compile time. This is where trait objects come in.

Trait objects are Rust's answer to Swift's existential types (`any Protocol`). They enable dynamic dispatch – method calls resolved through a vtable at runtime rather than through compile-time specialization.

## Static dispatch vs dynamic dispatch

To understand trait objects, it helps to contrast the two forms of polymorphism available in Rust.

With generics (static dispatch), the compiler knows the concrete type at compile time and generates specialized code:

```rust
// Rust – static dispatch
use std::fmt::Display;

fn print_item<T: Display>(item: &T) {
    println!("{item}");
}

print_item(&42);       // compiler generates print_item::<i32>
print_item(&"hello");  // compiler generates print_item::<&str>
```

With trait objects (dynamic dispatch), the concrete type is erased and method calls go through a vtable:

```rust
// Rust – dynamic dispatch
use std::fmt::Display;

fn print_item(item: &dyn Display) {
    println!("{item}");
}

print_item(&42);
print_item(&"hello");
```

Both compile and produce the same output. The difference is in how the compiler handles them.

## `dyn Trait`: Rust's existential type

In Swift, when you want to store or pass a value of any type conforming to a protocol, you use an existential:

```swift
// Swift
func printAnything(_ item: any CustomStringConvertible) {
    print(item.description)
}
```

Rust's equivalent is `dyn Trait`:

```rust
// Rust
use std::fmt::Display;

fn print_anything(item: &dyn Display) {
    println!("{item}");
}

print_anything(&42);
print_anything(&String::from("hello"));
```

The `dyn` keyword is required – it makes it explicit that you are opting into dynamic dispatch. Without it, `Display` in a type position refers to the trait itself (used in bounds), not a trait object.

A key constraint: `dyn Trait` is unsized. You cannot use it directly as a variable type or function return type. You must always use it behind some kind of pointer – a reference (`&dyn Trait`), a `Box` (`Box<dyn Trait>`), or another smart pointer.

## Borrowed trait objects: `&dyn Trait`

The simplest form is a reference to a trait object. This works when you need to pass a value polymorphically without taking ownership:

```rust
// Rust
trait Describe {
    fn describe(&self) -> String;
}

struct Circle {
    radius: f64,
}

struct Square {
    side: f64,
}

impl Describe for Circle {
    fn describe(&self) -> String {
        format!("Circle with radius {}", self.radius)
    }
}

impl Describe for Square {
    fn describe(&self) -> String {
        format!("Square with side {}", self.side)
    }
}

fn print_shape(shape: &dyn Describe) {
    println!("{}", shape.describe());
}

let c = Circle { radius: 3.0 };
let s = Square { side: 4.0 };
print_shape(&c);
print_shape(&s);
```

This is comparable to Swift's `any Describe` used as a parameter type – the function accepts any type that conforms to the protocol/trait, with the concrete type erased.

## Owned trait objects: `Box<dyn Trait>`

When you need to own a trait object – for instance, to store it in a struct or return it from a function – use `Box<dyn Trait>`:

```swift
// Swift
protocol Animal {
    func speak() -> String
}

struct Dog: Animal {
    func speak() -> String { "Woof" }
}

struct Cat: Animal {
    func speak() -> String { "Meow" }
}

func makeAnimal(isDog: Bool) -> any Animal {
    isDog ? Dog() : Cat()
}
```

```rust
// Rust
trait Animal {
    fn speak(&self) -> &str;
}

struct Dog;
struct Cat;

impl Animal for Dog {
    fn speak(&self) -> &str {
        "Woof"
    }
}

impl Animal for Cat {
    fn speak(&self) -> &str {
        "Meow"
    }
}

fn make_animal(is_dog: bool) -> Box<dyn Animal> {
    if is_dog {
        Box::new(Dog)
    } else {
        Box::new(Cat)
    }
}

fn main() {
    let animal = make_animal(true);
    println!("{}", animal.speak());

    let animal = make_animal(false);
    println!("{}", animal.speak());
}
```

`Box<dyn Animal>` is a heap-allocated, owned trait object. It is a fat pointer: it stores both a pointer to the data and a pointer to the vtable. When you call `animal.speak()`, the runtime looks up the method in the vtable and dispatches to the correct implementation.

### Heterogeneous collections

One of the most common uses for trait objects is storing values of different types in a single collection:

```rust
// Rust
trait Shape {
    fn area(&self) -> f64;
    fn name(&self) -> &str;
}

struct Circle {
    radius: f64,
}

struct Rectangle {
    width: f64,
    height: f64,
}

impl Shape for Circle {
    fn area(&self) -> f64 {
        std::f64::consts::PI * self.radius * self.radius
    }
    fn name(&self) -> &str {
        "Circle"
    }
}

impl Shape for Rectangle {
    fn area(&self) -> f64 {
        self.width * self.height
    }
    fn name(&self) -> &str {
        "Rectangle"
    }
}

fn main() {
    let shapes: Vec<Box<dyn Shape>> = vec![
        Box::new(Circle { radius: 3.0 }),
        Box::new(Rectangle { width: 4.0, height: 5.0 }),
    ];

    for shape in &shapes {
        println!("{}: area = {:.2}", shape.name(), shape.area());
    }
}
```

In Swift, you would write `[any Shape]` to achieve the same thing. The Rust version is more explicit about the allocation: each element is boxed on the heap.

## Dyn compatibility (formerly object safety)

Not every trait can be used as a trait object. The Rust Reference calls this requirement *dyn compatibility*; older material calls it *object safety*. The rules ensure that calls remain well-defined after the concrete type is erased.

A few of the main rules are:

- The trait and its supertraits must not require `Self: Sized`.
- Dispatchable methods need a supported receiver, such as `&self`, `&mut self`, or `Box<Self>`, and cannot use `Self` elsewhere in their signatures or have type parameters.
- Methods excluded from dynamic dispatch can use `where Self: Sized`; such methods do not prevent a trait object from being formed.
- Associated constants, generic associated types, and dispatchable `async fn` or `-> impl Trait` methods impose further restrictions. See the [complete dyn-compatibility rules](https://doc.rust-lang.org/reference/items/traits.html#dyn-compatibility).

Here is an example of a trait that is not object-safe:

```rust
// Rust
trait Clonable {
    fn clone_self(&self) -> Self; // returns Self – not object-safe
}

// This would NOT compile:
// fn take_clonable(c: &dyn Clonable) { }
```

Returning `Self` prevents object safety because the caller does not know the concrete type and therefore does not know the size of the return value.

The `Clone` trait in Rust's standard library has this same issue, which is why `dyn Clone` is not valid. If you need a clonable trait object, you can work around it by defining a method that returns `Box<dyn Trait>` instead of `Self`.

Swift's existentials have similar restrictions. The `any` keyword and constrained existentials have relaxed some of them, but many of the same underlying limitations apply.

### Making a trait object-safe

If you need both generic methods and trait object usage, you can split the trait:

```rust
// Rust
trait Drawable {
    fn draw(&self) -> String;
}

// Separate trait with the generic method
trait DrawableCompare: Drawable {
    fn same_shape<T: Drawable>(&self, other: &T) -> bool;
}

// dyn Drawable works fine – it has no generic methods
fn render(items: &[&dyn Drawable]) {
    for item in items {
        println!("{}", item.draw());
    }
}

struct Dot;

impl Drawable for Dot {
    fn draw(&self) -> String {
        String::from(".")
    }
}

let items: Vec<&dyn Drawable> = vec![&Dot, &Dot];
render(&items);
```

## When to use trait objects vs generics

This decision parallels the choice between `any Protocol` (existentials) and `some Protocol` (constrained generics) in Swift:

| Criterion | Generics (static dispatch) | Trait objects (dynamic dispatch) |
|---|---|---|
| Performance | No runtime overhead | Vtable lookup per call |
| Binary size | Larger (monomorphized copies) | Smaller (single implementation) |
| Heterogeneous collections | Not possible | Yes (`Vec<Box<dyn Trait>>`) |
| Return different types | Not directly | Yes (`Box<dyn Trait>`) |
| Compile-time type info | Full type information retained | Type erased |
| Inlining | Usually easier to inline | Requires the optimizer to recover the concrete call target |

Use generics when:
- You know the concrete type (or a bounded set of types) at compile time
- Performance is a priority and the overhead of vtable dispatch matters
- You need to use trait methods that are not object-safe

Use trait objects when:
- You need a heterogeneous collection of different types behind a single interface
- You want to return different types from a function based on runtime conditions
- You want to reduce binary size by avoiding monomorphization
- You are building plugin-like architectures where types are determined at runtime

## Performance implications

The performance difference between generics and trait objects comes down to inlining and indirection.

With generics, the compiler generates specialized code for each type. This enables inlining, constant propagation, and other optimizations. The method call compiles to a direct function call – or often, no call at all if the function body is inlined.

Trait-object calls normally use an indirect call through a vtable, which can limit inlining and other optimizations. If the optimizer can prove the concrete target, it may devirtualize the call. Performance depends on whether that happens and how much work each call performs.

In practice, the overhead is small. For most applications, the ergonomic benefits of trait objects outweigh the performance cost. But in tight loops or performance-critical paths, generics can make a measurable difference.

Swift's existentials also use type metadata and protocol witness tables. Their representation depends on the protocol constraints and may store a small value inline. A Rust pointer to `dyn Trait` carries a data pointer and a vtable pointer; it does not contain an inline buffer for the value. Comparing pointer sizes alone therefore does not compare the total storage costs.

## The `Any` trait

Rust has a built-in trait called `Any` that enables basic runtime type reflection, similar to using `Any` in Swift:

```rust
// Rust
use std::any::Any;

fn describe(value: &dyn Any) {
    if let Some(n) = value.downcast_ref::<i32>() {
        println!("It's an integer: {n}");
    } else if let Some(s) = value.downcast_ref::<String>() {
        println!("It's a string: {s}");
    } else {
        println!("Unknown type");
    }
}

describe(&42);
describe(&String::from("hello"));
describe(&3.14_f64);
```

`Any` allows you to downcast a trait object to a concrete type using `downcast_ref` (for references) or `downcast` (for `Box<dyn Any>`). This is similar to Swift's `as?` casting on `Any`:

```swift
// Swift
func describe(_ value: Any) {
    if let n = value as? Int {
        print("It's an integer: \(n)")
    } else if let s = value as? String {
        print("It's a string: \(s)")
    } else {
        print("Unknown type")
    }
}
```

`Any` supports checked downcasts to concrete types and requires `'static`, so it cannot represent arbitrary short-lived borrowed data. Prefer a trait exposing the operations you need when callers do not need concrete-type inspection.

## Key differences and gotchas

- **Explicit `dyn` keyword**: Modern Rust editions require `dyn` for trait objects. Swift uses `any` for explicit existential types; requiring it everywhere is controlled by the `ExistentialAny` feature, rather than universally by Swift 6 language mode.
- **Must use a pointer**: `dyn Trait` is unsized, so you always use it behind `&`, `Box`, `Arc`, or another pointer. Swift's existentials handle this internally with a protocol witness container.
- **Dyn compatibility**: methods dispatched through a trait object must satisfy the restrictions described above. An otherwise incompatible method can often be excluded from dynamic dispatch with `where Self: Sized`; that need not disqualify the entire trait.
- **No automatic boxing**: Rust does not automatically box values to create trait objects. You must explicitly write `Box::new(value)`. Swift handles boxing implicitly when you assign a concrete value to an existential variable.
- **Wide pointers**: a reference to a trait object contains a data pointer and vtable metadata. Swift existential layouts depend on the constraints and representation; there is no universal size comparison.
- **Upcasting**: Current Rust supports trait-object upcasting, so a `dyn Subtrait` can coerce to a `dyn Supertrait`. In Swift, upcasting existentials is also supported.
- **Single trait (plus auto traits)**: A trait object can only be one trait, plus auto traits like `Send` and `Sync` (e.g., `dyn Display + Send`). You cannot write `dyn Display + Debug` unless you define a combined supertrait.

## Further reading

- [Using Trait Objects That Allow for Values of Different Types](https://doc.rust-lang.org/book/ch18-02-trait-objects.html): The Rust Programming Language
- [Object Safety](https://doc.rust-lang.org/reference/items/traits.html#object-safety): The Rust Reference
- [std::any::Any](https://doc.rust-lang.org/std/any/trait.Any.html): Rust standard library documentation
- [Dynamic Dispatch](https://doc.rust-lang.org/rust-by-example/trait/dyn.html): Rust by Example
