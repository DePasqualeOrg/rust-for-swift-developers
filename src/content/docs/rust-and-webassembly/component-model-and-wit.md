---
title: The Component Model and WIT
sidebar:
  order: 33
---

The Component Model is a specification that adds typed interfaces, composability, and language interoperability on top of core WebAssembly. If core Wasm modules are like C object files – functional but low-level and loosely typed at their boundaries – then components are like libraries with well-defined APIs that different languages can call without hand-writing ABI glue.

## Why the Component Model exists

Core Wasm modules can import and export functions, but those functions still traffic in low-level Wasm value types rather than language-level data structures. Passing a string from a host to a module typically requires the host to write bytes into the module's linear memory and pass a pointer and length. Passing a record (struct) requires serializing it to bytes, copying it into linear memory, and agreeing on a layout. Returning a list requires the module to allocate memory, write the list contents, and return a pointer.

This works, but it has the same problems as C FFI:

- No self-describing interfaces – you need out-of-band documentation or header files
- No type safety at the boundary – the host and module must agree on memory layouts
- No composability – two modules cannot communicate without a shared memory convention
- Fragile ABI – changing a struct layout breaks everything

The Component Model solves these problems by defining a higher-level layer on top of core Wasm. A component wraps a core module and adds:

- A typed interface written in WIT, describing exactly what the component imports and exports
- The Canonical ABI, which specifies how high-level types (strings, lists, records, variants) are represented in linear memory
- A composition mechanism that lets components be linked together through their interfaces

For Swift developers, this is analogous to the difference between calling C functions through a bridging header and calling a Swift framework with its `.swiftinterface`. The Component Model gives Wasm the same level of type safety and discoverability that you are used to from Swift module interfaces.

## Components vs modules

| Feature | Core module | Component |
|---|---|---|
| Value types | Low-level Wasm scalar/vector/reference types | Strings, lists, records, variants, options, results, resources, and more |
| Interface description | None (convention-based) | WIT (embedded in the binary) |
| Composability | Shared memory only | Interface-level linking |
| Memory model | Single shared linear memory | Each component has its own memory (no shared state) |
| Language support | Any language that targets Wasm | Any language with a Component Model binding generator |

The memory isolation is worth emphasizing. When two components are composed together, they do not share linear memory. Data is copied across component boundaries through the Canonical ABI. This provides strong isolation – one component cannot corrupt another's memory – at the cost of copying data at interface boundaries.

## WIT: WebAssembly Interface Types

WIT is the interface definition language for the Component Model. It defines what a component imports and exports – the types, functions, and interfaces that make up a component's contract with the outside world.

If you are a Swift developer, think of a WIT file as roughly analogous to a Swift protocol definition. It declares the shape of an API without providing the implementation. The implementation is in Rust (or any other language with a WIT binding generator), and the WIT interface is the contract that consumers depend on.

### Packages

A WIT package is the top-level unit of organization. It has a namespace, a name, and an optional version:

```wit
package example:image-processing@1.0.0;
```

The namespace (`example`) and package name (`image-processing`) together form the package identifier. The version follows semantic versioning. This is similar to a Swift package or Rust crate identifier.

### Interfaces

An interface is a named collection of types and functions. It is the primary unit of abstraction in WIT – the thing that components import and export.

```wit
package example:image-processing@1.0.0;

interface resize {
    record dimensions {
        width: u32,
        height: u32,
    }

    enum algorithm {
        nearest-neighbor,
        bilinear,
        lanczos,
    }

    resize-image: func(
        data: list<u8>,
        target: dimensions,
        algo: algorithm,
    ) -> result<list<u8>, string>;
}
```

This interface defines a `resize` capability with a `dimensions` record, an `algorithm` enum, and a `resize-image` function. Anyone consuming this interface knows exactly what types to pass and what to expect back.

### Worlds

A world defines a complete component – what it imports (needs from the host) and what it exports (provides to consumers). It is the entry point for component compilation.

```wit
package example:image-processing@1.0.0;

interface resize {
    // ... types and functions as above
}

interface metadata {
    record image-info {
        width: u32,
        height: u32,
        format: string,
        size-bytes: u64,
    }

    get-info: func(data: list<u8>) -> result<image-info, string>;
}

world image-processor {
    export resize;
    export metadata;
}
```

This world says: "A component that implements `image-processor` must provide the `resize` and `metadata` interfaces." A consumer of the component can call any function in those exported interfaces.

Worlds can also import interfaces – things the component needs from its host environment:

```wit
interface host-log {
    log: func(message: string);
}

world image-processor {
    import host-log;
    export resize;
    export metadata;
}
```

