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

**Borrow checker**: Compiler analysis that checks reference validity and aliasing rules. Shared borrows exclude overlapping exclusive borrows; interior-mutability types provide controlled exceptions to mutation through shared references. Swift also checks exclusivity and supports ownership and lifetime-dependent types, though the languages expose these rules differently.

**Box**: A smart pointer that allocates a value on the heap. Written as `Box<T>`. Used for recursive types, trait objects, and large values. (No direct Swift equivalent – Swift handles heap allocation automatically for classes and large values.)

**Clone**: A trait for explicitly duplicating a value with `.clone()`. The implementation defines what duplication means: cloning a `Vec` clones its elements, while cloning an `Rc` or `Arc` shares its allocation and increments a reference count. A clone is not necessarily a deep copy.

**Closure call traits (`Fn`/`FnMut`/`FnOnce`)**: Traits describing how a closure can be called. `Fn` permits calls through a shared reference, `FnMut` requires mutable access, and `FnOnce` consumes the closure. Every closure implements `FnOnce`; some also implement `FnMut` and `Fn`. Capture by value with `move` does not by itself make a closure callable only once.

**Constant item**: A typed name declared with `const` whose initializer is evaluated at compile time. It is a value rather than one guaranteed shared storage location; `static` declares shared storage.

**Copy**: A marker trait indicating that a type can be duplicated by simply copying its bits, with no need for an explicit `.clone()` call. Types implementing `Copy` are implicitly copied on assignment or when passed to a function. Primitive types like integers and floats implement `Copy`. (Swift equivalent: most value types are copyable by default, though Swift also has newer noncopyable features.)

**Crate**: A compilation unit in Rust – either a binary or a library. This is usually closer to a Swift target or module than to an entire Swift package, because a single Rust package can contain multiple crates.

**Derive**: An attribute (`#[derive(...)]`) that automatically generates trait implementations for a type. Similar to Swift's automatic conformance synthesis for `Equatable`, `Hashable`, and `Codable`, but extensible to any trait via procedural macros.

**Destructuring**: Binding individual fields or elements of a struct, tuple, or enum to separate variables in a pattern. (Swift equivalent: tuple decomposition and `case let` patterns.)

**Drop**: A trait for running cleanup when a value is destroyed, normally at the end of its owner’s scope. Leaking or forgetting a value and aborting a process can prevent cleanup. Swift provides `deinit` for classes and noncopyable structs.

**`dyn`**: Keyword indicating dynamic dispatch through a trait object. `dyn Trait` is Rust's equivalent of Swift's existential `any Protocol` type.

**`impl` block**: A block that defines methods and associated functions for a type (`impl Type { }`) or implements a trait for a type (`impl Trait for Type { }`). (Swift equivalent: the type definition body itself, plus `extension` for adding conformances.)

**Lifetime**: A region over which a reference must remain valid. Lifetimes are usually inferred; named parameters such as `'a` express relationships in an API. They do not extend the life of a value. Swift also has lifetime-dependent types such as `Span`, although it does not use Rust’s lifetime-parameter syntax.

**Macro**: A metaprogramming construct that generates code at compile time. Declarative macros (`macro_rules!`) work by pattern matching on syntax. Procedural macros operate on the token stream directly. (Swift macros serve a similar role but differ in mechanism.)

**Module**: A namespace for organizing code within a crate. Declared with `mod`. (Swift equivalent: roughly the nesting you create with types/extensions and file organization, though Swift modules map more closely to Rust crates than to Rust modules.)

**Monomorphization**: The compiler's process of generating specialized versions of generic code for each concrete type used. Rust relies on this model for generic type parameters. Swift can also specialize generic code, but it is not as uniformly monomorphized as Rust.

**Move**: Transferring ownership of a value from one binding to another. After a move, the original binding is no longer usable. (Swift moves values of noncopyable types and can consume parameters with `consuming`, but most Swift types are copyable by default.)

**Mutex**: A synchronization primitive from `std::sync` that provides thread-safe interior mutability by requiring a lock before accessing the inner value. `Mutex<T>` ensures only one thread can access the data at a time. Often combined with `Arc` for shared ownership across threads. (Swift equivalent: using actors or `os_unfair_lock`/`NSLock` to protect shared mutable state.)

