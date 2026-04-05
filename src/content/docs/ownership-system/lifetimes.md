---
title: Lifetimes
sidebar:
  order: 14
---

If you have been reading the previous two chapters, you have seen Rust's ownership and borrowing rules prevent use-after-free bugs and data races at compile time. But there is a subtlety that ownership and borrowing alone do not fully address: how does the compiler know that a reference is still valid? The answer is *lifetimes*.

A lifetime is not how long a value lives. It is the span of code during which a reference is guaranteed to be valid. Every reference in Rust has a lifetime, and the compiler checks that no reference outlives the data it points to. Most of the time, the compiler infers lifetimes automatically, and you never write them. When it cannot, you add lifetime annotations to help it understand the relationships between references.

Swift has no equivalent concept. ARC keeps objects alive for as long as any reference exists, so a Swift reference can never dangle – but this comes at the cost of runtime reference counting. Rust achieves the same safety guarantee at compile time, and lifetimes are how it does it.

## Why lifetimes exist

Consider this function that returns the longer of two string slices:

```rust
// Rust – does not compile without lifetime annotations
fn longest(x: &str, y: &str) -> &str {
    if x.len() >= y.len() {
        x
    } else {
        y
    }
}
```

The compiler rejects this:

```
error[E0106]: missing lifetime specifier
 --> src/main.rs:1:33
  |
1 | fn longest(x: &str, y: &str) -> &str {
  |               ----     ----      ^ expected named lifetime parameter
  |
  = help: this function's return type contains a borrowed value,
          but the signature does not say whether it is borrowed from `x` or `y`
```

The problem is that the compiler does not know whether the returned reference comes from `x` or `y`. It needs to know, because the returned reference must not outlive whichever input it came from. If the caller drops one of the inputs while still holding the returned reference, that reference would dangle.

In Swift, this problem does not arise. Strings are value types, so `longest` would return a copy. And if you were working with class references, ARC would keep the object alive. But in Rust, returning a reference means you must tell the compiler how the output's validity relates to the inputs.

## Lifetime annotations

Lifetime annotations do not change how long any value lives. They describe the relationships between the lifetimes of references so the compiler can verify that everything is valid. Annotations use the syntax `'a` (an apostrophe followed by a lowercase name, by convention starting with `a`):

```rust
// Rust
fn longest<'a>(x: &'a str, y: &'a str) -> &'a str {
    if x.len() >= y.len() {
        x
    } else {
        y
    }
}

fn main() {
    let string1 = String::from("long string");
    let result;
    {
        let string2 = String::from("xyz");
        result = longest(&string1, &string2);
        println!("The longest string is: {result}");
    }
}
```

The annotation `'a` says: "the returned reference will be valid for as long as *both* `x` and `y` are valid." More precisely, `'a` represents the shorter of the two input lifetimes – the overlap where both references are guaranteed valid.

This compiles because `result` is used (in the `println!`) while both `string1` and `string2` are still alive. But if we tried to use `result` after `string2` is dropped, the compiler would catch it:

```rust
// Rust – does not compile
fn longest<'a>(x: &'a str, y: &'a str) -> &'a str {
    if x.len() >= y.len() {
        x
    } else {
        y
    }
}

fn main() {
    let string1 = String::from("long string");
    let result;
    {
        let string2 = String::from("xyz");
        result = longest(&string1, &string2);
    } // string2 is dropped here

    // println!("{result}"); // error: string2 does not live long enough
}
```

The compiler reports that `string2` does not live long enough because `result` might hold a reference to it, and that reference would be used after `string2`'s scope ends.

### Reading lifetime annotations

Think of `fn longest<'a>(x: &'a str, y: &'a str) -> &'a str` as a contract: "given two string slices that are both valid for at least the lifetime `'a`, I will return a string slice that is also valid for `'a`." The compiler then checks every call site to make sure this contract holds.

You are not telling the compiler how long things live – you are telling it which references are related to each other. The compiler figures out the actual durations from the code.

