---
title: "Appendix A: Syntax Quick Reference"
sidebar:
  order: 100
---

A side-by-side reference for Swift and Rust syntax. This is intended as a quick-lookup resource, not a tutorial – see the relevant chapters for detailed explanations.

## Variables and constants

| Swift | Rust |
|-------|------|
| `let x = 5` | `let x = 5;` |
| `var x = 5` | `let mut x = 5;` |
| `let x: Int = 5` | `let x: i32 = 5;` |
| `lazy var x = compute()` | `LazyCell` / `LazyLock` (depending on whether you need thread safety) |

## Functions

| Swift | Rust |
|-------|------|
| `func greet(name: String) -> String` | `fn greet(name: String) -> String` |
| `func add(_ a: Int, _ b: Int) -> Int` | `fn add(a: i32, b: i32) -> i32` |
| `func log(_ msg: String)` (returns Void) | `fn log(msg: &str)` (returns `()`) |
| `func compute() -> (Int, String)` | `fn compute() -> (i32, String)` |
| Default parameter: `func f(x: Int = 0)` | No default parameters (use builder pattern or `Option`) |

## Closures

| Swift | Rust |
|-------|------|
| `{ (x: Int) -> Int in x + 1 }` | `\|x: i32\| -> i32 { x + 1 }` |
| `{ x in x + 1 }` | `\|x\| x + 1` |
| `{ $0 + 1 }` | No anonymous parameters |
| `@escaping () -> Void` | `impl Fn()` or `Box<dyn Fn()>` |
| `[weak self]` capture list | Borrows captures by default when possible; `move \|\|` forces capture by value |

## Structs

| Swift | Rust |
|-------|------|
| `struct Point { var x: Double; var y: Double }` | `struct Point { x: f64, y: f64 }` |
| Automatic memberwise init | No automatic init – use literal syntax `Point { x, y }` |
| `extension Point { func method() { } }` | `impl Point { fn method(&self) { } }` |
| `static func create() -> Point` | `fn create() -> Point` (in `impl` block, no `self`) |
| `mutating func move_by()` | `fn move_by(&mut self)` |

## Enums

| Swift | Rust |
|-------|------|
| `enum Direction { case north, south }` | `enum Direction { North, South }` |
| `case value(Int)` (associated value) | `Value(i32)` (tuple variant) |
| `case named(x: Int, y: Int)` | `Named { x: i32, y: i32 }` (struct variant) |
| `case coin = 25` (raw value) | Explicit discriminant: `Quarter = 25`; add `#[repr(i32)]` for FFI-safe layout |
| `indirect case` | Wrap in `Box`: `Node(Box<Tree>)` |

## Pattern matching

| Swift | Rust |
|-------|------|
| `switch value { case .a: ... }` | `match value { Enum::A => ... }` |
| `case .a(let x):` | `Enum::A(x) =>` |
| `case .a(let x) where x > 0:` | `Enum::A(x) if x > 0 =>` |
| `case 1...5:` | `1..=5 =>` |
| `default:` | `_ =>` |
| `if case .a(let x) = value { }` | `if let Enum::A(x) = value { }` |
| `guard case .a(let x) = value else { return }` | `let Enum::A(x) = value else { return };` |

## Optionals / Option

| Swift | Rust |
|-------|------|
| `Int?` | `Option<i32>` |
| `nil` | `None` |
| `.some(value)` / just `value` | `Some(value)` |
| `x!` (force unwrap) | `x.unwrap()` |
| `x ?? defaultValue` | `x.unwrap_or(default_value)` |
| `x?.method()` | `x.as_ref().map(\|v\| v.method())` or `if let` |
| `if let x { }` | `if let Some(x) = x { }` |
| `guard let x else { return }` | `let Some(x) = x else { return };` |
| `x.map { $0 + 1 }` | `x.map(\|v\| v + 1)` |
| `x.flatMap { transform($0) }` | `x.and_then(\|v\| transform(v))` |

## Error handling

| Swift | Rust |
|-------|------|
| `func load() throws -> Data` | `fn load() -> Result<Data, Error>` |
| `try load()` | `load()?` |
| `try? load()` | `load().ok()` |
| `try! load()` | `load().unwrap()` |
| `do { try f() } catch { }` | `match f() { Ok(v) => ..., Err(e) => ... }` |
| `throw MyError.notFound` | `return Err(MyError::NotFound)` |
| `catch MyError.notFound { }` | `Err(MyError::NotFound) =>` |
| `Error` protocol | `std::error::Error` trait |

## Generics

| Swift | Rust |
|-------|------|
| `func first<T>(of arr: [T]) -> T?` | `fn first<T>(arr: &[T]) -> Option<&T>` |
| `func eq<T: Equatable>(a: T, b: T) -> Bool` | `fn eq<T: PartialEq>(a: &T, b: &T) -> bool` |
| `where T: Hashable` | `where T: Hash` |
| `some Collection` (opaque type) | `impl Iterator` (in return position) |
| `any Collection` (existential) | `dyn Iterator` (behind `Box` or reference) |

## Protocols / Traits

| Swift | Rust |
|-------|------|
| `protocol Drawable { func draw() }` | `trait Drawable { fn draw(&self); }` |
| `extension Drawable { func draw() { } }` | Default method body in the trait definition |
| `struct Circle: Drawable { }` | `impl Drawable for Circle { }` |
| `associatedtype Item` | `type Item;` (associated type) |
| Protocol inheritance: `protocol A: B { }` | Supertrait: `trait A: B { }` |
| `@objc optional func method()` | No optional methods – use default implementations |

