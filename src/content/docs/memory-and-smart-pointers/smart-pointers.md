---
title: Smart Pointers
sidebar:
  order: 20
---

In Swift, you rarely think about where values live. Value types are usually stored inline in whatever contains them, classes are heap-allocated, and the compiler manages reference counting for you. Rust makes these decisions explicit. By default, values are owned by exactly one binding, and when you need heap allocation, shared ownership, or interior mutability, you reach for a smart pointer.

Smart pointers in Rust are structs that behave like references but carry additional semantics – they own the data they point to, manage its lifecycle, and enforce borrowing rules at compile time or runtime.

## `Box<T>`: heap allocation

`Box<T>` is the simplest smart pointer: it allocates a value on the heap and provides single ownership. When the `Box` goes out of scope, the heap memory is freed.

```rust
// Rust
let x = Box::new(42);
// x is freed here when it goes out of scope
```

In Swift, every class instance is automatically heap-allocated and reference-counted. There is no explicit `Box` – the compiler handles it:

```swift
// Swift
class Container {
    var value: Int
    init(value: Int) { self.value = value }
}

let c = Container(value: 42) // heap-allocated, ARC-managed
```

Rust's `Box` is closest to a Swift class with exactly one strong reference – but without any reference counting overhead. The compiler knows at compile time that there is a single owner, so there is no retain/release cost.

### When to use `Box`

You typically need `Box` in three situations:

- **Recursive types**: a type that contains itself needs indirection because the compiler cannot determine a fixed size at compile time. `Box` provides that indirection.
- **Large values**: moving large structs between stack frames involves copying. Boxing the value means only an 8-byte pointer is moved.
- **Trait objects**: when you need dynamic dispatch, `Box<dyn Trait>` stores a trait object on the heap. This is covered in [Chapter 17](../../abstraction-and-composition/trait-objects/).

Recursive types are a common case:

```rust
// Rust
#[derive(Debug)]
enum List {
    Cons(i32, Box<List>),
    Nil,
}

let list = List::Cons(1, Box::new(List::Cons(2, Box::new(List::Nil))));
```

Without `Box`, this enum would have infinite size because `List` contains `List`. The `Box` adds a level of indirection – the inner `List` is on the heap behind a pointer, giving the enum a known, fixed size.

In Swift, `indirect enum` solves the same problem:

```swift
// Swift
indirect enum List {
    case cons(Int, List)
    case empty
}

let list = List.cons(1, .cons(2, .empty))
```

Swift's `indirect` keyword does the same thing as Rust's `Box` here – it adds heap indirection – but the mechanism is implicit.

## `Rc<T>`: single-threaded reference counting

`Rc<T>` (Reference Counted) provides shared ownership of a heap-allocated value. Multiple `Rc` pointers can point to the same data, and the data is freed when the last `Rc` is dropped. It works by maintaining a reference count, incrementing on clone and decrementing on drop.

```rust
// Rust
use std::rc::Rc;

let a = Rc::new(vec![1, 2, 3]);
let b = Rc::clone(&a); // increment reference count
let c = Rc::clone(&a);

Rc::strong_count(&a); // 3
```

This is directly comparable to Swift's ARC for classes – but with two important restrictions:

1. `Rc` is single-threaded. It cannot be sent across threads.
2. `Rc` provides only immutable access to the data. You cannot mutate through an `Rc` without interior mutability (covered below).

In Swift, ARC is thread-safe by default (using atomic operations) and allows mutation of class properties freely:

```swift
// Swift
class SharedData {
    var items: [Int]
    init(items: [Int]) { self.items = items }
}

let a = SharedData(items: [1, 2, 3])
let b = a // both a and b reference the same object (ARC)
b.items.append(4) // mutation is allowed
```

Rust separates these concerns: `Rc` handles shared ownership, and `RefCell` (discussed below) handles mutability. This makes the trade-offs explicit.

## `Arc<T>`: thread-safe reference counting

`Arc<T>` (Atomically Reference Counted) is the thread-safe counterpart to `Rc<T>`. It uses atomic operations for the reference count, making it safe to share across threads. The API is identical to `Rc`:

```rust
// Rust
use std::sync::Arc;
use std::thread;

fn main() {
    let data = Arc::new(vec![1, 2, 3]);

    let handles: Vec<_> = (0..3)
        .map(|i| {
            let data = Arc::clone(&data);
            thread::spawn(move || {
                println!("Thread {i}: {data:?}");
            })
        })
        .collect();

    for handle in handles {
        handle.join().unwrap();
    }
}
```