## When only one input matters

If the return value always comes from one specific input, you only need to annotate that relationship:

```rust
// Rust
fn first_word<'a>(s: &'a str) -> &'a str {
    match s.find(' ') {
        Some(pos) => &s[..pos],
        None => s,
    }
}

fn main() {
    let sentence = String::from("hello world");
    let word = first_word(&sentence);
    println!("{word}");
}
```

Here there is only one input reference, so the lifetime relationship is straightforward: the output is derived from the input and cannot outlive it.

## Lifetime elision rules

You may have noticed that many functions with references do not have lifetime annotations:

```rust
// Rust – no lifetime annotations needed
fn first_char(s: &str) -> &str {
    &s[..1]
}

fn main() {
    let s = String::from("hello");
    println!("{}", first_char(&s));
}
```

This compiles because the Rust compiler applies *lifetime elision rules* – a set of patterns where the lifetimes are so obvious that requiring annotations would be pure noise. The compiler infers them automatically.

The three elision rules are:

1. **Each input reference gets its own lifetime parameter.** A function with one reference parameter gets one lifetime `'a`; a function with two gets `'a` and `'b`; and so on. `fn foo(x: &str, y: &str)` becomes `fn foo<'a, 'b>(x: &'a str, y: &'b str)`.

2. **If there is exactly one input lifetime, it is assigned to all output references.** `fn foo(x: &str) -> &str` becomes `fn foo<'a>(x: &'a str) -> &'a str`. This covers the common case where a function takes one reference and returns something derived from it.

3. **If one of the parameters is `&self` or `&mut self`, the lifetime of `self` is assigned to all output references.** This covers methods that return references to data owned by the struct.

If after applying these rules the compiler still cannot determine all output lifetimes, it reports an error and you must add annotations explicitly. The `longest` function from earlier fails elision because it has two input lifetimes and the compiler does not know which one the output should use.

### Elision in practice

Most functions fall into patterns covered by elision, which is why you can write a lot of Rust without ever typing a lifetime annotation. Here are examples of each rule:

```rust
// Rust

// Rule 1 only (no output references)
fn print_both(a: &str, b: &str) {
    println!("{a} {b}");
}

// Rules 1 and 2 (one input, one output)
fn trim_start(s: &str) -> &str {
    s.trim_start()
}

// Rules 1 and 3 (method returning a reference)
struct Document {
    content: String,
}

impl Document {
    fn title(&self) -> &str {
        match self.content.find('\n') {
            Some(pos) => &self.content[..pos],
            None => &self.content,
        }
    }
}

fn main() {
    print_both("hello", "world");

    let trimmed = trim_start("   hello");
    println!("{trimmed}");

    let doc = Document {
        content: String::from("Title\nBody text here"),
    };
    println!("{}", doc.title());
}
```

## Lifetimes in struct definitions

When a struct holds a reference, it must declare the lifetime of that reference. This tells the compiler that instances of the struct cannot outlive the data being referenced:

```rust
// Rust
struct Highlight<'a> {
    text: &'a str,
    start: usize,
    end: usize,
}

impl<'a> Highlight<'a> {
    fn content(&self) -> &str {
        &self.text[self.start..self.end]
    }
}

fn main() {
    let source = String::from("The quick brown fox");
    let highlight = Highlight {
        text: &source,
        start: 4,
        end: 9,
    };
    println!("Highlighted: '{}'", highlight.content()); // "quick"
}
```

The `'a` on `Highlight<'a>` means: "a `Highlight` holds a reference to a string slice, and the `Highlight` cannot outlive that string slice." If you tried to use the `Highlight` after dropping the source `String`, the compiler would catch it.

In the `impl` block, the method `content` returns `&str` without explicit annotations because elision rule 3 applies – `&self` provides the output lifetime.

### Structs with multiple lifetimes

A struct can have multiple lifetime parameters when it holds references to different sources:

