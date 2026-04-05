---
title: "Appendix B: Glossary"
sidebar:
  order: 101
---

Rust-specific terminology with brief definitions. Where a Swift equivalent exists, it is noted in parentheses.

---

**Arc**: Atomically Reference Counted – a thread-safe shared ownership smart pointer. Similar to a thread-safe version of Swift's reference counting, though explicit rather than automatic. See also `Rc`.

**Associated function**: A function defined in an `impl` block that does not take `self` as a parameter. Called with `Type::function()` syntax. (Swift equivalent: `static func`.)

**Borrow**: Temporarily accessing a value through a reference (`&T` or `&mut T`) without taking ownership. (Loosely analogous to Swift's inout for mutable borrows, though more pervasive.)

**Borrow checker**: The part of the Rust compiler that enforces borrowing rules – ensuring references are always valid and that mutable and immutable references do not coexist. Swift has no equivalent; it relies on ARC and value semantics instead.

**Box**: A smart pointer that allocates a value on the heap. Written as `Box<T>`. Used for recursive types, trait objects, and large values. (No direct Swift equivalent – Swift handles heap allocation automatically for classes and large values.)

**Clone**: A trait that provides an explicit `.clone()` method for creating a deep copy of a value. Types that implement `Clone` can be duplicated on demand, but the copy is always explicit. (Swift equivalent: value types usually provide copy semantics automatically; for reference types, `NSCopying` or manual copy methods serve a similar purpose.)

**Closure capture (Fn / FnMut / FnOnce)**: Rust closures implement one of three traits depending on how they use captured variables. `Fn` borrows immutably, `FnMut` borrows mutably, `FnOnce` consumes the captured values. (Swift closures capture by reference by default, with `[value]` capture lists for value captures.)

**Copy**: A marker trait indicating that a type can be duplicated by simply copying its bits, with no need for an explicit `.clone()` call. Types implementing `Copy` are implicitly copied on assignment or when passed to a function. Primitive types like integers and floats implement `Copy`. (Swift equivalent: most value types are copyable by default, though Swift also has newer noncopyable features.)

**Crate**: A compilation unit in Rust – either a binary or a library. This is usually closer to a Swift target or module than to an entire Swift package, because a single Rust package can contain multiple crates.

**Derive**: An attribute (`#[derive(...)]`) that automatically generates trait implementations for a type. Similar to Swift's automatic conformance synthesis for `Equatable`, `Hashable`, and `Codable`, but extensible to any trait via procedural macros.

**Destructuring**: Binding individual fields or elements of a struct, tuple, or enum to separate variables in a pattern. (Swift equivalent: tuple decomposition and `case let` patterns.)

**Drop**: A trait that provides a deterministic destructor. When a value goes out of scope, its `drop` method is called automatically, allowing it to release resources. (Swift equivalent: `deinit` on classes, which is called when the reference count reaches zero.)

**`dyn`**: Keyword indicating dynamic dispatch through a trait object. `dyn Trait` is Rust's equivalent of Swift's existential `any Protocol` type.

**`impl` block**: A block that defines methods and associated functions for a type (`impl Type { }`) or implements a trait for a type (`impl Trait for Type { }`). (Swift equivalent: the type definition body itself, plus `extension` for adding conformances.)

**Lifetime**: A compile-time annotation (e.g., `'a`) that tells the borrow checker how long a reference is valid. Swift has no equivalent – ARC manages object lifetimes at runtime.

**Macro**: A metaprogramming construct that generates code at compile time. Declarative macros (`macro_rules!`) work by pattern matching on syntax. Procedural macros operate on the token stream directly. (Swift macros, introduced in Swift 5.9, serve a similar role but differ in mechanism.)

**Module**: A namespace for organizing code within a crate. Declared with `mod`. (Swift equivalent: roughly the nesting you create with types/extensions and file organization, though Swift modules map more closely to Rust crates than to Rust modules.)

**Monomorphization**: The compiler's process of generating specialized versions of generic code for each concrete type used. Rust relies on this model for generic type parameters. Swift can also specialize generic code, but it is not as uniformly monomorphized as Rust.

**Move**: Transferring ownership of a value from one binding to another. After a move, the original binding is no longer usable. (Swift moves values of noncopyable types and can consume parameters with `consuming`, but most Swift types are copyable by default.)

**Mutex**: A synchronization primitive from `std::sync` that provides thread-safe interior mutability by requiring a lock before accessing the inner value. `Mutex<T>` ensures only one thread can access the data at a time. Often combined with `Arc` for shared ownership across threads. (Swift equivalent: using actors or `os_unfair_lock` / `NSLock` to protect shared mutable state.)

**`mut`**: Keyword that makes a variable binding mutable (`let mut x`) or creates a mutable reference (`&mut x`). (Swift equivalent: `var` for mutable bindings, `inout` for mutable parameter passing.)

**Option**: An enum (`Some(T)` or `None`) representing an optional value. (Swift equivalent: `Optional<T>`, written as `T?`.)

**Ownership**: Rust's system where each value has exactly one owner at a time. When the owner goes out of scope, the value is dropped. In the default model this replaces garbage collection and implicit reference counting, though Rust still provides explicit shared-ownership types such as `Rc` and `Arc` when you need them. (Swift uses ARC for reference types and copy-on-write for value types instead.)

**Panic**: An unrecoverable error that unwinds the stack and terminates the thread (or the process, depending on configuration). Similar to Swift's `fatalError()` or a force-unwrap failure. Not used for recoverable errors – those use `Result`.

**Pattern matching**: Destructuring and testing values against patterns using `match`, `if let`, `while let`, or `let` bindings. Both Swift and Rust have extensive pattern matching, though the syntax differs.

**Pin**: A wrapper (`Pin<P>`) that prevents a value from being moved in memory. Used primarily with async futures and self-referential types. Swift has no equivalent because it uses ARC and does not expose move semantics at this level.

**Rc**: Reference Counted – a single-threaded shared ownership smart pointer. Similar to Swift's ARC-managed references, but limited to one thread and opt-in rather than automatic. See also `Arc`.

**RefCell**: A type that provides interior mutability by enforcing borrow rules at runtime rather than compile time. Allows mutable access to data inside an otherwise immutable structure. (No direct Swift equivalent – Swift's class references and `var` properties serve a loosely similar role.)

**Result**: An enum (`Ok(T)` or `Err(E)`) representing success or failure. (Closest Swift analogues: the standard library's `Result<Success, Failure>` type and, in everyday code, the `throws` / `try` mechanism.)

**`Send`**: A marker trait indicating that a type can be safely transferred across thread boundaries. (Swift equivalent: `Sendable`.)

**Shadowing**: Declaring a new variable with the same name as an existing one, effectively replacing it within the current scope. Unlike reassignment, shadowing allows changing the type. (Swift allows shadowing across scopes but discourages it within the same scope.)

**Slice**: A dynamically sized view into a contiguous sequence, written as `&[T]`. (Swift equivalent: `ArraySlice<T>` or `Slice`.)

**`Sync`**: A marker trait indicating that a type can be safely shared between threads by reference. (Swift equivalent: `Sendable` covers both `Send` and `Sync` semantics.)

**Trait**: A collection of methods that types can implement, enabling polymorphism. (Swift equivalent: `protocol`.)

**Trait object**: A dynamically dispatched reference to a type implementing a trait, written as `dyn Trait`. Must be behind a pointer (`&dyn Trait`, `Box<dyn Trait>`). (Swift equivalent: existential types, `any Protocol`.)

**Turbofish**: The `::<Type>` syntax used to specify generic type parameters at the call site, as in `"42".parse::<i32>()`. Named for its resemblance to a fish. (No Swift equivalent – Swift uses type inference or explicit type annotations on the binding.)

**`unsafe`**: A keyword that marks a block or function where the compiler's safety guarantees are relaxed. Inside `unsafe`, you can dereference raw pointers, call FFI functions, and access mutable statics. The programmer is responsible for upholding safety invariants. (Swift equivalent: `UnsafePointer`, `UnsafeMutablePointer`, and related APIs, though Swift does not have a single `unsafe` block construct.)

**Unwrap**: Extracting the inner value from an `Option` or `Result`, panicking if the value is `None` or `Err`. Called via `.unwrap()`. (Swift equivalent: force-unwrapping with `!`.)

**Visibility**: The rules governing which code can access an item. Rust defaults to private within the module. Items are made public with `pub`, with finer-grained options like `pub(crate)` and `pub(super)`. (Swift defaults to `internal` visibility within the module.)

**Zero-cost abstraction**: A design principle where high-level constructs compile down to code as efficient as a hand-written low-level equivalent. Both Swift and Rust embrace this principle – Rust applies it especially to iterators, closures, and trait-based generics.
