---
title: From FFI to the Component Model
sidebar:
  order: 30
---

The previous two chapters showed how to cross the language boundary with C FFI and how to make that practical on Apple platforms with tools like UniFFI. These approaches work, and many production apps rely on them. But they all share fundamental limitations that become more apparent as your ambitions grow – especially if you want to write a library once and use it on every platform, in every language, without recompiling.

The WebAssembly Component Model is an attempt to solve those problems.

## Limitations of C FFI

The C ABI is the lingua franca of systems programming. Nearly every language can call C functions, which is why C FFI is the default approach for cross-language interop. But the C ABI was designed in the 1970s for a single language on a single machine. Using it as the foundation for modern multi-language interop comes with real costs.

### No rich types

C has no strings (only null-terminated byte arrays), no slices (only pointers and lengths passed separately), no variants or sum types, no optionals, no result types, and no generics. When you expose a Rust API through C FFI, you lose most of the type richness that makes Rust (and Swift) pleasant to use:

```rust
// Rust – the real API
pub fn parse_config(input: &str) -> Result<Config, ParseError> { ... }

// Rust – the C FFI version
#[unsafe(no_mangle)]
pub extern "C" fn parse_config(
    input: *const c_char,       // was &str
    out: *mut ConfigFfi,        // was Config (via return)
    err_buf: *mut c_char,       // was ParseError (via Result)
    err_buf_len: usize,         // error buffer capacity
) -> i32 {                      // 0 = success, negative = error code
    ...
}
```

Every `Result` becomes an error code. Every `String` becomes a pointer and a length. Every enum becomes an integer. The type information that the compiler uses to prevent bugs is stripped away at the boundary.

### Manual memory management across the boundary

When Rust allocates memory and passes a pointer to C (or Swift), someone has to free it – and both sides must agree on who and how. You saw this in Chapter 28 with the `Box::into_raw` / `Box::from_raw` pattern. Get it wrong, and you get memory leaks, double frees, or use-after-free bugs – exactly the classes of bugs that both Rust and Swift are designed to prevent.

There is no compile-time help at the boundary. Rust's ownership system and Swift's ARC both stop at the FFI edge.

### Platform-specific compilation

A static library compiled for `aarch64-apple-ios` will not run on `x86_64-unknown-linux-gnu`. You must compile separately for every target platform and architecture, then distribute platform-specific binaries. For a library targeting iOS, macOS, Android, Linux, Windows, and the web, this means maintaining a matrix of build configurations.

### No sandboxing

When you link a C library into your process, it has full access to your process's memory space. A bug in the library can corrupt your app's state. A malicious library can read your app's private data. There is no isolation – the C ABI assumes full trust between caller and callee.

### ABI fragility

C's ABI depends on platform conventions for struct layout, alignment, and calling conventions. These vary across architectures and operating systems. A struct that is laid out correctly on ARM may have different padding on x86. The `repr(C)` attribute in Rust guarantees C-compatible layout, but the specific layout still depends on the target platform.

## Limitations of UniFFI

UniFFI (Chapter 29) solves the ergonomics problem by generating idiomatic Swift (and Kotlin, Python, and Ruby) bindings from Rust code. It maps `Result` to `throws`, `Vec` to arrays, and converts naming conventions. This is a significant improvement over raw C FFI, but UniFFI inherits some fundamental limitations.

### Still platform-specific binaries

UniFFI generates beautiful Swift code, but the underlying library is still a compiled static library for a specific target triple. You still need to cross-compile for every platform, create XCFrameworks, and manage per-platform build pipelines.

### Still no sandboxing

The generated Swift code calls into the Rust library through C FFI under the hood. The Rust code runs in the same process with full access to the host's memory and system calls. UniFFI improves the developer experience but does not change the trust model.

### Language-specific code generation

UniFFI must generate bindings for each target language separately. Supporting a new language requires building a new code generator. UniFFI officially supports Swift, Kotlin, Python, and Ruby, with community-contributed bindings for additional languages such as C#, Go, and others. However, each new language binding is a significant engineering effort, and community bindings vary in completeness and maintenance.