```rust
// Rust
struct Comparison<'a, 'b> {
    left: &'a str,
    right: &'b str,
}

impl<'a, 'b> Comparison<'a, 'b> {
    fn longer(&self) -> &str {
        if self.left.len() >= self.right.len() {
            self.left
        } else {
            self.right
        }
    }
}

fn main() {
    let a = String::from("hello");
    let b = String::from("hi");
    let cmp = Comparison {
        left: &a,
        right: &b,
    };
    println!("Longer: {}", cmp.longer());
}
```

Using separate lifetime parameters `'a` and `'b` tells the compiler that the two references may come from data with different lifetimes. In many cases a single `'a` works fine (as it would here), but separate parameters give you more flexibility when the sources truly have different scopes.

Note how the `longer` method works: by lifetime elision, the returned `&str` is tied to the lifetime of `&self`. Since the `Comparison` struct cannot outlive either `'a` or `'b` – it holds references with those lifetimes – the compiler knows that `&self` (and therefore the returned reference) is valid for as long as the struct exists. This is why the method compiles without an explicit lifetime annotation on the return type.

## The `'static` lifetime

The lifetime `'static` means "this reference is valid for the entire duration of the program." String literals have the `'static` lifetime because they are baked into the compiled binary:

```rust
// Rust
let s: &'static str = "I live forever";
```

You will also encounter `'static` in trait bounds, particularly in error handling and concurrency. For example, values sent to another thread must be `'static` because the compiler cannot guarantee the original thread's stack will still exist:

```rust
// Rust
use std::thread;

fn main() {
    let handle = thread::spawn(|| {
        println!("Hello from a thread!");
    });
    handle.join().unwrap();
}
```

The closure passed to `thread::spawn` must satisfy `'static` – it cannot capture references to the spawning thread's local variables. It can capture owned values (by moving them into the closure), but not borrows.

A common point of confusion: `'static` does not mean "lives forever" in the sense that the value is leaked or never freed. It means the *reference* is valid for as long as the program runs. An owned `String` satisfies a `T: 'static` bound because it does not contain any non-static references – it owns all its data. The `String` is still dropped normally when it goes out of scope.

### `T: 'static` vs. `&'static T`

These two are often confused:

- **`&'static T`**: a reference that is valid for the entire program. This is rare – string literals and leaked allocations are the main examples.
- **`T: 'static`**: a type that contains no non-static references. All owned types satisfy this (`String`, `Vec<i32>`, `i32`). This bound appears frequently in threading and async APIs.

```rust
// Rust
fn requires_static<T: 'static>(value: T) {
    println!("Got a 'static value");
    drop(value);
}

fn main() {
    let s = String::from("owned");
    requires_static(s); // works – String: 'static because it owns its data

    // let r = &String::from("temporary");
    // requires_static(r); // would fail – &String is not 'static
}
```

## How to think about lifetimes

Coming from Swift, lifetimes can feel like unnecessary bookkeeping. Here are some mental models that may help.

**Lifetimes are constraints, not durations.** You are not specifying how long something lives – you are specifying how long it *must* live for your code to be valid. The compiler then checks that the actual lifetimes satisfy those constraints.

**Lifetime annotations are for the compiler, not for you.** When you write `'a`, you are giving the compiler enough information to verify your references are valid. You already know they are (or you think they are) – the annotations let the compiler confirm it.

**Most lifetimes are inferred.** Thanks to elision, you only need explicit annotations when the compiler cannot figure out the relationships on its own. This typically happens when a function takes multiple references and returns one, or when a struct stores a reference.

**When in doubt, own the data.** If lifetime annotations are making your code complex, consider whether the struct or function should own the data instead of borrowing it. Storing a `String` instead of a `&str` in a struct eliminates the need for a lifetime parameter. This trades some efficiency (a heap allocation) for simplicity, and it is often the right choice.

```rust
// Rust – with lifetime (borrows the data)
struct Config<'a> {
    name: &'a str,
}
```

