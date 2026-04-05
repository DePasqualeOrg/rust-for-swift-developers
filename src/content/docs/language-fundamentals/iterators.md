---
title: Iterators and Functional Patterns
sidebar:
  order: 11
---

Swift and Rust both support a rich set of functional-style operations on sequences – `map`, `filter`, `reduce`, `flatMap`, and more. The underlying abstractions are similar: both languages define a protocol (Swift) or trait (Rust) that types implement to produce values one at a time. But Rust's iterator model has a few distinctive properties that will change how you think about data pipelines: all adaptors are lazy by default, ownership determines which iterator method you call, and collecting results requires an explicit type annotation.

## The `Iterator` trait and Swift's `Sequence`/`IteratorProtocol`

In Swift, the foundation is two protocols:

```swift
// Swift
protocol IteratorProtocol {
    associatedtype Element
    mutating func next() -> Element?
}

protocol Sequence {
    associatedtype Iterator: IteratorProtocol
    func makeIterator() -> Iterator
}
```

In Rust, a single trait covers both roles:

```rust
// Rust
trait Iterator {
    type Item;
    fn next(&mut self) -> Option<Self::Item>;
}
```

Rust's `Iterator` trait is both the protocol for producing values and the gateway to all the adaptor methods. There is no separate `Sequence`-like trait – if a type implements `Iterator`, it gets `map`, `filter`, `fold`, and dozens of other methods for free.

## Three ways to iterate: `iter()`, `iter_mut()`, `into_iter()`

In Swift, iterating over a collection with `for...in` gives you each element by value (for value types) or by reference (for reference types). Swift's copy-on-write semantics mean you rarely think about whether iteration consumes the collection.

In Rust, ownership matters. Collections provide three iterator methods:

- **`iter()`**: borrows each element as `&T`. The collection remains usable afterward.
- **`iter_mut()`**: borrows each element as `&mut T`. You can modify elements in place.
- **`into_iter()`**: takes ownership of the collection, yielding owned `T` values. The collection is consumed.

```rust
// Rust
let names = vec!["Alice".to_string(), "Bob".to_string(), "Carol".to_string()];

// Borrow: names is still usable after this loop
for name in names.iter() {
    println!("{name}"); // name is &String
}

// Consume: names is moved and cannot be used after this loop
for name in names.into_iter() {
    println!("{name}"); // name is String (owned)
}
// println!("{:?}", names); // compile error: names was moved
```

When you write `for item in &collection`, Rust calls `iter()`. When you write `for item in &mut collection`, it calls `iter_mut()`. And `for item in collection` calls `into_iter()`, consuming the collection:

```rust
// Rust
let mut numbers = vec![1, 2, 3];

for n in &numbers { /* n is &i32 */ }         // sugar for numbers.iter()
for n in &mut numbers { /* n is &mut i32 */ } // sugar for numbers.iter_mut()
for n in numbers { /* n is i32 */ }           // sugar for numbers.into_iter()
```

This three-way split has no Swift equivalent. It is a direct consequence of Rust's ownership model, and it becomes natural quickly.

## Iterator adaptors (lazy transformations)

Iterator adaptors transform an iterator into another iterator without consuming any elements. They are lazy – no work happens until you consume the result. This is how all adaptors work in Rust, whereas in Swift, most operations on `Array` are eager (you need `.lazy` for deferred evaluation).

### `map`

```swift
// Swift
let doubled = [1, 2, 3].map { $0 * 2 } // [2, 4, 6]
```

```rust
// Rust
let doubled: Vec<i32> = [1, 2, 3].iter().map(|x| x * 2).collect();
```

### `filter`

```swift
// Swift
let evens = [1, 2, 3, 4, 5].filter { $0 % 2 == 0 } // [2, 4]
```

```rust
// Rust
let evens: Vec<&i32> = [1, 2, 3, 4, 5].iter().filter(|x| *x % 2 == 0).collect();
```

