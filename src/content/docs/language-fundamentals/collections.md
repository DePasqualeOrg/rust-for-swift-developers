---
title: Collections
sidebar:
  order: 9
---

Swift and Rust share the same trio of workhorse collections – dynamic arrays, hash maps, and hash sets – but the details of how they work differ in important ways. Rust also has a pair of types with no direct Swift equivalent: fixed-size arrays that live on the stack and slices that borrow a contiguous region of another collection.

## Dynamic arrays: `Vec<T>` and `Array`

Rust's `Vec<T>` is the equivalent of Swift's `Array<Element>`. Both are growable, heap-allocated, contiguous sequences of values.

### Creation

```swift
// Swift
var numbers: [Int] = [1, 2, 3]
let empty: [String] = []
let repeated = Array(repeating: 0, count: 5)
```

```rust
// Rust
let mut numbers: Vec<i32> = vec![1, 2, 3];
let empty: Vec<String> = Vec::new();
let repeated = vec![0; 5];
```

The `vec![]` macro is the idiomatic way to create a `Vec` with initial values. It plays the same role as Swift's array literal syntax. `Vec::new()` creates an empty vector, just as `[]` does in Swift.

You can also build a `Vec` from a range or an iterator:

```rust
// Rust
let range_vec: Vec<i32> = (1..=5).collect();   // [1, 2, 3, 4, 5]
let from_iter: Vec<i32> = [10, 20, 30].into_iter().collect();
```

### Accessing elements

Both languages provide subscript access, but Rust panics on out-of-bounds access just as Swift does:

```swift
// Swift
let first = numbers[0]       // 1
let maybe = numbers.first    // Optional<Int>
```

```rust
// Rust
let first = numbers[0];         // 1 – panics if empty
let maybe = numbers.first();    // Option<&i32>
```

Notice that `first()` in Rust returns an `Option<&T>` – a reference to the element inside the vector. Swift's `.first` returns an `Optional<Element>` that is a copy of the value (for value types) or a reference (for reference types).

### Mutation

```swift
// Swift
numbers.append(4)
numbers.insert(0, at: 0)
let removed = numbers.remove(at: 2)
numbers[0] = 99
```

```rust
// Rust
numbers.push(4);
numbers.insert(0, 0);
let removed = numbers.remove(2);
numbers[0] = 99;
```

Swift uses `append` and `remove(at:)` with argument labels; Rust uses `push` and `remove` with positional arguments. The naming difference reflects Rust's convention of shorter method names without labels.

### Common methods

```swift
// Swift
numbers.count
numbers.isEmpty
numbers.contains(3)
numbers.sort()
numbers.reverse()
let sorted = numbers.sorted()
```

```rust
// Rust
numbers.len()
numbers.is_empty()
numbers.contains(&3)
numbers.sort();
numbers.reverse();
let mut sorted = numbers.clone();
sorted.sort();
```

A few things stand out. Rust uses `len()` rather than `count`. The `contains` method takes a reference (`&3`) because it compares by borrowing, not by consuming elements. And Rust has no built-in `sorted()` that returns a new vector – you clone and sort in place, or use iterators (covered in the [next chapter on iterators](../iterators/)).

### Capacity and performance

Both `Vec` and `Array` use a growth strategy that amortizes appends to O(1). You can pre-allocate capacity in both languages:

```swift
// Swift
var buffer: [Int] = []
buffer.reserveCapacity(1000)
```

```rust
// Rust
let mut buffer: Vec<i32> = Vec::with_capacity(1000);
```

In Rust, `Vec::with_capacity` allocates memory for 1,000 elements without initializing them. `buffer.len()` is still 0, but `buffer.capacity()` is at least 1,000.

## Fixed-size arrays: `[T; N]`

Rust has a separate type for fixed-size arrays: `[T; N]`, where `N` is a compile-time constant. These live on the stack (unless explicitly boxed) and have no heap allocation.

```rust
// Rust
let rgb: [u8; 3] = [255, 128, 0];
let zeros = [0i32; 10]; // ten zeros
```

Swift does not have a direct equivalent. Swift's `Array` is always heap-allocated and dynamically sized. The closest Swift analog would be a tuple like `(UInt8, UInt8, UInt8)`, but tuples lack the collection API.

Fixed-size arrays in Rust support indexing, iteration, and comparison. The size is part of the type, so `[u8; 3]` and `[u8; 4]` are different types and cannot be assigned to each other:

```rust
// Rust
let a: [i32; 3] = [1, 2, 3];
let b: [i32; 4] = [1, 2, 3, 4];
// a = b; // compile error: mismatched types
```

