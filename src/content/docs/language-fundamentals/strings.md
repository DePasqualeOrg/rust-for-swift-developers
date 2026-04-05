---
title: Strings in Depth
sidebar:
  order: 10
---

Strings are one of the first places where Rust's ownership model becomes tangible in everyday code. Both Swift and Rust treat strings as complex, Unicode-aware types rather than simple byte buffers, and both refuse to let you index into a string with an integer. But the way they achieve this differs significantly, and the distinction between owned and borrowed strings in Rust has no direct equivalent in Swift.

## `String` vs `&str`: owned and borrowed

Rust has two primary string types:

- **`String`**: a heap-allocated, growable, owned string. This is the Rust equivalent of Swift's `String`.
- **`&str`** (pronounced "string slice"): a borrowed, immutable view into a sequence of UTF-8 bytes. It consists of a pointer and a length – no allocation, no ownership.

```rust
// Rust
let owned: String = String::from("hello");  // heap-allocated, owned
let borrowed: &str = "hello";               // points to static data, borrowed
```

Every string literal in Rust has type `&str` (specifically `&'static str`, meaning it lives for the entire program). In Swift, every string literal creates a `String` value. This is a fundamental difference: Rust distinguishes between "I own this text" and "I'm just looking at some text that someone else owns."

The relationship between `String` and `&str` is analogous to `Vec<T>` and `&[T]`. A `String` is essentially a `Vec<u8>` that is guaranteed to contain valid UTF-8. A `&str` is a `&[u8]` with the same guarantee.

### Converting between `String` and `&str`

Going from `String` to `&str` is cheap – it is just borrowing:

```rust
// Rust
let owned = String::from("hello");
let borrowed: &str = &owned;         // borrow the whole string
let slice: &str = &owned[0..3];      // borrow a substring: "hel"
```

Going from `&str` to `String` requires allocation – you are creating an owned copy:

```rust
// Rust
let borrowed: &str = "hello";
let owned: String = borrowed.to_string();    // one way
let also_owned: String = String::from(borrowed); // another way
let third: String = borrowed.to_owned();     // yet another
```

All three approaches produce the same result. `to_string()` is the most common in practice.

### Which to use in function signatures

A function that only needs to read a string should accept `&str`:

```rust
// Rust
fn greet(name: &str) {
    println!("Hello, {name}!");
}

fn main() {
    let owned = String::from("Alice");
    greet(&owned);       // String coerces to &str automatically
    greet("Bob");        // &str passed directly
}
```

A function that needs to store or return an owned string should use `String`:

```rust
// Rust
fn make_greeting(name: &str) -> String {
    format!("Hello, {name}!")
}
```

This is similar to how a Swift function might accept `some StringProtocol` for read-only access and return `String` when creating new strings, but the distinction is sharper in Rust because it maps directly to ownership.

## UTF-8 encoding

Rust strings are always valid UTF-8. Swift's `String` also uses UTF-8 as its internal storage (since Swift 5), so the two languages are aligned on encoding. However, the APIs they expose on top of that encoding differ.

In Swift, you access different views of a string's contents:

```swift
// Swift
let text = "cafe\u{0301}" // decomposed form of "café"
text.count               // 4 (grapheme clusters)
text.unicodeScalars.count // 5 (Unicode scalars)
text.utf8.count          // 6 (UTF-8 bytes)
text.utf16.count         // 5 (UTF-16 code units)
```

In Rust, you get a similar set of views through methods on `str`:

```rust
// Rust
let text = "cafe\u{0301}";
text.chars().count()     // 5 (Unicode scalar values, like Swift's unicodeScalars)
text.bytes().count()     // 6 (UTF-8 bytes, like Swift's utf8)
text.len()               // 6 (byte length, not character count)
```