Note that `filter` receives `&&i32` (a reference to the iterator's item, which is already a reference), so you can dereference with `**x` to get the `i32` value, or use pattern matching: `.filter(|&&x| x % 2 == 0)`. A single `*x` also works in comparisons thanks to auto-deref.

### `flat_map`

Equivalent to Swift's `flatMap` – maps each element to an iterator and flattens the results:

```swift
// Swift
let words = ["hello world", "foo bar"].flatMap { $0.split(separator: " ") }
// ["hello", "world", "foo", "bar"]
```

```rust
// Rust
let words: Vec<&str> = ["hello world", "foo bar"]
    .iter()
    .flat_map(|s| s.split_whitespace())
    .collect();
```

### `enumerate`

Pairs each element with its index:

```swift
// Swift
for (index, value) in ["a", "b", "c"].enumerated() {
    print("\(index): \(value)")
}
```

```rust
// Rust
for (index, value) in ["a", "b", "c"].iter().enumerate() {
    println!("{index}: {value}");
}
```

### `zip`

Combines two iterators into pairs, stopping at the shorter one:

```swift
// Swift
let pairs = Array(zip([1, 2, 3], ["a", "b", "c"])) // [(1, "a"), (2, "b"), (3, "c")]
```

```rust
// Rust
let pairs: Vec<_> = [1, 2, 3].iter().zip(["a", "b", "c"].iter()).collect();
// [(&1, &"a"), (&2, &"b"), (&3, &"c")]
```

### `take` and `skip`

```swift
// Swift
let first_three = Array([1, 2, 3, 4, 5].prefix(3))   // [1, 2, 3]
let after_two = Array([1, 2, 3, 4, 5].dropFirst(2))   // [3, 4, 5]
```

```rust
// Rust
let first_three: Vec<&i32> = [1, 2, 3, 4, 5].iter().take(3).collect();
let after_two: Vec<&i32> = [1, 2, 3, 4, 5].iter().skip(2).collect();
```

### `chain`

Concatenates two iterators:

```rust
// Rust
let combined: Vec<i32> = [1, 2].iter()
    .chain([3, 4].iter())
    .cloned()
    .collect();
// [1, 2, 3, 4]
```

Swift achieves this with `Array(a) + Array(b)`, or lazily with `[a, b].joined()`, though there is no built-in `.chain` method on `Sequence`.

### Chaining multiple adaptors

Because adaptors are lazy, you can chain them freely without creating intermediate collections:

```rust
// Rust
let result: Vec<String> = (1..=20)
    .filter(|x| x % 3 == 0)
    .map(|x| format!("{x} is divisible by 3"))
    .take(3)
    .collect();

// ["3 is divisible by 3", "6 is divisible by 3", "9 is divisible by 3"]
```

This processes each element through the full pipeline before moving to the next – no intermediate `Vec` is allocated. In Swift, you would need `.lazy` on the collection to get the same behavior:

```swift
// Swift
let result = (1...20)
    .lazy
    .filter { $0 % 3 == 0 }
    .map { "\($0) is divisible by 3" }
    .prefix(3)
let array = Array(result) // forces evaluation
```

## Consuming adaptors

Consuming adaptors drive the iterator to completion and produce a final value. Once called, the iterator is exhausted.

### `collect`

The most important consuming adaptor. It gathers an iterator's output into a collection. The target type is inferred from context or specified explicitly:

```rust
// Rust
let v: Vec<i32> = (1..=5).collect();
let s: String = ['h', 'e', 'l', 'l', 'o'].iter().collect();
```

When the target type cannot be inferred, you use the turbofish syntax:

```rust
// Rust
let v = (1..=5).collect::<Vec<i32>>();
let v = (1..=5).collect::<Vec<_>>(); // let Rust infer the element type
```

The `::<>` syntax (nicknamed "turbofish" for its resemblance to a fish) provides explicit type parameters to a generic function or method. You can use `_` for type parameters that Rust can figure out on its own.

`collect` can produce any type that implements `FromIterator`, not just `Vec`. You can collect into a `String`, a `HashSet`, a `HashMap`, a `BTreeMap`, or even a `Result`:

```rust
// Rust
use std::collections::HashMap;

let map: HashMap<&str, i32> = vec![("a", 1), ("b", 2)]
    .into_iter()
    .collect();

// Collecting Results: stops at the first Err
let results: Result<Vec<i32>, _> = vec!["1", "2", "three"]
    .iter()
    .map(|s| s.parse::<i32>())
    .collect();
// Err(ParseIntError { ... })
```

### `fold` and `reduce`

Both languages offer `reduce`. Rust also provides `fold`, which takes an initial accumulator value:

```swift
// Swift
let sum = [1, 2, 3, 4].reduce(0, +) // 10
```

```rust
// Rust
let sum = [1, 2, 3, 4].iter().fold(0, |acc, x| acc + x); // 10
```

Rust's `reduce` has no initial value – it uses the first element as the seed and returns `Option` (in case the iterator is empty):

```rust
// Rust
let sum = [1, 2, 3, 4].iter().copied().reduce(|acc, x| acc + x);
// Some(10)
```

### `sum` and `product`

Shorthand for common fold operations:

```rust
// Rust
let total: i32 = [1, 2, 3, 4].iter().sum();       // 10
let factorial: i32 = (1..=5).product();             // 120
```

The type annotation on the binding (`: i32`) is required because `sum` and `product` are generic over the output type.

### `count`

Returns the number of elements:

```rust
// Rust
let n = (1..=100).filter(|x| x % 7 == 0).count(); // 14
```

### `any` and `all`

Short-circuiting boolean queries:

```swift
// Swift
[1, 2, 3].contains(where: { $0 > 2 })  // true
[1, 2, 3].allSatisfy { $0 > 0 }        // true
```

```rust
// Rust
[1, 2, 3].iter().any(|&x| x > 2)   // true
[1, 2, 3].iter().all(|&x| x > 0)   // true
```

### `find`

Returns the first element matching a predicate:

```swift
// Swift
let first_even = [1, 3, 4, 6].first(where: { $0 % 2 == 0 }) // Optional(4)
```

```rust
// Rust
let first_even = [1, 3, 4, 6].iter().find(|&&x| x % 2 == 0); // Some(&4)
```

### `min` and `max`

```rust
// Rust
let smallest = [3, 1, 4, 1, 5].iter().min(); // Some(&1)
let largest = [3, 1, 4, 1, 5].iter().max();  // Some(&5)
```

Both return `Option` because the iterator might be empty.

## Creating custom iterators

In Swift, you conform to `IteratorProtocol` and `Sequence`. In Rust, you implement the `Iterator` trait:

```swift
// Swift
struct Countdown: Sequence, IteratorProtocol {
    var current: Int

    mutating func next() -> Int? {
        guard current > 0 else { return nil }
        defer { current -= 1 }
        return current
    }
}

for n in Countdown(current: 3) {
    print(n) // 3, 2, 1
}
```

```rust
// Rust
struct Countdown {
    current: i32,
}

impl Countdown {
    fn new(start: i32) -> Self {
        Countdown { current: start }
    }
}

impl Iterator for Countdown {
    type Item = i32;

    fn next(&mut self) -> Option<Self::Item> {
        if self.current > 0 {
            let value = self.current;
            self.current -= 1;
            Some(value)
        } else {
            None
        }
    }
}

fn main() {
    for n in Countdown::new(3) {
        println!("{n}"); // 3, 2, 1
    }
}
```

Once you implement `next`, you get all the adaptor methods (`map`, `filter`, `take`, `fold`, etc.) for free. You can also override default implementations like `size_hint` or `nth` for better performance when the iterator's length or random access pattern is known.

### Quick iterators with `std::iter`

For simple cases, you can avoid defining a struct entirely:

```rust
// Rust
use std::iter;

// Repeat a value forever
let ones = iter::repeat(1);
let first_five: Vec<i32> = ones.take(5).collect(); // [1, 1, 1, 1, 1]

// Generate values from a closure
let powers_of_two = iter::successors(Some(1u64), |&prev| Some(prev * 2));
let first_ten: Vec<u64> = powers_of_two.take(10).collect();
// [1, 2, 4, 8, 16, 32, 64, 128, 256, 512]

// Create from a function
let mut count = 0;
let counter = iter::from_fn(move || {
    count += 1;
    if count <= 5 { Some(count) } else { None }
});
let nums: Vec<i32> = counter.collect(); // [1, 2, 3, 4, 5]
```

## Lazy evaluation

All iterator adaptors in Rust are lazy. This means calling `.map(...)` or `.filter(...)` does nothing on its own – it returns a new iterator struct that will apply the transformation when consumed. Nothing happens until you call a consuming adaptor like `collect`, `for_each`, `fold`, or use a `for` loop.

```rust
// Rust
let iter = [1, 2, 3].iter().map(|x| {
    println!("processing {x}");
    x * 2
});
// Nothing is printed yet

let result: Vec<_> = iter.collect();
// Now "processing 1", "processing 2", "processing 3" are printed
```

This is the default in Rust, while Swift's standard collection methods are eager by default:

```swift
// Swift – eager (processes all elements immediately)
let result = [1, 2, 3].map { $0 * 2 } // [2, 4, 6], evaluated now

// Swift – lazy (deferred, like Rust's default)
let result = [1, 2, 3].lazy.map { $0 * 2 }
```

The practical benefit of laziness is efficiency. When you chain adaptors and then take only a few elements, Rust only processes what is needed:

```rust
// Rust
let first_match = (0..1_000_000)
    .map(|x| x * x)
    .filter(|&x| x % 7 == 0 && x % 11 == 0)
    .next();
// Stops as soon as it finds the first match – does not compute all 1,000,000 squares
```

## Key differences and gotchas

- **Lazy by default**: Rust iterator adaptors are lazy. If you call `.map(...)` and never consume the result, the closure never runs. The compiler will warn you about unused iterators.
- **Three iterator methods**: `iter()` borrows, `iter_mut()` borrows mutably, `into_iter()` consumes. Choose based on whether you need to read, modify, or take ownership of elements.
- **`collect` needs a type**: the compiler cannot infer what collection type you want. Provide a type annotation on the binding or use the turbofish syntax (`.collect::<Vec<_>>()`).
- **Double references in `filter`**: when filtering an iterator of references, the closure receives `&&T`. Use pattern matching (`|&&x|`) or dereference (`|x| *x`) to access the value.
- **No free `sorted()` method**: Rust iterators do not have a built-in `sorted()` adaptor in the standard library. Collect into a `Vec` and call `.sort()`, or use the `itertools` crate which adds `.sorted()`.
- **`for_each` vs `for` loops**: `iter.for_each(|x| ...)` is a consuming adaptor equivalent to a `for` loop. Prefer `for` loops when you need `break`, `continue`, or `return` – closures cannot use these to control the outer function.
- **Ownership in closures**: closures passed to `map`, `filter`, etc. follow Rust's normal closure capture rules. If you need to move values into a closure, use the `move` keyword.

## Further reading

- [The Rust Programming Language – Processing a Series of Items with Iterators](https://doc.rust-lang.org/book/ch13-02-iterators.html)
- [`Iterator` trait documentation](https://doc.rust-lang.org/std/iter/trait.Iterator.html)
- [`std::iter` module](https://doc.rust-lang.org/std/iter/): helper functions and types
- [`itertools` crate](https://docs.rs/itertools/latest/itertools/): additional iterator adaptors not in the standard library
- [Rust by Example – Iterator](https://doc.rust-lang.org/rust-by-example/trait/iter.html)