Fixed-size arrays are useful for data with a known, constant length – pixel components, cryptographic hashes, matrix dimensions, or small lookup tables.

## Slices: `&[T]`

A slice `&[T]` is a borrowed view into a contiguous sequence of `T` values. It consists of a pointer and a length – no ownership, no allocation. Slices can refer to part or all of a `Vec`, a fixed-size array, or another slice.

```rust
// Rust
let numbers = vec![10, 20, 30, 40, 50];
let middle: &[i32] = &numbers[1..4]; // [20, 30, 40]
let all: &[i32] = &numbers;          // the whole vector as a slice
```

Swift's closest equivalent is `ArraySlice`:

```swift
// Swift
let numbers = [10, 20, 30, 40, 50]
let middle = numbers[1..<4] // ArraySlice<Int> containing [20, 30, 40]
```

There is an important difference: Swift's `ArraySlice` retains the original array's indices (so `middle.startIndex` is 1, not 0), while a Rust slice always starts at index 0. This is a common source of confusion for Swift developers.

Slices are the preferred way to pass collections to functions when you only need to read the data. Because they borrow rather than own, they avoid copies and work with any contiguous source:

```rust
// Rust
fn sum(values: &[i32]) -> i32 {
    values.iter().sum()
}

fn main() {
    let v = vec![1, 2, 3];
    let a = [4, 5, 6];

    println!("{}", sum(&v));   // pass a Vec as a slice
    println!("{}", sum(&a));   // pass a fixed-size array as a slice
}
```

This is similar to how you might write a Swift function that accepts `some Sequence<Int>`, except that slices are specific to contiguous memory and carry no protocol witness overhead.

Mutable slices (`&mut [T]`) allow modifying the underlying data:

```rust
// Rust
fn double_all(values: &mut [i32]) {
    for v in values.iter_mut() {
        *v *= 2;
    }
}

fn main() {
    let mut data = vec![1, 2, 3];
    double_all(&mut data);
    println!("{:?}", data); // [2, 4, 6]
}
```

## Hash maps: `HashMap<K, V>` and `Dictionary`

Rust's `HashMap<K, V>` is the equivalent of Swift's `Dictionary<Key, Value>`. Both are unordered collections of key-value pairs with O(1) average-case lookups.

### Creation

```swift
// Swift
var scores: [String: Int] = ["Alice": 10, "Bob": 7]
let empty: [String: Int] = [:]
```

```rust
// Rust
use std::collections::HashMap;

let mut scores: HashMap<&str, i32> = HashMap::from([
    ("Alice", 10),
    ("Bob", 7),
]);
let empty: HashMap<String, i32> = HashMap::new();
```

Unlike `Vec`, `HashMap` is not in the prelude – you must bring it into scope with `use std::collections::HashMap`. There is no built-in macro like `vec![]` for hash maps, but `HashMap::from` accepts an array of tuples.

### Access and insertion

```swift
// Swift
let aliceScore = scores["Alice"]       // Optional<Int>
scores["Charlie"] = 5
scores["Alice"] = nil                  // removes the entry
```

```rust
// Rust
let alice_score = scores.get("Alice");     // Option<&i32>
scores.insert("Charlie", 5);
scores.remove("Alice");
```

Swift overloads subscript for both reading (returns optional) and writing (including deletion via assigning `nil`). Rust separates these into distinct methods: `get` for lookup, `insert` for insertion, and `remove` for deletion.

### The entry API

Rust's `Entry` API provides a concise way to insert a value only if the key is missing – a common pattern that Swift handles with `Dictionary`'s subscript with `default`:

```swift
// Swift
scores["Dave", default: 0] += 1
```

```rust
// Rust
*scores.entry("Dave").or_insert(0) += 1;
```

The `entry` method returns an `Entry` enum that lets you inspect whether the key exists and act accordingly, all without doing two separate lookups.

### Iteration

```swift
// Swift
for (name, score) in scores {
    print("\(name): \(score)")
}
```

```rust
// Rust
for (name, score) in &scores {
    println!("{name}: {score}");
}
```

As with dictionaries in Swift, iteration order is not guaranteed.

### Key requirements

In Swift, dictionary keys must conform to `Hashable`. In Rust, keys must implement both `Hash` and `Eq`. Most primitive types and `String` satisfy these requirements. If you need a custom struct as a key, derive the necessary traits:

```rust
// Rust
#[derive(Hash, Eq, PartialEq)]
struct Point {
    x: i32,
    y: i32,
}
```

## Hash sets: `HashSet<T>` and `Set`