**`mut`**: Keyword that makes a variable binding mutable (`let mut x`) or creates a mutable reference (`&mut x`). (Swift equivalent: `var` for mutable bindings, `inout` for mutable parameter passing.)

**Option**: An enum (`Some(T)` or `None`) representing an optional value. (Swift equivalent: `Optional<T>`, written as `T?`.)

**Ownership**: Rules governing responsibility for values and their destruction. Moves transfer ownership; `Rc` and `Arc` represent shared ownership explicitly. Swift also supports ownership and noncopyable values; ARC manages class instances, while some value types use copy-on-write storage.

**Panic**: A failure that invokes Rust’s panic machinery. Depending on configuration, it unwinds the stack or aborts the process. Unwinding panics can sometimes be caught; an uncaught panic in a spawned thread does not necessarily terminate the process. Use `Result` for expected, recoverable errors.

**Pattern matching**: Destructuring and testing values against patterns using `match`, `if let`, `while let`, or `let` bindings. Both Swift and Rust have extensive pattern matching, though the syntax differs.

**Pin**: A pointer wrapper, `Pin<P>`, that restricts moving the pointee when its type is not `Unpin`. It supports address-sensitive values, including some async futures. Moving the pointer itself is allowed; pinning an `Unpin` value adds no such movement restriction.

**Rc**: Reference Counted – a single-threaded shared ownership smart pointer. Similar to Swift's ARC-managed references, but limited to one thread and opt-in rather than automatic. See also `Arc`.

**RefCell**: A type that provides interior mutability by enforcing borrow rules at runtime rather than compile time. Allows mutable access to data inside an otherwise immutable structure. (No direct Swift equivalent – Swift's class references and `var` properties serve a loosely similar role.)

**Result**: An enum (`Ok(T)` or `Err(E)`) representing success or failure. (Closest Swift analogues: the standard library's `Result<Success, Failure>` type and, in everyday code, the `throws`/`try` mechanism.)

**`Send`**: A marker trait indicating that a type can be safely transferred across thread boundaries. (Swift equivalent: `Sendable`.)

**Shadowing**: Declaring a new binding with the same name as an existing one. Unlike reassignment, it can change the type. Swift supports shadowing in nested scopes but rejects redeclaring a local in the same scope.

**Slice**: A dynamically sized contiguous sequence type, `[T]`, usually accessed through `&[T]` or `&mut [T]`. Swift’s `ArraySlice` provides a collection view with different ownership semantics; `Span` provides a lifetime-dependent borrowed view.

**`Sync`**: A marker trait meaning that `&T` can be transferred safely between threads, equivalently that `&T: Send`. Swift’s `Sendable` serves a related concurrency-safety role but does not map one-to-one to Rust’s separate `Send` and `Sync` traits.

**Trait**: A collection of methods that types can implement, enabling polymorphism. (Swift equivalent: `protocol`.)

**Trait object**: A dynamically dispatched reference to a type implementing a trait, written as `dyn Trait`. Must be behind a pointer (`&dyn Trait`, `Box<dyn Trait>`). (Swift equivalent: existential types, `any Protocol`.)

**Turbofish**: The `::<Type>` syntax used to specify generic type parameters at the call site, as in `"42".parse::<i32>()`. Named for its resemblance to a fish. (No Swift equivalent – Swift uses type inference or explicit type annotations on the binding.)

**`unsafe`**: A keyword used to declare safety obligations or acknowledge them at an operation. Unsafe blocks permit specific operations such as raw-pointer dereferences; ordinary type and borrow checks still apply. Swift has unsafe pointer APIs and, in Swift 6.2, explicit `unsafe` expressions for strict memory-safety checking.

**Unwrap**: Extracting the inner value from an `Option` or `Result`, panicking if the value is `None` or `Err`. Called via `.unwrap()`. (Swift equivalent: force-unwrapping with `!`.)

**Visibility**: The rules governing which code can access an item. Rust defaults to private within the module. Items are made public with `pub`, with finer-grained options like `pub(crate)` and `pub(super)`. (Swift defaults to `internal` visibility within the module.)

**Zero-cost abstraction**: A design principle where high-level constructs compile down to code as efficient as a hand-written low-level equivalent. Both Swift and Rust embrace this principle – Rust applies it especially to iterators, closures, and trait-based generics.