In Swift terms, a world is like a protocol that declares both requirements (exports – what the conforming type must implement) and dependencies (imports – what the conforming type needs to be provided).

### WIT types

WIT provides a rich type system that maps naturally to both Rust and Swift types. Here is the full set:

**Primitive types:**

| WIT type | Rust type | Swift equivalent |
|---|---|---|
| `bool` | `bool` | `Bool` |
| `u8`, `u16`, `u32`, `u64` | `u8`, `u16`, `u32`, `u64` | `UInt8`, `UInt16`, `UInt32`, `UInt64` |
| `s8`, `s16`, `s32`, `s64` | `i8`, `i16`, `i32`, `i64` | `Int8`, `Int16`, `Int32`, `Int64` |
| `f32`, `f64` | `f32`, `f64` | `Float`, `Double` |
| `char` | `char` | `Unicode.Scalar` (closest match) |
| `string` | `String` | `String` |

WIT's `char` is a Unicode scalar value, so Swift's `Unicode.Scalar` is the closest conceptual match. Swift's `Character` can contain multiple scalars.

**Compound types:**

- **`record`**: a named collection of fields. Maps to a Rust `struct` and a Swift `struct`.

```wit
record point {
    x: f64,
    y: f64,
}
```

- **`variant`**: a tagged union with optional payloads. Maps to a Rust `enum` with associated data and a Swift `enum` with associated values.

```wit
variant shape {
    circle(f64),
    rectangle(dimensions),
    triangle(point, point, point),
}
```

- **`enum`**: a variant with no payloads – just labels. Maps to a unit-only Rust `enum` and a Swift `enum` without associated values.

```wit
enum color {
    red,
    green,
    blue,
}
```

- **`flags`**: a set of named boolean flags, represented as a bitmask. Maps to a Rust bitflags type and is similar to Swift's `OptionSet`.

```wit
flags permissions {
    read,
    write,
    execute,
}
```

- **`list<T>`**: a variable-length sequence. Maps to `Vec<T>` in Rust and `[T]` (Array) in Swift.

```wit
get-items: func() -> list<string>;
```

- **`option<T>`**: an optional value. Maps to `Option<T>` in Rust and `T?` in Swift.

```wit
find-user: func(id: u32) -> option<user>;
```

- **`result<T, E>`**: a success-or-error value. Maps to `Result<T, E>` in Rust and is similar to Swift's `Result<T, E>`.

```wit
parse-config: func(input: string) -> result<config, string>;
```

- **`tuple<T1, T2, ...>`**: an anonymous grouping of values. Maps to Rust tuples and Swift tuples.

```wit
get-bounds: func() -> tuple<f64, f64>;
```

- **`resource`**: a handle to an opaque, host-managed object with methods and a lifetime. Resources support constructors, methods, and static functions:

```wit
resource connection {
    constructor(url: string);
    send: func(data: list<u8>) -> result<_, string>;
    close: func();
    timeout: static func() -> u32;
}
```

Resources are the most complex WIT type. They represent owned handles that the host manages. The component interacts with a resource through its methods, and the resource is cleaned up when the handle is dropped. In Swift terms, a resource is similar to a class instance with reference semantics – you hold a handle to it, and the runtime manages its lifecycle.

### Type aliases

WIT supports type aliases for readability:

```wit
type user-id = u32;
type image-data = list<u8>;
```

### Using types across interfaces

Types defined in one interface can be used in another through `use` statements:

```wit
interface types {
    record user {
        id: u32,
        name: string,
    }
}

interface auth {
    use types.{user};
    authenticate: func(token: string) -> option<user>;
}
```

## The Canonical ABI

The Canonical ABI is the specification that defines how WIT types are represented in linear memory. It is the bridge between the rich types in a WIT interface and the flat numeric types that core Wasm actually supports.

You do not need to implement the Canonical ABI yourself – `wit-bindgen` and `cargo-component` handle it automatically. But understanding what it does helps explain the design decisions:

- **Strings**: UTF-8 encoded bytes in linear memory. The ABI passes a pointer and a byte length.
- **Lists**: similarly passed as a pointer to the first element and an element count.
- **Records**: laid out as a sequence of fields in memory, with alignment and padding rules similar to C structs.
- **Variants**: represented as a discriminant tag followed by the payload of the active case.
- **Options and results**: variants with standard layouts.

When data crosses a component boundary, it is serialized into the source component's linear memory, and the receiving component copies it into its own memory. This is different from shared-memory FFI, where both sides see the same bytes. The copying adds overhead but guarantees isolation.