Rust's `HashSet<T>` is equivalent to Swift's `Set<Element>`. It stores unique values with O(1) average-case lookups.

```swift
// Swift
var tags: Set<String> = ["rust", "swift", "wasm"]
tags.insert("go")
tags.contains("rust") // true
```

```rust
// Rust
use std::collections::HashSet;

let mut tags: HashSet<&str> = HashSet::from(["rust", "swift", "wasm"]);
tags.insert("go");
tags.contains("rust"); // true
```

Both languages support the standard set operations:

```swift
// Swift
let a: Set = [1, 2, 3, 4]
let b: Set = [3, 4, 5, 6]

a.union(b)              // {1, 2, 3, 4, 5, 6}
a.intersection(b)       // {3, 4}
a.subtracting(b)        // {1, 2}
a.symmetricDifference(b) // {1, 2, 5, 6}
```

```rust
// Rust
use std::collections::HashSet;

let a: HashSet<i32> = HashSet::from([1, 2, 3, 4]);
let b: HashSet<i32> = HashSet::from([3, 4, 5, 6]);

let union: HashSet<_> = a.union(&b).cloned().collect();
let intersection: HashSet<_> = a.intersection(&b).cloned().collect();
let difference: HashSet<_> = a.difference(&b).cloned().collect();
let symmetric: HashSet<_> = a.symmetric_difference(&b).cloned().collect();
```

The Rust versions return iterators rather than new sets, so you call `.cloned().collect()` to materialize the results. The set operation methods borrow `a` and `b`, so both remain usable. You can also use the operator overloads `&` (intersection), `|` (union), `-` (difference), and `^` (symmetric difference) on `HashSet` references:

```rust
// Rust
let also_union: HashSet<_> = &a | &b;
let also_intersection: HashSet<_> = &a & &b;
```

## Ownership and collections

When you add a value to a collection in Rust, the collection takes ownership of that value. This is the most important difference from Swift for day-to-day programming.

```rust
// Rust
let name = String::from("Alice");
let mut names = Vec::new();
names.push(name);
// println!("{name}"); // compile error: value moved into the vector
```

After `push`, the string has been moved into the vector and `name` is no longer usable. In Swift, `Array.append` copies value types and retains reference types – the original variable remains valid either way.

The same applies to `HashMap` and `HashSet`. If you need to keep using the original value, you can clone it or store references:

```rust
// Rust – cloning
let name = String::from("Alice");
let mut names = Vec::new();
names.push(name.clone());
println!("{name}"); // still valid

// Rust – storing references (requires lifetime management)
let name = String::from("Alice");
let mut names: Vec<&str> = Vec::new();
names.push(&name);
println!("{name}"); // still valid
```

When you remove a value from a collection, ownership transfers back to you:

```rust
// Rust
let mut stack = vec![1, 2, 3];
let top = stack.pop(); // Option<i32> – you now own the value
```

This ownership model means that Rust collections never share mutable state implicitly. Combined with the borrowing rules, this prevents a whole class of bugs that Swift addresses through copy-on-write semantics.

## Key differences and gotchas

- **`Vec` vs `Array` naming**: Rust's `Vec` is Swift's `Array`. Rust's `[T; N]` (fixed-size array) has no Swift equivalent. Be careful not to confuse them.
- **No implicit copying**: adding a value to a Rust collection moves it. Use `.clone()` if you need to keep the original.
- **Imports required**: `HashMap` and `HashSet` must be imported from `std::collections`. `Vec` is in the prelude and needs no import.
- **References in access methods**: many `Vec` and `HashMap` methods return references (`&T`) rather than owned values, since the collection still owns the data.
- **Slice indexing**: Rust slices are always zero-indexed, unlike Swift's `ArraySlice` which preserves original indices.
- **No subscript sugar for maps**: Rust does not overload `[]` for optional access on `HashMap`. Use `get()` for safe lookups and `[]` only when you are certain the key exists (it panics otherwise).
- **`contains` takes a reference**: `vec.contains(&value)` requires passing a reference, not the value itself.

## Further reading

- [`Vec` in the standard library](https://doc.rust-lang.org/std/vec/struct.Vec.html)
- [`HashMap` documentation](https://doc.rust-lang.org/std/collections/struct.HashMap.html)
- [`HashSet` documentation](https://doc.rust-lang.org/std/collections/struct.HashSet.html)
- [The Rust Programming Language – Storing Lists of Values with Vectors](https://doc.rust-lang.org/book/ch08-01-vectors.html)
- [The Rust Programming Language – Storing Keys with Associated Values in Hash Maps](https://doc.rust-lang.org/book/ch08-03-hash-maps.html)
