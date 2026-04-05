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

## WASI 0.2: the baseline for these examples

The WASI 0.2.0 release arrived in early 2024 and established the Component Model interfaces used in this chapter. WASI 0.3 is now the current preview, but support varies across toolchains and runtimes. Unlike WASI 0.1/preview1’s lower-level imports, WASI 0.2 defines interfaces using WIT, covered in the [previous chapter](../component-model-and-wit/).

### Worlds

A central concept in WASI 0.2 is the **world**. A world is a WIT definition that specifies which interfaces a component can import (use) and which it must export (provide). Think of it as a contract between the component and its host.

WASI 0.2 defines several standard worlds:

- **`wasi:cli/command`**: a command-line world importing filesystem, environment, standard I/O, clocks, and random interfaces. The host controls which resources those interfaces expose.
- **`wasi:http/proxy`**: an HTTP handler that receives incoming requests and can make outgoing requests. This is designed for serverless and edge-computing environments.

Each world is composed of smaller interfaces. For example, `wasi:cli/command` imports `wasi:filesystem/types`, `wasi:clocks/wall-clock`, and `wasi:random/random`. You can define custom worlds with only the interfaces you need.

Here is a simplified sketch of the `wasi:cli/command` world; a real definition must resolve the matching WIT package dependencies:

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

Choose a `wasi` crate version that matches the interface generation you intend to use. Check its documentation for the supported WASI release and module layout rather than assuming the latest crate targets WASI 0.2.

## Capability-based security

WASI uses a **capability-based security model**: filesystem and network access are mediated by interfaces and handles supplied by the host. A runtime’s CLI may grant capabilities such as standard I/O, clocks, and randomness by default. Inspect the host configuration instead of assuming that omitting permission flags grants nothing.

When you run a WASI component, you choose what to grant:

```sh
# Grant access to a specific directory
wasmtime run --dir ./data my_component.wasm

# No filesystem preopen; other CLI defaults still apply
wasmtime run my_component.wasm
```

If a component tries to open a file it has no capability for, the call returns an error – it does not crash the host or escape the sandbox. Other capabilities, such as outgoing HTTP, are enabled through runtime-specific CLI flags or embedding-API configuration.

### Comparison to iOS sandboxing

Swift developers are familiar with the iOS app sandbox and privacy permissions for resources such as the camera and contacts. WASI similarly mediates access, but the embedding application configures the capabilities available to each component:

| Aspect | iOS sandbox | WASI capabilities |
|--------|------------|-------------------|
| **Default access** | App container and platform-defined services | Depends on host configuration |
| **Granting access** | Entitlements and user prompts | Host flags and preopens |
| **Granularity** | Per-app | Per-component invocation |
| **Enforcement** | OS kernel | Wasm runtime |
| **Revocation** | Platform permissions and settings | Requires host enforcement; omitting a new handle does not revoke an existing one |

Both models can limit access to the resources a program needs. With WASI, the host must configure those limits and avoid exposing imports that provide unintended access.

## WASI 0.1 vs 0.2

You may encounter references to `wasm32-wasi`, the older name for `wasm32-wasip1`. This is the WASI 0.1 target (also called "preview1"), which predates the Component Model:

- **WASI 0.1** (`wasm32-wasip1`, formerly `wasm32-wasi`): defines POSIX-like function imports directly. Simpler but limited – no rich types, no components, no composition.
- **WASI 0.2** (`wasm32-wasip2`): built on the Component Model and WIT. Supports rich types, multiple return values, resources, and interface composition.

For new component-based work, target `wasm32-wasip2`. Keep `wasm32-wasip1` in mind when you need preview1 compatibility with existing runtimes or toolchains.

## Beyond the examples in this chapter

The examples here use WASI 0.2. A different interface generation can require different bindings and a different runtime configuration. The [dated status appendix](../../appendices/wasm-status/#wasi-and-rust-target-support) records WASI 0.3 and Rust target support separately from these instructions.

## Key differences and gotchas

- **WASI is not POSIX**: although WASI 0.1 was inspired by POSIX, WASI 0.2 uses its own interface definitions. Not all POSIX functions have WASI equivalents, and the semantics may differ.
- **Support depends on both the target and the runtime**: `wasm32-wasip2` supports `std`, but functionality only works when the runtime implements and grants the relevant WASI interfaces. Check the [Rust WASI tier documentation](https://doc.rust-lang.org/rustc/platform-support/wasm32-wasip2.html) for current status.
- **Capabilities must be granted**: forgetting to pass `--dir` or a runtime-specific permission flag such as Wasmtime's `-S http` is a common source of "permission denied" errors when running WASI components. This is by design, not a bug.
- **`wasm32-wasip2` produces components**: the output is a Wasm component (with a component-model wrapper), not a raw core module. Some tools expect core modules – make sure your toolchain understands components.
- **`wasm32-wasi` is legacy**: if you see tutorials targeting `wasm32-wasi`, they are using WASI 0.1. The concepts still apply, but the interfaces and tooling have evolved.
- **Binary size**: components include type information and may contain adapters. Optimize core modules with `wasm-opt` before componentization; do not assume it accepts a component binary. Use component-aware tools for the final artifact.

## Further reading

- [WASI documentation](https://wasi.dev/): official WASI project site
- [WASI 0.2 specification](https://github.com/WebAssembly/WASI/tree/main/specifications): detailed interface definitions
- [Rust `wasm32-wasip2` platform support](https://doc.rust-lang.org/rustc/platform-support/wasm32-wasip2.html): Rust compiler documentation
- [`wasi` crate on crates.io](https://crates.io/crates/wasi): Rust bindings for WASI interfaces
- [Bytecode Alliance](https://bytecodealliance.org/): the organization driving WASI and related tooling
- [Component Model design](https://component-model.bytecodealliance.org/): Bytecode Alliance documentation on the Component Model