`Arc` is the closest equivalent to Swift's default ARC behavior, which provides thread-safe reference counting for shared class instances. The trade-off is that atomic operations are more expensive than non-atomic ones, which is why Rust provides both `Rc` (cheap, single-threaded) and `Arc` (more expensive, thread-safe). In Swift, there is no separate non-atomic reference-counted class model you opt into.

| Concept | Swift | Rust |
|---|---|---|
| Reference counting (general) | ARC (thread-safe reference counting) | `Rc<T>` (non-atomic) or `Arc<T>` (atomic) |
| Thread-safe sharing | Automatic with ARC | `Arc<T>` required |
| Single-threaded sharing | No special case | `Rc<T>` (cheaper) |

## `Cell<T>`: interior mutability for `Copy` types

Rust's borrowing rules normally prevent you from mutating data through a shared reference (`&T`). `Cell<T>` relaxes this rule for `Copy` types by allowing you to get and set the value through a shared reference, with no runtime borrow-checking overhead:

```rust
// Rust
use std::cell::Cell;

let counter = Cell::new(0);

// Even though counter is not mut, we can change its value
counter.set(counter.get() + 1);
counter.set(counter.get() + 1);

counter.get(); // 2
```

The `get()` method requires `T: Copy`, so `Cell` is most commonly used with small value types like integers, booleans, and floats. For non-`Copy` types, `Cell` offers `replace()` and `take()`, but `RefCell` is usually more ergonomic. There is no Swift equivalent because Swift classes already allow mutation of properties through any reference.

## `RefCell<T>`: runtime borrow checking

`RefCell<T>` provides interior mutability for any type, not just `Copy` types. It moves Rust's borrow checking from compile time to runtime: you can borrow the inner value mutably or immutably, but the usual rules (one mutable borrow *or* any number of immutable borrows) are enforced at runtime. Violating the rules causes a panic rather than a compile error.

```rust
// Rust
use std::cell::RefCell;

let data = RefCell::new(vec![1, 2, 3]);

// Immutable borrow
{
    let borrowed = data.borrow();
}

// Mutable borrow
{
    let mut borrowed = data.borrow_mut();
    borrowed.push(4);
}
```

In Swift, mutating a class property requires no special ceremony – the reference always allows mutation:

```swift
// Swift
class Container {
    var items: [Int] = [1, 2, 3]
}

let c = Container()
c.items.append(4) // fine – class references allow mutation
```

Rust's `RefCell` is the closest equivalent to this behavior. The key difference is that `RefCell` panics if you violate borrowing rules at runtime:

```rust
// Rust
use std::cell::RefCell;

let data = RefCell::new(42);

let borrow1 = data.borrow();
// let borrow2 = data.borrow_mut(); // this would panic at runtime!
```

Swift never has this problem because classes do not enforce borrow exclusivity at the language level (though the Swift runtime does check exclusivity for value types).

## The `Rc<RefCell<T>>` pattern

Since `Rc` gives you shared ownership but only immutable access, and `RefCell` gives you interior mutability, combining them gives you shared ownership with mutable access – the Rust equivalent of multiple references to the same mutable Swift class instance:

```rust
// Rust
use std::cell::RefCell;
use std::rc::Rc;

#[derive(Debug)]
struct Document {
    content: String,
}

let doc = Rc::new(RefCell::new(Document {
    content: String::from("Hello"),
}));

// Clone the Rc to create shared ownership
let editor1 = Rc::clone(&doc);
let editor2 = Rc::clone(&doc);

// Both editors can mutate the document
editor1.borrow_mut().content.push_str(", world");
editor2.borrow_mut().content.push_str("!");

doc.borrow(); // Document { content: "Hello, world!" }
```

The Swift equivalent is simply having two variables point to the same class instance:

```swift
// Swift
class Document {
    var content: String = "Hello"
}

let doc = Document()
let editor1 = doc
let editor2 = doc

editor1.content += ", world"
editor2.content += "!"

print(doc.content) // "Hello, world!"
```

`Rc<RefCell<T>>` is more verbose, but it makes the trade-offs visible: you can see that ownership is shared (`Rc`), mutation uses runtime checks (`RefCell`), and this only works on a single thread (`Rc` instead of `Arc`).

## `Weak<T>`: breaking reference cycles

Just like Swift's ARC, Rust's `Rc` and `Arc` can create reference cycles that leak memory. Both languages solve this with weak references.

In Swift, you mark a property as `weak` to create a non-owning reference:

```swift
// Swift
class Node {
    var value: Int
    var next: Node?
    weak var parent: Node?

    init(value: Int) { self.value = value }

    deinit { print("Node \(value) deallocated") }
}

var a: Node? = Node(value: 1)
var b: Node? = Node(value: 2)
a?.next = b
b?.parent = a // weak reference, no retain cycle
a = nil // Node 1 deallocated
b = nil // Node 2 deallocated
```