### Async gaps

Rust's `async fn` does not map cleanly through C FFI. UniFFI supports async function bridging, mapping Rust's `async fn` to Swift's `async` functions. However, the bridging still introduces complexity – runtime management and platform-specific event loop integration. The experience is improving but not yet as seamless as native `async`/`await` within a single language.

### Build pipeline complexity

UniFFI adds a code generation step to your build pipeline. The generated Swift code must be kept in sync with the Rust source. When the Rust API changes, the bindings must be regenerated, and the generated code checked in or rebuilt. This is manageable but adds friction, especially for teams where some developers work primarily in Swift and others in Rust.

## What the Component Model solves

The WebAssembly Component Model is a higher-level Wasm architecture that is being standardized for packaging compiled code into portable, sandboxed, composable modules with rich typed interfaces. Where C FFI strips types down to the lowest common denominator, the Component Model builds them up.

### Rich typed interfaces via WIT

The Component Model uses WIT (WebAssembly Interface Types) as its interface definition language. WIT supports strings, lists, options, results, variants, records, enums, flags, and more – types that map naturally to both Rust and Swift:

```wit
// WIT interface
package my:math@1.0.0;

interface compute {
    record statistics {
        mean: f64,
        median: f64,
        std-dev: f64,
    }

    hypotenuse: func(a: f64, b: f64) -> f64;
    compute-stats: func(values: list<f64>) -> result<statistics, string>;
}
```

This snippet shows just the interface definition. A complete WIT package would also include a `world` declaration that specifies which interfaces a component exports and imports – this is covered in detail in Chapter 33.

Compare this with the C FFI version of the same interface: WIT preserves the `result` type, uses a proper `list` instead of a pointer-and-length pair, and defines `statistics` as a structured record. The interface definition carries semantic information that C headers cannot express.

### Platform-independent modules

A WebAssembly component is compiled to a platform-independent binary format. The same `.wasm` artifact can be shipped across macOS, Linux, Windows, servers, and embedded hosts that have Component Model-aware runtimes or adapters. You compile once and distribute a single artifact; what changes is the host runtime, not the library binary.

This is a fundamental shift from the C FFI model, where you compile once per platform and architecture. For a library author, it means distributing one binary instead of a matrix of platform-specific builds.

### Sandboxing by default

WebAssembly components run in a sandboxed environment. A component cannot access the host's memory, file system, or network unless the host explicitly grants those capabilities. This is the opposite of C FFI, where linking a library gives it unrestricted access to your process.

For Swift developers, this is analogous to the difference between linking a C framework (full trust) and running an App Extension (sandboxed). The Component Model applies extension-level isolation to every component.

### Polyglot interop

Because WIT is language-independent, any language that can compile to WebAssembly components can interoperate through WIT interfaces. A component written in Rust can be called from Swift, Python, JavaScript, Go, or C# through the same WIT contract. In practice, hosts and toolchains still generate bindings or adapters from that WIT, but you no longer hand-design a separate ABI for each language.

The host runtime handles the translation between each language's native types and the Component Model's canonical ABI. The library author does not need to know which languages will consume their component.

### Composability

Components can be composed – linked together at the component level without recompiling. If component A exports an interface and component B imports the same interface, a tool like `wac` can wire them together into a new component. This enables plugin architectures, dependency injection, and modular deployment without shared memory or process-level linking.

## Comparing the three approaches

