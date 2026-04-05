---
title: WASI
sidebar:
  order: 34
---

WebAssembly was designed as a sandboxed execution environment with no built-in access to the outside world. A Wasm module cannot read a file, open a network connection, or even get the current time unless the host explicitly provides those capabilities. WASI – the WebAssembly System Interface – fills this gap by defining standardized APIs for operating-system-level functionality. For Swift developers exploring Rust as a path to portable libraries, WASI is the layer that lets your Wasm code do useful work beyond pure computation.

## What WASI is and why it exists

A core Wasm module has no built-in filesystem, network, clock, or process model. It can interact with the outside world only through imports supplied by the host. This is fine for a math library or an image encoder, but most real software needs I/O – reading configuration files, making HTTP requests, generating random numbers, or querying the system clock.

Before WASI, each Wasm host provided its own ad-hoc imports. A module written for the browser used JavaScript glue to access `fetch` or `Date.now()`. A module running on a server used host-specific imports from Wasmtime or Wasmer. This made Wasm modules non-portable across hosts, defeating one of WebAssembly's primary goals.

WASI solves this by defining a set of standard interfaces that runtimes can implement. In principle, a module targeting a particular WASI release can run across hosts that support that same release. In practice, you still need to verify which WASI version, worlds, and interfaces a given runtime implements. The interfaces cover common system functionality:

- **Filesystem**: reading and writing files, listing directories
- **Clocks**: wall-clock time and monotonic timers
- **Random**: cryptographically secure random number generation
- **HTTP**: outgoing HTTP requests
- **Sockets**: TCP and UDP networking
- **I/O streams**: stdin, stdout, stderr

## WASI 0.2: the current stable line

WASI 0.2 is the first stable WASI release built on the Component Model. The initial 0.2.0 release landed in early 2024, and the 0.2.x line remains the stable foundation for component-based WASI tooling. Rather than defining raw function imports (as the earlier WASI 0.1 / "preview1" did), WASI 0.2 defines its interfaces using WIT (WebAssembly Interface Types), the same interface definition language covered in the [previous chapter](../component-model-and-wit/).

### Worlds

A central concept in WASI 0.2 is the **world**. A world is a WIT definition that specifies which interfaces a component can import (use) and which it must export (provide). Think of it as a contract between the component and its host.

WASI 0.2 defines several standard worlds:

- **`wasi:cli`**: a command-line program that has access to filesystem, environment variables, stdin/stdout, clocks, and random. This is the closest analogue to a traditional Unix process.
- **`wasi:http/proxy`**: an HTTP handler that receives incoming requests and can make outgoing requests. This is designed for serverless and edge-computing environments.

Each world is composed of smaller interfaces. For example, `wasi:cli` imports `wasi:filesystem/types`, `wasi:clocks/wall-clock`, `wasi:random/random`, and others. You can also define custom worlds that import only the interfaces you need.

Here is a simplified view of what `wasi:cli` looks like in WIT:

```wit
// A simplified sketch of the wasi:cli world
world cli {
    import wasi:filesystem/types;
    import wasi:filesystem/preopens;
    import wasi:clocks/wall-clock;
    import wasi:clocks/monotonic-clock;
    import wasi:random/random;
    import wasi:io/streams;
    import wasi:cli/stdin;
    import wasi:cli/stdout;
    import wasi:cli/stderr;
    import wasi:cli/environment;

    export wasi:cli/run;
}
```

### Building a WASI component in Rust

Rust supports WASI 0.2 through the `wasm32-wasip2` target. The target supports `std`, but it requires a runtime that understands both components and WASI preview2. To build a simple CLI program:

```sh
# Add the target (one-time setup)
rustup target add wasm32-wasip2

# Build for WASI 0.2
cargo build --target wasm32-wasip2
```

Your Rust code can use standard library APIs like `std::fs`, `std::io`, and `std::time`, and the compiler will route them through the appropriate WASI interfaces. For example, this standard Rust program compiles and runs as a WASI component:

```rust
use std::fs;

fn main() {
    match fs::read_to_string("config.toml") {
        Ok(contents) => println!("Config:\n{contents}"),
        Err(e) => eprintln!("Failed to read config: {e}"),
    }
}
```

```sh
# Run it with Wasmtime, granting access to the current directory
wasmtime run --dir . target/wasm32-wasip2/debug/my_app.wasm
```

Notice the `--dir .` flag – the runtime does not automatically give the component access to the filesystem. You must explicitly grant it. This leads to one of WASI's most important properties.

### Using WASI-specific APIs

For functionality beyond what the standard library covers – such as outgoing HTTP requests – you typically add the `wasi` crate or generate bindings from the upstream WIT packages:

```sh
cargo add wasi
```

The `wasi` crate exposes WASI 0.2 interfaces as Rust bindings. Its exact module layout evolves along with the spec and tooling, so it is better to check the current crate docs than to cargo-cult an import path from an older tutorial.

## Capability-based security