## Access control

| Swift | Rust |
|-------|------|
| `public` | `pub` |
| `internal` (default) | `pub(crate)` (closest match: visible within the crate) |
| `fileprivate` | No exact equivalent |
| `private` | No exact equivalent (closest: default visibility, which is private to the module) |
| `open` | No exact equivalent (Rust has no subclassability distinction) |
| (none) | Default visibility: private to the module |
| (none) | `pub(super)` (visible to the parent module) |

## String interpolation / formatting

| Swift | Rust |
|-------|------|
| `"Hello, \(name)"` | `format!("Hello, {name}")` |
| `print("x = \(x)")` | `println!("x = {x}");` |
| `String(format: "%.2f", value)` | `format!("{value:.2}")` |
| `"\(value, specifier: "%04d")"` | `format!("{value:04}")` |
| `String(describing: obj)` | `format!("{obj:?}")` (Debug) or `format!("{obj}")` (Display) |

## Type casting

| Swift | Rust |
|-------|------|
| `value as! Type` (force cast) | No direct equivalent – Rust does not have class hierarchies |
| `value as? Type` (conditional cast) | Pattern matching or `downcast_ref` on trait objects |
| `value as Type` (guaranteed cast) | `value as Type` (only for primitive numeric conversions) |
| `value is Type` | Pattern matching; `.is::<Type>()` on `Any` |
| `Int(floatValue)` | `float_value as i32` (truncating) |
| `Double(intValue)` | `int_value as f64` or `f64::from(int_value)` |

## Loops

| Swift | Rust |
|-------|------|
| `for item in collection { }` | `for item in collection { }` |
| `for i in 0..<10 { }` | `for i in 0..10 { }` |
| `for i in 0...10 { }` | `for i in 0..=10 { }` |
| `for (i, item) in arr.enumerated() { }` | `for (i, item) in arr.iter().enumerate() { }` |
| `while condition { }` | `while condition { }` |
| `repeat { } while condition` | `loop { /* body */; if !condition { break; } }` |
| `for i in stride(from: 0, to: 10, by: 2)` | `for i in (0..10).step_by(2)` |

## Array / Vec operations

| Swift | Rust |
|-------|------|
| `[Int]()` or `Array<Int>()` | `Vec::<i32>::new()` or `vec![]` |
| `[1, 2, 3]` (literal) | `vec![1, 2, 3]` |
| `arr.append(4)` | `vec.push(4);` |
| `arr.count` | `vec.len()` |
| `arr.isEmpty` | `vec.is_empty()` |
| `arr[0]` | `vec[0]` (panics on out-of-bounds) |
| `arr.first` | `vec.first()` (returns `Option`) |
| `arr.map { $0 + 1 }` | `vec.iter().map(\|x\| x + 1).collect::<Vec<_>>()` |
| `arr.filter { $0 > 2 }` | `vec.iter().filter(\|&&x\| x > 2).collect::<Vec<_>>()` |
| `arr.reduce(0, +)` | `vec.iter().sum::<i32>()` or `.fold(0, \|a, b\| a + b)` |
| `arr.sorted()` | `vec.sort(); vec` or clone and sort |
| `arr.contains(3)` | `vec.contains(&3)` |
| `arr + [4, 5]` | `vec.extend([4, 5]);` |
| Slice: `arr[1...3]` | Slice: `&vec[1..=3]` |

## Dictionary / HashMap operations

| Swift | Rust |
|-------|------|
| `[String: Int]()` | `HashMap::<String, i32>::new()` |
| `["a": 1, "b": 2]` | `HashMap::from([("a", 1), ("b", 2)])` |
| `dict["key"] = value` | `map.insert("key", value);` |
| `dict["key"]` (returns optional) | `map.get("key")` (returns `Option`) |
| `dict.count` | `map.len()` |
| `dict.keys` | `map.keys()` |
| `dict.values` | `map.values()` |
| `dict.removeValue(forKey: "a")` | `map.remove("a")` |
| `dict["key", default: 0] += 1` | `*map.entry("key").or_insert(0) += 1;` |
| `for (k, v) in dict { }` | `for (k, v) in &map { }` |

## Comments

| Swift | Rust |
|-------|------|
| `// line comment` | `// line comment` |
| `/* block comment */` | `/* block comment */` |
| `/// doc comment` | `/// doc comment` (outer) |
| (none) | `//! module-level doc comment` (inner) |
| Markup with `- Parameter x:` etc. | Markdown with `# Examples`, `# Panics`, etc. |

## Attributes / Annotations

| Swift | Rust |
|-------|------|
| `@discardableResult` | `#[must_use]` (inverse – warns if result is unused) |
| `@available(iOS 15, *)` | `#[cfg(target_os = "ios")]` (compile-time only; Rust has no direct equivalent of runtime version checks) |
| `@frozen` | Non-exhaustive is opt-in: `#[non_exhaustive]` |
| `@inlinable` | `#[inline]` |
| `@objc` | `#[no_mangle]` / `extern "C"` |
| `#warning("...")` | `compile_error!("...")` (halts compilation, unlike `#warning` which is non-fatal) or `todo!()` |
| `@testable import` | `#[cfg(test)]` module with `use super::*;` |
| `@MainActor` | No direct equivalent – use runtime-specific mechanisms |
| `Codable` | `#[derive(Serialize, Deserialize)]` (via serde) |
| `Equatable`, `Hashable` | `#[derive(PartialEq, Eq, Hash)]` |
| `CustomStringConvertible` | `#[derive(Debug)]` or manual `impl Display` |
