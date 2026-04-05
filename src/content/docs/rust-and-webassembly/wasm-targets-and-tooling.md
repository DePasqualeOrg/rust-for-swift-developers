---
title: Wasm Targets and Tooling
sidebar:
  order: 32
---

Rust provides multiple built-in compilation targets for WebAssembly, each designed for a different execution environment.

## Rust's Wasm targets

Rust's compiler supports several Wasm targets out of the box. Each target produces a `.wasm` binary, but they differ in what system interfaces are available and what ABI conventions they use.

### wasm32-unknown-unknown

This is the most minimal target. It assumes nothing about the host environment – no operating system, no file system, no WASI. The resulting module can only interact with the outside world through explicitly imported and exported functions.

```bash
rustup target add wasm32-unknown-unknown
cargo build --target wasm32-unknown-unknown
```

This target is primarily used for browser-based Wasm, where JavaScript provides all external functionality through imports. It is also used for situations where you want a completely self-contained module with no system dependencies.

Limitations: no access to `std::fs`, `std::net`, `std::env`, or anything else that assumes an operating-system interface. You can still use much of `std` (strings, collections, formatting), but there is no built-in filesystem, process, or networking layer.

### wasm32-wasip1

This target compiles against WASI preview 1 – the first stable snapshot of the WebAssembly System Interface. It provides access to file I/O, environment variables, command-line arguments, clocks, and random number generation through a capability-based API.

```bash
rustup target add wasm32-wasip1
cargo build --target wasm32-wasip1
```

Modules compiled for this target can be run on runtimes that implement WASI preview1 (for example Wasmtime, Wasmer, or WasmEdge). This remains the common target for CLI-style Wasm modules that need today's broadly deployed WASI story.

The older name for this target was `wasm32-wasi`. If you see that name in documentation or blog posts, it refers to the same thing – it was renamed to `wasm32-wasip1` to distinguish it from the newer WASI preview 2.

### wasm32-wasip2

This is the target for the Component Model and WASI preview 2. It produces Wasm components (not just core modules) with support for the full WIT type system, including strings, lists, records, variants, options, results, and resources.

```bash
rustup target add wasm32-wasip2
cargo build --target wasm32-wasip2
```

This is the target you want for building portable libraries with rich typed interfaces. The output is a Wasm component that can be consumed from hosts and languages that have Component Model tooling.

This target is available in stable Rust and is Tier 2 in the upstream compiler, but the Rust platform-support docs still describe it as a new, experimental target and note that the Rust project does not test it in CI. In practice, that means it is usable today, but you should still expect some tooling rough edges.

WASI preview 2 includes the core ideas of preview 1 (filesystem, clocks, random, and related host capabilities) but expresses them through WIT interfaces instead of the legacy WASI function signatures. Most new WASI interface work targets preview 2 and beyond rather than preview 1.

### wasm32-wasip1-threads

This target extends `wasm32-wasip1` with support for shared memory and the Wasm threads proposal. It enables `std::thread`, atomics, and `Mutex`/`RwLock` in Wasm modules.

```bash
rustup target add wasm32-wasip1-threads
cargo build --target wasm32-wasip1-threads
```

Threading support in Wasm is still limited. Not all runtimes support it, and Rust's own target documentation describes this target as experimental and in flux. Use it only when you control the runtime and know it supports the relevant threading proposals.

### Choosing a target

| Target | Use case | System access | Output |
|---|---|---|---|
| `wasm32-unknown-unknown` | Browser, minimal sandbox | None | Core module |
| `wasm32-wasip1` | CLI tools, server-side, legacy WASI | WASI preview 1 | Core module |
| `wasm32-wasip2` | Portable libraries, Component Model | WASI preview 2 | Component |
| `wasm32-wasip1-threads` | Multi-threaded workloads | WASI preview 1 + threads | Core module |

For the goals described in this guide – building portable libraries that can be consumed from any language – `wasm32-wasip2` is the primary target.