| Aspect | C FFI | UniFFI | Component Model |
|---|---|---|---|
| **Type richness** | C types only (integers, pointers, structs of the same) | Rich types generated per language (Result to throws, Vec to Array) | Rich types defined in WIT (strings, lists, options, results, variants, records) |
| **Memory safety at boundary** | Manual (pointer passing, manual free) | Managed by generated code, but still C FFI underneath | Enforced by sandbox (no shared memory) |
| **Platform dependency** | Platform-specific binary per target | Platform-specific binary per target | Single platform-independent `.wasm` binary |
| **Sandboxing** | None (full process access) | None (full process access) | Yes (capability-based, deny by default) |
| **Language support** | Any language with C FFI (nearly all) | Swift, Kotlin, Python, Ruby (requires per-language codegen) | Any language with Component Model tooling (growing) |
| **Async support** | Callbacks and manual threading | Supported (async fn bridging) | Evolving (async proposal in progress) |
| **Performance** | Native speed (no overhead) | Native speed (thin wrapper) | Near-native (Wasm execution overhead, copy at boundary) |
| **Build complexity** | Low (just compile and link) | Medium (code generation step) | Medium (Wasm compilation, host runtime required) |
| **Binary size** | Minimal additional size | Minimal + generated code | Wasm module size + host runtime |
| **Debugging** | Standard debugger (LLDB) | Standard debugger, generated code adds indirection | Limited (Wasm debugging is less mature) |
| **Maturity** | Decades of production use | Several years, widely adopted in Mozilla ecosystem | Actively developing, stabilizing rapidly |

## When to use which approach

### Use C FFI when

You need maximum performance with zero overhead, you are integrating with an existing C library, or you are working in a constrained environment where the WebAssembly runtime is not available. C FFI is also appropriate when you need fine-grained control over memory layout and calling conventions.

### Use UniFFI when

You are building a Rust library specifically for consumption by Swift (or Kotlin/Python) applications, you want idiomatic bindings without writing them by hand, and you are willing to manage per-platform builds. UniFFI is the pragmatic choice for most Rust-in-Swift-apps scenarios today.

### Use the Component Model when

You want to write a library once and use it everywhere, you need sandboxed execution, you want polyglot interop without per-language code generation, or you are building a plugin system where components from different authors need to be composed safely. The Component Model is the forward-looking choice for portable libraries.

## The practical transition

For a Swift developer evaluating these approaches, the progression often looks like:

1. **Start with UniFFI** for existing projects where you need Rust code in a Swift app today. UniFFI is mature, well-documented, and produces excellent Swift APIs.

2. **Learn the Component Model** for new libraries that need to be truly portable. If your Rust library does not depend on platform-specific APIs, compiling it as a WebAssembly component gives you a single binary artifact for hosts and toolchains that support the required component interfaces.

3. **Watch the tooling mature**. The Component Model's tooling for Apple platforms – hosting Wasm components in a Swift app – is still evolving. As runtimes like Wasmtime and WasmKit gain more complete Apple platform support, the Component Model will become increasingly practical for iOS and macOS apps.

The next part of this guide covers WebAssembly in detail: the core specification, Wasm targets and tooling, the Component Model and WIT, WASI, and running Wasm components on Apple platforms.

## Key differences and gotchas

**The Component Model is not a replacement for all FFI**: when you need to call a platform-specific API (like Core Animation or Metal), C FFI or UniFFI is still the right tool. The Component Model is designed for portable logic, not platform integration.

**Performance characteristics differ**: C FFI and UniFFI calls are essentially native function calls. Component Model calls cross a sandbox boundary and may involve copying data between the host and the component. For hot loops calling across the boundary millions of times per second, this overhead matters. For typical API calls, it is negligible.

**The ecosystem is at different maturity levels**: C FFI has decades of production use. UniFFI has several years and is used in Firefox. The Component Model is stabilizing rapidly but is younger. Evaluating maturity against your project's risk tolerance is important.

**Not all Rust crates compile to Wasm**: crates that use platform-specific system calls, inline assembly, or link to C libraries will not compile to `wasm32-wasip2` without modification. Pure Rust crates that do computation – parsing, serialization, cryptography, image processing – are the best candidates for the Component Model.

## Further reading

- [The Component Model specification](https://component-model.bytecodealliance.org/): the official design documentation
- [WIT format reference](https://component-model.bytecodealliance.org/design/wit.html): the interface definition language used by the Component Model
- [UniFFI User Guide](https://mozilla.github.io/uniffi-rs/): for the pragmatic approach to Rust-Swift interop today
- [Bytecode Alliance](https://bytecodealliance.org/): the organization stewarding the Component Model and related tooling
- [WebAssembly Component Model: A New Era for Wasm](https://www.fermyon.com/blog/component-model): an overview of the Component Model's goals and design