For Swift developers used to the cost of copying value types across boundaries, the mental model is similar. Passing a `struct` from one Swift module to another involves copying it; passing a record from one Wasm component to another involves serializing and copying it through the Canonical ABI. The cost is comparable for small types and proportional to size for large ones.

## wit-bindgen

[wit-bindgen](https://github.com/bytecodealliance/wit-bindgen) is the tool that generates language-specific bindings from WIT definitions. For Rust, it generates:

- Trait definitions for exported interfaces (you implement these traits)
- Struct definitions for imported interfaces (you call methods on these structs)
- Type definitions for all WIT types (records become Rust structs, variants become enums, etc.)

When using `cargo-component`, binding generation is integrated into the build process – you do not need to run `wit-bindgen` manually. The tool reads your WIT files, generates Rust code, and makes it available through the `bindings` module.

`wit-bindgen` also supports other languages: C, C++, Java, Go, C#, and more. This is what makes the Component Model language-agnostic: the same WIT definition can generate bindings for any supported language, and components implemented in different languages can interact through their shared interfaces.

## Practical example: implementing a WIT interface

Let's build a text-analysis component that demonstrates several WIT types. This example uses `cargo-component` for the full workflow.

### 1. Define the WIT interface

Create a file at `wit/world.wit`:

```wit
package example:text-analysis@0.1.0;

interface analyzer {
    record analysis {
        word-count: u32,
        char-count: u32,
        sentence-count: u32,
        average-word-length: f64,
        most-common-words: list<word-frequency>,
    }

    record word-frequency {
        word: string,
        count: u32,
    }

    enum case-style {
        lower,
        upper,
        title,
    }

    analyze: func(text: string) -> analysis;
    convert-case: func(text: string, style: case-style) -> string;
    extract-sentences: func(text: string) -> list<string>;
}

world text-analysis {
    export analyzer;
}
```

### 2. Implement the component

In `src/lib.rs`:

```rust
mod bindings;

use std::collections::HashMap;

use bindings::exports::example::text_analysis::analyzer::{
    Analysis, CaseStyle, Guest, WordFrequency,
};

struct Component;

impl Guest for Component {
    fn analyze(text: String) -> Analysis {
        let words: Vec<&str> = text.split_whitespace().collect();
        let word_count = words.len() as u32;
        let char_count = text.chars().count() as u32;
        let sentence_count = text
            .chars()
            .filter(|c| matches!(c, '.' | '!' | '?'))
            .count() as u32;

        let total_word_chars: usize = words.iter().map(|w| w.chars().count()).sum();
        let average_word_length = if word_count > 0 {
            total_word_chars as f64 / word_count as f64
        } else {
            0.0
        };

        // Count word frequencies
        let mut freq_map: HashMap<String, u32> = HashMap::new();
        for word in &words {
            let normalized = word
                .to_lowercase()
                .trim_matches(|c: char| !c.is_alphanumeric())
                .to_string();
            if !normalized.is_empty() {
                *freq_map.entry(normalized).or_insert(0) += 1;
            }
        }

        let mut most_common_words: Vec<WordFrequency> = freq_map
            .into_iter()
            .map(|(word, count)| WordFrequency { word, count })
            .collect();
        most_common_words.sort_by(|a, b| b.count.cmp(&a.count));
        most_common_words.truncate(10);

        Analysis {
            word_count,
            char_count,
            sentence_count,
            average_word_length,
            most_common_words,
        }
    }

    fn convert_case(text: String, style: CaseStyle) -> String {
        match style {
            CaseStyle::Lower => text.to_lowercase(),
            CaseStyle::Upper => text.to_uppercase(),
            CaseStyle::Title => text
                .split_whitespace()
                .map(|word| {
                    let mut chars = word.chars();
                    match chars.next() {
                        None => String::new(),
                        Some(first) => {
                            let upper: String = first.to_uppercase().collect();
                            format!("{upper}{}", chars.as_str().to_lowercase())
                        }
                    }
                })
                .collect::<Vec<_>>()
                .join(" "),
        }
    }

    fn extract_sentences(text: String) -> Vec<String> {
        text.split_inclusive(|c: char| matches!(c, '.' | '!' | '?'))
            .map(|s| s.trim().to_string())
            .filter(|s| !s.is_empty())
            .collect()
    }
}

bindings::export!(Component with_types_in bindings);
```

Notice how the WIT types map to Rust:

- `record analysis` became the `Analysis` struct with fields matching the WIT definition
- `record word-frequency` became `WordFrequency` (WIT's kebab-case is converted to Rust's PascalCase and snake_case)
- `enum case-style` became `CaseStyle` – a Rust enum with unit variants
- `list<word-frequency>` became `Vec<WordFrequency>`
- `list<string>` became `Vec<String>`

### 3. Build and inspect

```bash
cargo component build --release
wasm-tools component wit target/wasm32-wasip2/release/text_analysis.wasm
```

The `wasm-tools component wit` command prints the WIT interface that the compiled component actually exports, letting you verify it matches your definition.

## Composing components

One of the Component Model's most powerful features is composition – linking components together through their interfaces. Suppose you have:

- A `text-analysis` component that exports an `analyzer` interface
- A `report-generator` component that imports an `analyzer` interface and exports a `reporter` interface

You can compose them into a single component:

```bash
wac plug report-generator.wasm \
    --plug text-analysis.wasm \
    -o composed.wasm
```

The composed component satisfies the `report-generator`'s import of `analyzer` with the `text-analysis` component's export. The result is a new component that exports only the `reporter` interface and has no unsatisfied imports (for the `analyzer` dependency).

This is conceptually similar to dependency injection in Swift, but at the binary level. Components are wired together by matching interface types, and the result is a new component that can be deployed as a single unit.

## WIT compared to Swift protocols

For Swift developers, WIT interfaces and Swift protocols serve a similar purpose – they define a contract that an implementor must fulfill. Here are the parallels and differences:

| Concept | Swift | WIT |
|---|---|---|
| Interface definition | `protocol` | `interface` |
| Implementation | `struct`/`class` conforming to protocol | Component implementing the world |
| Associated types | `associatedtype` | Type definitions within interface |
| Enums with data | `enum` with associated values | `variant` |
| Enums without data | `enum` (raw-value or simple) | `enum` |
| Structs | `struct` | `record` |
| Optionals | `Optional<T>` / `T?` | `option<T>` |
| Error handling | `Result<T, E>` / `throws` | `result<T, E>` |
| Opaque types | `some Protocol` / class reference | `resource` |
| Namespacing | Module / package | Package / interface |

The most significant conceptual difference is scope. A Swift protocol defines a contract within a single process and language. A WIT interface defines a contract across languages, runtimes, and execution environments. The same WIT interface can be implemented in Rust, consumed from Python, and run inside a JavaScript application – all without any of the participants knowing or caring what language the others are using.

## Key differences and gotchas

- **Kebab-case naming**: WIT uses kebab-case for identifiers (`word-count`, `case-style`). Binding generators convert these to the target language's conventions – `word_count` in Rust, `wordCount` in Swift-style languages.
- **No generics in WIT**: WIT does not support user-defined generic types. `list<T>`, `option<T>`, and `result<T, E>` are built-in parameterized types, but you cannot define your own `container<T>`. If you need polymorphism, use separate interfaces or `variant` types.
- **Copy semantics at boundaries**: all data crossing a component boundary is copied through the Canonical ABI. There are no shared references between components. For large data transfers, this copying has a real cost. Design your interfaces to minimize cross-boundary data movement for performance-sensitive workloads.
- **Resources have overhead**: each `resource` handle involves a table lookup in the host. For fine-grained operations on many resources, the overhead can add up. Prefer batch operations when possible.
- **The standards and tooling are still evolving**: some runtimes and workflows are usable today, but WIT, resources, async support, and surrounding tools continue to change. Pin your tooling versions and test thoroughly when upgrading.
- **String encoding**: WIT strings are always UTF-8. This matches Rust's `String` type. Swift's `String` is also Unicode-correct and has used UTF-8 as its native encoding since Swift 5, so the conversion is transparent when going through binding generators.
- **Error handling**: WIT's `result<T, E>` maps directly to Rust's `Result<T, E>`. There is no equivalent of Swift's `throws` sugar – you work with the result type explicitly.

## Further reading

- [Component Model specification](https://github.com/WebAssembly/component-model): the official repository and design documents
- [Component Model documentation](https://component-model.bytecodealliance.org/): the Bytecode Alliance's guide to the Component Model
- [WIT specification](https://github.com/WebAssembly/component-model/blob/main/design/mvp/WIT.md): the formal WIT language definition
- [wit-bindgen repository](https://github.com/bytecodealliance/wit-bindgen): binding generators for Rust, C, Java, Go, and more
- [cargo-component repository](https://github.com/bytecodealliance/cargo-component): the Cargo subcommand for building components
- [Canonical ABI specification](https://github.com/WebAssembly/component-model/blob/main/design/mvp/CanonicalABI.md): how WIT types map to linear memory
- [WASI proposals](https://github.com/WebAssembly/WASI/blob/main/Proposals.md): standard interfaces built on WIT