## Tools

### wasm-pack

[wasm-pack](https://rustwasm.github.io/wasm-pack/) is a tool for building Rust-generated Wasm packages intended for use in JavaScript environments (browsers and Node.js). It compiles your Rust code, runs `wasm-bindgen` to generate JavaScript glue code, and packages the result as an npm module.

```bash
# Install
cargo install wasm-pack

# Build for the browser
wasm-pack build --target web

# Build for Node.js
wasm-pack build --target nodejs
```

`wasm-pack` uses `wasm-bindgen` under the hood, which generates the FFI layer between Rust and JavaScript. It handles converting Rust types to JavaScript types (strings, arrays, objects) and generates TypeScript type definitions.

If your goal is browser integration, `wasm-pack` is the standard tool. If your goal is portable components that work across languages (not just JavaScript), `cargo-component` is the better choice.

### cargo-component

[cargo-component](https://github.com/bytecodealliance/cargo-component) is a Cargo subcommand for building Wasm components using the Component Model. It manages WIT definitions, generates Rust bindings, and produces `.wasm` components.

```bash
# Install
cargo install cargo-component --locked

# Create a new component project
cargo component new --lib my-library

# Build the component
cargo component build --release
```

`cargo-component` integrates with Cargo's build system. It reads WIT files from your project, generates Rust bindings at build time using `wit-bindgen`, and packages the result as a Wasm component. It is especially useful when you are defining custom WIT worlds or depending on other components, even though the upstream `wasm32-wasip2` target also exists.

`cargo-component` is extremely useful in practice, but its own README still describes it as experimental while the component model continues to stabilize. Budget for occasional breaking changes between releases.

One subtle but important detail: current `cargo-component` releases still build a `wasm32-wasip1` core module first and then adapt it into a preview2 component. Plain `cargo build --target wasm32-wasip2` uses the upstream compiler target directly. That is why the two workflows overlap, but do not produce identical build layouts or capabilities.

If you only need WASI interfaces, plain `wasm32-wasip2` plus the `wasi` crate may be the simpler path. Reach for `cargo-component` when custom or third-party WIT worlds enter the picture.

### wasm-tools

[wasm-tools](https://github.com/bytecodealliance/wasm-tools) is a Swiss Army knife for working with Wasm binaries. It is maintained by the Bytecode Alliance and includes subcommands for inspecting, validating, and transforming Wasm modules and components. For component-to-component composition, pair it with [`wac`](https://github.com/bytecodealliance/wac), the dedicated composition CLI.

```bash
# Install
cargo install wasm-tools

# Print the text representation of a Wasm binary
wasm-tools print module.wasm

# Validate a Wasm binary
wasm-tools validate module.wasm

# Inspect a component's WIT interface
wasm-tools component wit my-component.wasm

# Convert a core module into a component
wasm-tools component new core-module.wasm -o component.wasm

# Compose two components together
wac plug component-a.wasm --plug component-b.wasm -o composed.wasm
```

The `component wit` subcommand is particularly useful during development. It extracts the WIT interface from a compiled component, letting you verify that your component exposes the types and functions you expect.

### wasm-opt

[wasm-opt](https://github.com/WebAssembly/binaryen) is part of the Binaryen toolkit and focuses on optimizing Wasm binary size and performance. It applies a series of optimization passes that go beyond what the Rust compiler does.

```bash
# Install via Homebrew on macOS
brew install binaryen

# Optimize for size
wasm-opt -Oz input.wasm -o output.wasm

# Optimize for speed
wasm-opt -O3 input.wasm -o output.wasm
```

Binary size matters for Wasm, especially when modules are loaded over the network. A typical Rust Wasm module compiled with `--release` and `lto = true` might be 100–500 KB. Running `wasm-opt -Oz` can reduce that by 10–30%. For browser-targeted Wasm, this optimization step is worth including in your build pipeline.

Common `Cargo.toml` settings for minimizing Wasm binary size:

```toml
[profile.release]
opt-level = "z"    # optimize for size
lto = true         # link-time optimization
codegen-units = 1  # better optimization at the cost of compile time
strip = true       # strip debug symbols
```

### wasmtime CLI

[Wasmtime](https://wasmtime.dev/) is both a library and a command-line tool for running Wasm modules and components. The CLI is useful for testing your modules locally without setting up a browser or deployment target.

```bash
# Install via Homebrew on macOS
brew install wasmtime

# Or via the official installer
curl https://wasmtime.dev/install.sh -sSf | bash

# Run a WASI module
wasmtime run my-module.wasm

# Run a component
wasmtime run my-component.wasm

# Pass command-line arguments
wasmtime run my-module.wasm -- arg1 arg2

# Grant file system access
wasmtime run --dir ./data my-module.wasm
```

Wasmtime supports both core modules (compiled for `wasm32-wasip1`) and components (compiled for `wasm32-wasip2`). The `--dir` flag grants access to a directory on the host file system – an example of WASI's capability-based security model.

## Practical example: building a Wasm component

Let's walk through building a simple Rust library as a Wasm component using `cargo-component`. This example creates a string-processing library that exposes a `slugify` function – the kind of utility you might want to share across web, server, and native applications.

### 1. Create the project

```bash
cargo component new --lib string-utils
cd string-utils
```

This creates a project with the following structure:

```
string-utils/
  Cargo.toml
  wit/
    world.wit
  src/
    lib.rs
```

### 2. Define the WIT interface

Edit `wit/world.wit` to define the component's interface:

```wit
package example:string-utils@0.1.0;

interface processing {
    slugify: func(input: string) -> string;
    word-count: func(input: string) -> u32;
    truncate: func(input: string, max-length: u32, suffix: string) -> string;
}

world string-utils {
    export processing;
}
```

This WIT file declares a `processing` interface with three functions and a world that exports it. WIT syntax and semantics are covered in detail in [Chapter 33](../component-model-and-wit/).

### 3. Implement the component in Rust

Edit `src/lib.rs`:

```rust
// Generated bindings from the WIT file
mod bindings;

use bindings::exports::example::string_utils::processing::Guest;

struct Component;

impl Guest for Component {
    fn slugify(input: String) -> String {
        input
            .to_lowercase()
            .chars()
            .map(|c| {
                if c.is_ascii_alphanumeric() {
                    c
                } else {
                    '-'
                }
            })
            .collect::<String>()
            // Collapse consecutive dashes
            .split('-')
            .filter(|s| !s.is_empty())
            .collect::<Vec<_>>()
            .join("-")
    }

    fn word_count(input: String) -> u32 {
        input.split_whitespace().count() as u32
    }

    fn truncate(input: String, max_length: u32, suffix: String) -> String {
        let max = max_length as usize;
        let suffix_chars = suffix.chars().count();
        if input.chars().count() <= max {
            input
        } else if suffix_chars >= max {
            suffix.chars().take(max).collect()
        } else {
            let end = max - suffix_chars;
            let truncated: String = input.chars().take(end).collect();
            format!("{truncated}{suffix}")
        }
    }
}

bindings::export!(Component with_types_in bindings);
```

A few things to note about this code:

- `cargo-component` generates the `bindings` module from the WIT file at build time. The `Guest` trait corresponds to the `processing` interface – each WIT function becomes a trait method.
- The `export!` macro at the bottom wires the `Component` struct to the generated bindings.
- WIT `string` maps to Rust's `String`. WIT `u32` maps to Rust's `u32`. The binding generator handles the conversions through the Canonical ABI.

### 4. Build the component

```bash
cargo component build --release
```

The output is a `.wasm` component under Cargo's `target/` directory. With plain `cargo build --target wasm32-wasip2`, that is typically under `target/wasm32-wasip2/<profile>/`. With current `cargo component build` releases, the artifact is commonly placed under a `wasm32-wasip1` target directory because the tool still componentizes a preview1 core module under the hood.

### 5. Inspect the component

Use `wasm-tools` to verify the component's interface:

```bash
wasm-tools component wit <path-to-string_utils.wasm>
```

This prints the WIT interface extracted from the binary, confirming that the component exports the functions you defined.

### 6. Test with Wasmtime

For a library component like this, you would typically consume it from a host application or compose it with other components. But you can also create a command component that uses it for quick testing. In practice, testing during development usually happens through Rust's standard `cargo test` (which runs natively, not in Wasm) and integration tests that embed the component in a Wasmtime host.

## Comparison with Swift tooling

If you are used to building Swift libraries for multiple platforms, here is how the Wasm workflow compares:

| Concept | Swift | Rust / Wasm |
|---|---|---|
| Cross-compilation | Xcode build settings, `--destination` | `--target wasm32-wasip2` |
| Package format | `.framework`, `.xcframework` | `.wasm` component |
| Interface definition | Swift module interface (`.swiftinterface`) | WIT file (embedded in component) |
| Binary optimization | Xcode build settings, `strip` | `wasm-opt`, `Cargo.toml` profile settings |
| Running locally | Simulator, device, `swift run` | `wasmtime run` |
| Package manager | SPM | Cargo + `cargo-component` |

The most significant difference is that a Wasm component is designed to be portable. An `.xcframework` works on Apple platforms. A `.wasm` component can work anywhere a compatible runtime or toolchain exists, though in practice server-side tooling is ahead of browser-native component support.

## Key differences and gotchas

- **Target confusion**: `wasm32-unknown-unknown` and `wasm32-wasip1` produce core modules. The upstream compiler target that produces components is `wasm32-wasip2`, while current `cargo-component` releases still build a preview1 core module and adapt it into a component. Be explicit about which workflow you are using.
- **Not all crates compile to Wasm**: crates that use OS-specific APIs (raw system calls, platform-specific networking) will not compile for any Wasm target. Check crate documentation for Wasm compatibility, and look for `#[cfg(target_arch = "wasm32")]` or `#[cfg(not(target_arch = "wasm32"))]` blocks in the source.
- **Binary size**: Rust Wasm binaries are small compared to languages with managed runtimes, but they can still be larger than expected if you pull in heavy dependencies. Use [`twiggy`](https://rustwasm.github.io/twiggy/) (e.g., `twiggy top my_lib.wasm`) to identify what contributes to binary size – it is purpose-built for Wasm binary analysis.
- **Debug builds are large**: always use `--release` for Wasm. Debug Wasm binaries include debug info and unoptimized code, making them much larger and slower.
- **No threads by default**: the `wasm32-wasip2` and `wasm32-unknown-unknown` targets do not support `std::thread`. If you need threading, use `wasm32-wasip1-threads`, but be aware that not all runtimes support it.
- **`cargo-component` vs `cargo build`**: plain `cargo build --target wasm32-wasip2` works well for straightforward WASI 0.2 components. Use `cargo component build` when you need custom WIT worlds, component dependencies, or the higher-level workflow it provides.

## Further reading

- [Rust and WebAssembly book](https://rustwasm.github.io/docs/book/): the official guide (browser-focused)
- [wasm-pack documentation](https://rustwasm.github.io/wasm-pack/): building Wasm for JavaScript
- [cargo-component repository](https://github.com/bytecodealliance/cargo-component): building Wasm components
- [wasm-tools repository](https://github.com/bytecodealliance/wasm-tools): inspecting and manipulating Wasm binaries
- [Binaryen / wasm-opt](https://github.com/WebAssembly/binaryen): Wasm binary optimizer
- [Wasmtime documentation](https://docs.wasmtime.dev/): the reference Wasm runtime
- [Wasmer documentation](https://docs.wasmer.io/): an alternative Wasm runtime
- [min-sized-rust](https://github.com/johnthagen/min-sized-rust): techniques for reducing Rust binary size (applicable to Wasm)