In Rust, `Rc::downgrade` creates a `Weak<T>` reference that does not increment the strong count:

```rust
// Rust
use std::cell::RefCell;
use std::rc::{Rc, Weak};

#[derive(Debug)]
struct Node {
    value: i32,
    parent: RefCell<Weak<Node>>,
    children: RefCell<Vec<Rc<Node>>>,
}

fn main() {
    let parent = Rc::new(Node {
        value: 1,
        parent: RefCell::new(Weak::new()),
        children: RefCell::new(vec![]),
    });

    let child = Rc::new(Node {
        value: 2,
        parent: RefCell::new(Rc::downgrade(&parent)),
        children: RefCell::new(vec![]),
    });

    parent.children.borrow_mut().push(Rc::clone(&child));

    // Access the parent through the weak reference
    if let Some(p) = child.parent.borrow().upgrade() {
        println!("Child's parent value: {}", p.value);
    }

    println!("Parent strong count: {}", Rc::strong_count(&parent)); // 1
    println!("Child strong count: {}", Rc::strong_count(&child)); // 2
}
```

The `upgrade()` method on `Weak<T>` returns `Option<Rc<T>>` – `Some` if the value still exists, `None` if it has been dropped. This is equivalent to Swift's optional weak reference, which becomes `nil` when the referenced object is deallocated.

| Concept | Swift | Rust |
|---|---|---|
| Weak reference | `weak var` property | `Weak<T>` from `Rc::downgrade` |
| Access weakly-held value | Optional chaining (`parent?.value`) | `weak.upgrade()` returns `Option<Rc<T>>` |
| Unowned (non-zeroing) | `unowned` keyword | Not provided in std; use `Weak` instead |

## Choosing the right smart pointer

Here is a decision guide for choosing among Rust's smart pointers:

- **Single owner, heap allocation needed**: use `Box<T>`.
- **Multiple owners, single thread**: use `Rc<T>`. Add `RefCell<T>` if you need mutation.
- **Multiple owners, multiple threads**: use `Arc<T>`. Add `Mutex<T>` or `RwLock<T>` for mutation (covered in [Chapter 23](../../concurrency/concurrency-and-parallelism/)).
- **Interior mutability for `Copy` types**: use `Cell<T>`.
- **Interior mutability for non-`Copy` types**: use `RefCell<T>`.
- **Breaking reference cycles**: use `Weak<T>`.

For many Rust programs – especially those using ownership and borrowing effectively – you will not need smart pointers at all. They are tools for specific situations where the default ownership model is too restrictive.

## Key differences and gotchas

- **Explicit vs. implicit**: Swift heap-allocates classes automatically; Rust requires you to opt in with `Box`, `Rc`, or `Arc`. This verbosity is intentional – it makes performance characteristics visible.
- **`Rc` is not `Arc`**: using `Rc` across threads is a compile error, not a runtime error. Rust's type system prevents this mistake entirely. In Swift, all reference counting is atomic, so there is no equivalent pitfall.
- **`RefCell` panics at runtime**: unlike most of Rust's safety checks, `RefCell` borrow violations are detected at runtime and cause a panic. Treat `borrow_mut()` with the same caution you would use for force-unwrapping in Swift.
- **No `unowned` equivalent**: Swift has `unowned` references, which are like `weak` but assume the referenced object will outlive the reference (crashing if it does not). Rust does not have a standard library equivalent; use `Weak` and call `upgrade()`.
- **Clone vs. copy**: calling `Rc::clone(&x)` is cheap – it increments the reference count. It does not deep-copy the data. This is the same as assigning a class variable in Swift. However, `clone()` on a non-smart-pointer type may perform a deep copy, so the cost depends on the type.
- **Smart pointers implement `Deref`**: `Box<T>`, `Rc<T>`, and `Arc<T>` all implement the `Deref` trait, so you can call methods on the inner value directly. `my_box.len()` works the same as if you had a direct reference to the value. This is similar to how Swift lets you call methods on a class reference without explicit dereferencing.

## Further reading

- [Smart Pointers](https://doc.rust-lang.org/book/ch15-00-smart-pointers.html): The Rust Programming Language
- [std::boxed::Box](https://doc.rust-lang.org/std/boxed/struct.Box.html): standard library documentation
- [std::rc::Rc](https://doc.rust-lang.org/std/rc/struct.Rc.html): reference-counted pointer
- [std::sync::Arc](https://doc.rust-lang.org/std/sync/struct.Arc.html): atomic reference-counted pointer
- [std::cell](https://doc.rust-lang.org/std/cell/): `Cell` and `RefCell` documentation
- [Interior Mutability](https://doc.rust-lang.org/reference/interior-mutability.html): Rust reference