```rust
// Rust – without lifetime (owns the data)
struct Config {
    name: String,
}
```

The owned version is simpler, more flexible (the `Config` can be moved freely without worrying about what it borrows), and is often what you want unless you are in a performance-critical path.

## Common patterns

### Functions that return references to their input

This is the most common case for explicit lifetimes. The output must be tied to an input:

```rust
// Rust
fn split_at_comma<'a>(s: &'a str) -> (&'a str, &'a str) {
    match s.find(',') {
        Some(pos) => (&s[..pos], &s[pos + 1..]),
        None => (s, ""),
    }
}

fn main() {
    let data = String::from("key,value");
    let (key, value) = split_at_comma(&data);
    println!("key: {key}, value: {value}");
}
```

### Iterators that borrow from a collection

When implementing an iterator over borrowed data, the items yielded are references tied to the collection's lifetime:

```rust
// Rust
struct Words<'a> {
    remaining: &'a str,
}

impl<'a> Iterator for Words<'a> {
    type Item = &'a str;

    fn next(&mut self) -> Option<Self::Item> {
        let remaining = self.remaining.trim_start();
        if remaining.is_empty() {
            return None;
        }
        match remaining.find(' ') {
            Some(pos) => {
                let word = &remaining[..pos];
                self.remaining = &remaining[pos..];
                Some(word)
            }
            None => {
                self.remaining = "";
                Some(remaining)
            }
        }
    }
}

fn main() {
    let text = String::from("hello world from rust");
    let words = Words { remaining: &text };
    for word in words {
        println!("{word}");
    }
}
```

The `'a` lifetime ties the `Words` iterator to the string it is iterating over. The iterator cannot outlive the string, and each word it yields is a slice of the original string – no allocations occur.

### The "just add `'static`" trap

When lifetime errors frustrate you, it can be tempting to slap `'static` everywhere. Resist this urge. `'static` is rarely the right fix for a lifetime issue – it restricts your API to only accept data that lives for the entire program, which rules out most dynamically created values. Instead, look at what the compiler is telling you about which lifetimes are in conflict, and either restructure the code or switch to owned data.

## Key differences and gotchas

**Swift has no lifetimes**: ARC eliminates the need for lifetime reasoning by keeping objects alive as long as any reference exists. This is convenient but has a cost: ARC introduces runtime retain/release bookkeeping, and reference cycles must be broken manually with `weak` or `unowned`.

**Lifetimes are a compile-time concept**: there is no runtime representation of lifetimes. They exist only in the type system and are erased during compilation. They add no runtime overhead.

**Lifetime errors are not bugs in your logic (usually)**: they are the compiler telling you that a reference might outlive its data. The fix is usually one of: restructure code so the reference does not escape its scope, clone or own the data, or add the correct lifetime annotation so the compiler can verify the relationship.

**Lifetimes become second nature**: early on, lifetime annotations feel like arbitrary syntax you are forced to write. With practice, they become a natural part of expressing "this data depends on that data." You will find yourself designing data structures that minimize the need for lifetime parameters, and reaching for owned types when borrowing adds complexity without clear benefit.

## Further reading

- [The Rust Programming Language – Validating References with Lifetimes](https://doc.rust-lang.org/book/ch10-03-lifetime-syntax.html): the official chapter on lifetimes
- [Rust by Example – Lifetimes](https://doc.rust-lang.org/rust-by-example/scope/lifetime.html): practical lifetime examples
- [Common Rust Lifetime Misconceptions](https://github.com/pretzelhammer/rust-blog/blob/master/posts/common-rust-lifetime-misconceptions.md): an excellent article that clears up frequent misunderstandings
- [The Rustonomicon – Lifetimes](https://doc.rust-lang.org/nomicon/lifetimes.html): advanced lifetime topics
- [Crust of Rust: Lifetime Annotations](https://www.youtube.com/watch?v=rAl-9HwD858): Jon Gjengset's video walkthrough of lifetimes