Rust does not have a built-in grapheme cluster view. The `chars()` iterator yields Unicode scalar values (Rust's `char` type), which is equivalent to Swift's `unicodeScalars` view, not its default character view. For grapheme cluster segmentation, you need an external crate like [`unicode-segmentation`](https://crates.io/crates/unicode-segmentation).

The `len()` method on a Rust string returns the byte length, not the number of characters. This is a common source of confusion for newcomers. Swift's `count` returns the grapheme cluster count, which is the most linguistically meaningful measure but the most expensive to compute.

## Why you cannot index by integer

Neither Swift nor Rust lets you write `text[2]` to get the third character. The reasons are similar – characters are variable-width in both UTF-8 and grapheme clusters – but the mechanics differ.

In Swift:

```swift
// Swift
let text = "hello"
// text[2] // compile error
let index = text.index(text.startIndex, offsetBy: 2)
let ch = text[index] // "l" (a Character, i.e., grapheme cluster)
```

In Rust:

```rust
// Rust
let text = "hello";
// text[2] // compile error – cannot index `str` with `usize`
let ch = text.chars().nth(2); // Some('l') – a Unicode scalar value
```

Both languages make the O(n) cost explicit. Swift does it through its `String.Index` type; Rust does it by requiring you to use an iterator.

You can index into the byte representation of a Rust string using a range, but this creates a `&str` slice and will panic at runtime if the range does not fall on a character boundary:

```rust
// Rust
let text = "hello";
let slice: &str = &text[0..3]; // "hel" – safe because ASCII
println!("{slice}");

let emoji = "\u{1F600}hello"; // starts with a 4-byte emoji
// let bad = &emoji[0..1]; // panics: byte index 1 is not a char boundary
```

## String slicing

Rust string slices use byte ranges, not character ranges:

```rust
// Rust
let greeting = "Hello, world!";
let hello: &str = &greeting[0..5];     // "Hello"
let world: &str = &greeting[7..12];    // "world"
```

This is efficient – it is O(1) pointer arithmetic – but dangerous with multi-byte characters. Swift's `Substring` type serves a similar role but uses `String.Index` values that are always valid:

```swift
// Swift
let greeting = "Hello, world!"
let start = greeting.index(greeting.startIndex, offsetBy: 7)
let end = greeting.index(start, offsetBy: 5)
let world = greeting[start..<end] // "world" (a Substring)
```

## Common operations

### Concatenation

```swift
// Swift
let full = "Hello" + ", " + "world!"
var greeting = "Hello"
greeting += ", world!"
greeting.append("!")
```

```rust
// Rust
let full = format!("{}, {}!", "Hello", "world");
let mut greeting = String::from("Hello");
greeting.push_str(", world!");
greeting.push('!'); // push a single char
```

Rust's `+` operator works on strings, but it has an asymmetric signature – the left operand is consumed (moved) and the right must be a `&str`:

```rust
// Rust
let hello = String::from("Hello");
let full = hello + ", world!"; // hello is moved; full owns the result
// println!("{hello}"); // compile error: hello was moved
```

Because of this, `format!` is usually preferred for combining strings – it is clearer and does not consume any of its arguments.

### Formatting with `format!`

The `format!` macro is Rust's equivalent of Swift's string interpolation:

```swift
// Swift
let name = "Alice"
let age = 30
let message = "Name: \(name), Age: \(age)"
```

```rust
// Rust
let name = "Alice";
let age = 30;
let message = format!("Name: {name}, Age: {age}");
```

`format!` returns a new `String`. The inline variable syntax (`{name}`) works for local variables; you can also use positional (`{0}`) or named arguments with formatting options:

```rust
// Rust
let pi = std::f64::consts::PI;
let formatted = format!("{pi:.4}");         // "3.1416"
let padded = format!("{:>10}", "right");    // "     right"
let hex = format!("{:#x}", 255);            // "0xff"
```

### Searching and replacing

```swift
// Swift
"hello world".contains("world")     // true
"hello world".replacingOccurrences(of: "world", with: "Rust") // "hello Rust"
"hello world".hasPrefix("hello")    // true
"hello world".hasSuffix("world")    // true
```

```rust
// Rust
"hello world".contains("world")           // true
"hello world".replace("world", "Rust")    // "hello Rust" (returns String)
"hello world".starts_with("hello")        // true
"hello world".ends_with("world")          // true
```

### Splitting and joining

```swift
// Swift
let parts = "a,b,c".split(separator: ",") // [Substring]
let joined = parts.joined(separator: "-") // "a-b-c"
```

```rust
// Rust
let parts: Vec<&str> = "a,b,c".split(',').collect();
let joined = parts.join("-"); // "a-b-c"
```

Rust's `split` returns an iterator, so you call `.collect()` to gather the results into a `Vec<&str>`. The slices borrow from the original string – no allocation happens until you collect.

### Trimming whitespace

```swift
// Swift
" hello ".trimmingCharacters(in: .whitespaces) // "hello"
```

```rust
// Rust
" hello ".trim() // "hello" (returns &str)
```

Rust also provides `trim_start()` and `trim_end()` for one-sided trimming. These methods return `&str` slices – they do not allocate.

### Case conversion

```swift
// Swift
"hello".uppercased() // "HELLO"
"HELLO".lowercased() // "hello"
```

```rust
// Rust
"hello".to_uppercase() // "HELLO" (returns String)
"HELLO".to_lowercase() // "hello" (returns String)
```

## String literals and raw strings

Regular string literals work the same way in both languages:

```rust
// Rust
let simple = "Hello, world!";
let escaped = "She said \"hello\"";
let newline = "line one\nline two";
let unicode = "\u{1F600}"; // emoji
```

Rust raw strings use `r#"..."#` to avoid escaping:

```rust
// Rust
let raw = r#"She said "hello" and it was fine"#;
let regex = r#"\d{3}-\d{4}"#;
```

You can add more `#` symbols if your content contains `"#`:

```rust
// Rust
let nested = r##"Contains a "# sequence"##;
```

Swift uses `#"..."#` for a similar purpose (extended delimiters):

```swift
// Swift
let raw = #"She said "hello" and it was fine"#
let regex = #"\d{3}-\d{4}"#
```

### Multiline strings

```swift
// Swift
let multi = """
    Line one
    Line two
    """
```

```rust
// Rust
let multi = "\
Line one
Line two";
```

Rust does not have a dedicated multiline string literal like Swift's triple-quoted syntax. Regular string literals can span multiple lines. A backslash at the end of a line suppresses the newline and any leading whitespace on the next line, which is useful for formatting long strings in code.

### Byte strings

Rust has byte string literals (`b"..."`) that produce `&[u8]` rather than `&str`. These are useful when working with binary protocols or ASCII-only data:

```rust
// Rust
let bytes: &[u8] = b"hello"; // [104, 101, 108, 108, 111]
let byte: u8 = b'A';         // single byte literal: 65
```

Swift does not have a direct equivalent. You would use `Array("hello".utf8)` or a `[UInt8]` literal to achieve something similar.

## Key differences and gotchas

- **Two string types**: Rust's `String`/`&str` distinction has no Swift equivalent. Learn to think of `&str` as the default for function parameters and `String` as the default when you need ownership.
- **`len()` is byte length**: `"cafe\u{0301}".len()` returns 6 (bytes), not 4 or 5. Use `.chars().count()` for scalar count, but remember that there is no built-in grapheme cluster count.
- **Indexing panics**: `&s[0..n]` panics if the range does not land on a UTF-8 character boundary. Always validate or use `char_indices()` to find safe boundaries.
- **`+` moves the left operand**: `let c = a + &b;` consumes `a`. Use `format!` when you want to combine strings without consuming any of them.
- **No grapheme clusters**: Rust's `char` is a Unicode scalar value (4 bytes), not a grapheme cluster. For user-perceived characters, use the `unicode-segmentation` crate.
- **String literals are `&str`**: in Rust, `"hello"` is a `&str`, not a `String`. To get an owned `String`, write `String::from("hello")` or `"hello".to_string()`.
- **Deref coercion**: a `&String` automatically coerces to `&str`, so you can pass a `&String` anywhere a `&str` is expected. This is why accepting `&str` in function signatures is idiomatic – it works with both types.

## Further reading

- [The Rust Programming Language – Storing UTF-8 Encoded Text with Strings](https://doc.rust-lang.org/book/ch08-02-strings.html)
- [`String` in the standard library](https://doc.rust-lang.org/std/string/struct.String.html)
- [Primitive type `str`](https://doc.rust-lang.org/std/primitive.str.html)
- [`unicode-segmentation` crate](https://crates.io/crates/unicode-segmentation): grapheme cluster support
- [Rust by Example – Strings](https://doc.rust-lang.org/rust-by-example/std/str.html)