WASI uses a **capability-based security model**. A component cannot access any system resource unless the host explicitly grants it a handle (a capability) to that resource. There is no ambient authority – no global filesystem access, no unrestricted network, no environment variable access by default.

When you run a WASI component, you choose what to grant:

```sh
# Grant access to a specific directory
wasmtime run --dir ./data my_component.wasm

# Grant nothing – pure computation only
wasmtime run my_component.wasm
```

If a component tries to open a file it has no capability for, the call returns an error – it does not crash the host or escape the sandbox. Other capabilities, such as outgoing HTTP, are enabled through runtime-specific CLI flags or embedding-API configuration.

### Comparison to iOS sandboxing

Swift developers are familiar with iOS's sandbox model, where each app has access to its own container and must request entitlements for additional capabilities (camera, location, contacts). WASI's capability model is conceptually similar but more granular:

| Aspect | iOS sandbox | WASI capabilities |
|--------|------------|-------------------|
| **Default access** | Own container directory | Nothing |
| **Granting access** | Entitlements and user prompts | Host flags and preopens |
| **Granularity** | Per-app | Per-component invocation |
| **Enforcement** | OS kernel | Wasm runtime |
| **Revocation** | Settings app | Don't pass the capability |

The philosophical alignment is strong: both models assume code should have the minimum access necessary. But WASI is even more restrictive by default – a component starts with zero capabilities, while an iOS app starts with access to its own sandbox.

## WASI 0.1 vs 0.2

You may encounter references to `wasm32-wasi`, the older name for `wasm32-wasip1`. This is the WASI 0.1 target (also called "preview1"), which predates the Component Model:

- **WASI 0.1** (`wasm32-wasip1`, formerly `wasm32-wasi`): defines POSIX-like function imports directly. Simpler but limited – no rich types, no components, no composition.
- **WASI 0.2** (`wasm32-wasip2`): built on the Component Model and WIT. Supports rich types, multiple return values, resources, and interface composition.

For new component-based work, target `wasm32-wasip2`. Keep `wasm32-wasip1` in mind when you need preview1 compatibility with existing runtimes or toolchains.

## WASI 0.3 and the path forward

WASIp3 is still in development and is focused primarily on adding native async concepts to the Component Model. The additions being explored include:

- **`stream<T>`**: an asynchronous stream of values, similar to Rust's `Stream` ecosystem or Swift's `AsyncSequence`
- **`future<T>`**: a single asynchronous value, similar to a Rust `Future` or a Swift `async` return value

These primitives will allow components to express asynchronous operations in their WIT interfaces without blocking the host runtime. For example, an HTTP handler could stream response bodies incrementally rather than buffering the entire response in memory.

Rust now has an upstream `wasm32-wasip3` target, but the current platform-support docs still describe it as Tier 3, note that WASIp3 itself is not yet approved, and say that extra patching is currently required before the target builds. Treat it as an experiment rather than a production target. Beyond WASI 0.3, the project aims for a WASI 1.0 release that stabilizes the core set of interfaces for long-term compatibility.

## Key differences and gotchas

- **WASI is not POSIX**: although WASI 0.1 was inspired by POSIX, WASI 0.2 uses its own interface definitions. Not all POSIX functions have WASI equivalents, and the semantics may differ.
- **Support depends on both the target and the runtime**: `wasm32-wasip2` supports `std`, but functionality only works when the runtime implements and grants the relevant WASI interfaces. Check the [Rust WASI tier documentation](https://doc.rust-lang.org/rustc/platform-support/wasm32-wasip2.html) for current status.
- **Capabilities must be granted**: forgetting to pass `--dir` or a runtime-specific permission flag such as Wasmtime's `-S http` is a common source of "permission denied" errors when running WASI components. This is by design, not a bug.
- **`wasm32-wasip2` produces components**: the output is a Wasm component (with a component-model wrapper), not a raw core module. Some tools expect core modules – make sure your toolchain understands components.
- **`wasm32-wasi` is legacy**: if you see tutorials targeting `wasm32-wasi`, they are using WASI 0.1. The concepts still apply, but the interfaces and tooling have evolved.
- **Binary size**: WASI components include interface metadata and may be larger than equivalent core modules. Tools like `wasm-opt` and `wasm-tools strip` can help reduce size.

## Further reading

- [WASI documentation](https://wasi.dev/): official WASI project site
- [WASI 0.2 specification](https://github.com/WebAssembly/WASI/blob/main/wasip2/README.md): detailed interface definitions
- [Rust `wasm32-wasip2` platform support](https://doc.rust-lang.org/rustc/platform-support/wasm32-wasip2.html): Rust compiler documentation
- [`wasi` crate on crates.io](https://crates.io/crates/wasi): Rust bindings for WASI interfaces
- [Bytecode Alliance](https://bytecodealliance.org/): the organization driving WASI and related tooling
- [Component Model design](https://component-model.bytecodealliance.org/): Bytecode Alliance documentation on the Component Model
