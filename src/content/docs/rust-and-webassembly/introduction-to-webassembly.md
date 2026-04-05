---
title: Introduction to WebAssembly
sidebar:
  order: 31
---

WebAssembly (Wasm) is a portable binary instruction format designed to run at near-native speed across any platform that has a Wasm runtime. If you have built Swift libraries that you wish you could use outside of Apple's ecosystem – on the web, on a Linux server, at the edge, or inside another application as a plugin – Wasm gives you a realistic path to do that.

## What WebAssembly is

At its core, Wasm is a compilation target. You write code in a high-level language (Rust, C, C++, or others), compile it to the `.wasm` binary format, and run it on a runtime that implements the Wasm specification. The result is a sandboxed execution environment whose behavior is designed to be portable across hosts, subject to the capabilities the host chooses to expose.

Wasm was originally designed for the web – browser engines in Chrome, Firefox, Safari, and Edge all include Wasm runtimes. But the format was intentionally designed to be host-agnostic. The spec defines a stack-based virtual machine with linear memory, structured control flow, and a minimal set of value types. There is no assumption about a browser, a DOM, or JavaScript in the core specification.

### Design goals

The Wasm specification was shaped by four principles:

- **Safe**: Wasm modules execute in a sandboxed environment. They cannot access the host's memory, file system, or network unless the host explicitly grants those capabilities. This is security by default – the opposite of native code, which has full access to everything the process can touch.
- **Fast**: the binary format is designed for efficient validation, compilation, and execution. Wasm runtimes can compile modules ahead of time or just-in-time, achieving performance within a small factor of native code.
- **Portable**: a `.wasm` binary runs on any compliant runtime without recompilation. The same module works in a browser, on a server, and on an embedded device.
- **Compact**: the binary format is dense. Wasm modules are typically smaller than equivalent native binaries and much smaller than the source code that produced them.

For Swift developers, the sandboxing model is worth emphasizing. Unlike linking a dynamic library or embedding a framework, loading a Wasm module carries minimal trust requirements. The module can only do what you allow it to do through explicitly imported functions. This makes Wasm a natural fit for plugin systems, user-submitted code execution, and multi-tenant environments.

## Wasm beyond the browser

Although Wasm originated in the browser, its most interesting growth is happening elsewhere. Several ecosystems have adopted Wasm as a portable execution format.

### WASI: the WebAssembly System Interface

[WASI](https://wasi.dev/) is a standardized set of APIs that give Wasm modules access to system capabilities like file I/O, environment variables, clocks, and random number generation. WASI is to Wasm what POSIX is to Unix: a portable interface to the operating system.

Without WASI, a Wasm module running outside the browser has no way to read a file, write to stdout, or get the current time – the sandbox is completely sealed. WASI opens controlled holes in that sandbox through a capability-based security model. The host decides which capabilities to grant, and the module can only use what it is given.

WASI is covered in detail in [Chapter 34](../wasi/).

### Server-side runtimes

Standalone Wasm runtimes let you execute `.wasm` binaries from the command line or embed them in a host application:

- **Wasmtime**: the reference implementation from the Bytecode Alliance. It is written in Rust, supports WASI and the Component Model, and is designed for production use in server-side and embedded scenarios.
- **Wasmer**: another production-grade runtime with multiple compiler backends and language-specific embedding SDKs.

Both runtimes can be embedded as libraries in Rust, C, Python, Go, and other languages, allowing you to load and execute Wasm modules from within your own application.

### Edge computing

Platforms such as Cloudflare Workers and Fastly Compute have used Wasm as part of their edge execution story. You compile your application to Wasm, deploy it, and it runs close to users on infrastructure you do not manage. One of Wasm's appeals here is low startup overhead compared to heavier deployment units like containers or virtual machines.

### Plugin systems

Wasm's sandboxing makes it an excellent foundation for plugin and extension architectures. The host application loads third-party Wasm modules, provides them with a controlled API, and runs them with far tighter isolation than a native plugin. Projects like Zed use Wasm for extensions, and Envoy uses Wasm for filters. Platforms such as Fermyon Spin use Wasm more broadly as the unit of deployment for server-side applications.

This is conceptually similar to how some Swift applications use XPC services or app extensions for isolation, but Wasm provides a language-agnostic, cross-platform mechanism.

### Embedded runtimes

Lightweight Wasm runtimes like Wasm3 and WAMR (WebAssembly Micro Runtime) target embedded systems and IoT devices. These runtimes have tiny memory footprints and can run on microcontrollers, making Wasm a viable format even in resource-constrained environments.

## Why Rust is one of the best Wasm languages

Several properties make Rust unusually well-suited for Wasm:

- **No garbage collector or large managed runtime**: Rust compiles to Wasm without shipping a GC or heavyweight managed runtime. That often leads to small binaries relative to GC-based languages, though the exact size still depends heavily on your panic strategy, allocator, standard-library usage, and dependencies.
- **Predictable performance**: Rust's zero-cost abstractions and lack of GC pauses translate directly to Wasm. There is no hidden overhead from reference counting or garbage collection cycles.
- **Mature tooling**: the Rust Wasm ecosystem is one of the most developed. Tools like `wasm-pack`, `cargo-component`, `wasm-bindgen`, and `wasm-tools` provide a complete workflow from source code to deployable Wasm binaries.
- **First-class compiler support**: the Rust compiler has multiple built-in Wasm targets (`wasm32-unknown-unknown`, `wasm32-wasip1`, `wasm32-wasip2`) maintained by the Rust project itself, not third-party forks.
- **Strong community and ecosystem**: a large number of Rust crates are designed to work in Wasm environments, and many are tested against Wasm targets in CI. The crate ecosystem has good coverage for `no_std` and Wasm-compatible libraries.

Swift's Wasm story is no longer purely experimental: Swift 6.2 added official WebAssembly support, and the current Swift.org Wasm SDK workflow uses WasmKit in recent compatible toolchains and snapshots on macOS and Linux. Rust's ecosystem is still broader for portable libraries, though, especially around Component Model tooling, server-side runtimes, and cross-language interop. For a Swift developer who wants to ship portable Wasm libraries today, writing the Wasm-targeted code in Rust and consuming it from Swift via FFI or an embedded runtime is still often the more practical path.

## Wasm modules vs Wasm components

The Wasm specification defines **core modules** – the low-level binary format with linear memory, functions, tables, and low-level value types. Core modules can import and export numbers, vectors, references, and multiple return values, but there is still no native concept of strings, lists, records, or other language-level types. Passing complex data between a core module and its host usually still requires manual memory management: the host writes bytes into the module's linear memory, passes a pointer and length, and the module interprets those bytes according to a convention agreed upon out-of-band.

This is workable, but fragile. It is essentially FFI with all of FFI's problems – ABI compatibility, manual serialization, version mismatch risks, and no self-describing interfaces.

The **Component Model** is a higher-level architecture being standardized on top of core Wasm modules that solves these problems. A Wasm component:

- Has a typed interface described in [WIT (WebAssembly Interface Types)](../component-model-and-wit/): a language for defining rich types like strings, lists, records, variants, options, results, and resources
- Can import and export functions with these rich types, not just integers
- Is self-describing: the interface is embedded in the binary, so a host or another component can inspect it without any external documentation
- Can be composed with other components: you can link two components together at the interface level without sharing memory

Today, the most complete Component Model implementations are in the Bytecode Alliance toolchain, especially Wasmtime and related tools. Browser-native support is still less mature.

For Swift developers, the distinction maps roughly to the difference between calling C functions through a bridging header (core modules) and calling a well-typed Swift API defined by a protocol (components). The Component Model gives Wasm the type safety and composability that makes it practical for real library distribution.

The Component Model and WIT are covered in depth in [Chapter 33](../component-model-and-wit/).

## The Bytecode Alliance

The [Bytecode Alliance](https://bytecodealliance.org/) is a nonprofit organization that stewards much of the Wasm ecosystem outside of the browser. Its members include Fastly, Intel, Microsoft, and others. The Bytecode Alliance maintains:

- **Wasmtime**: the reference Wasm runtime
- **Cranelift**: a code generator used by Wasmtime (and also available as a Rust compiler backend)
- **wasm-tools**: a suite of CLI tools for working with Wasm binaries
- **wit-bindgen**: a tool for generating language bindings from WIT definitions
- **cargo-component**: a Cargo subcommand for building Wasm components from Rust
- **WASI implementations, adapters, and tooling**: much of the day-to-day WASI ecosystem outside the browser

If you are coming from the Apple ecosystem, think of the Bytecode Alliance as playing a role somewhat similar to the institutions around Swift: hosting many of the reference implementations and maintaining much of the core tooling. The difference is that the Bytecode Alliance is an open, multi-stakeholder organization, and the specifications are developed collaboratively across companies and standards groups.

## The value proposition for Swift developers

If you are a Swift developer, you likely have libraries – parsers, formatters, encoders, state machines, algorithms – that are useful beyond Apple platforms. Today, porting those libraries to other ecosystems means rewriting them in another language or maintaining multiple implementations.

Rust with WebAssembly offers a different path:

1. **Write the core logic in Rust**: a language with similar expressiveness and safety to Swift
2. **Compile to a Wasm component**: package it with a well-typed WIT interface
3. **Consume the component from any language**: JavaScript, Python, Go, or Swift through a runtime or toolchain that understands the Component Model

The same Wasm binary can be reused across platforms without recompilation whenever the host runtime or toolchain supports the required component interfaces. The WIT interface serves as the contract, and language-specific bindings can be generated automatically.

This is no longer purely theoretical. Wasm is already used widely in production, and component-model-based workflows are becoming practical for real library distribution. The remaining chapters in this part walk through the tools, the Component Model, WASI, and running Wasm on Apple platforms.

## Key differences and gotchas

- **Wasm is not JavaScript**: Wasm runs alongside JavaScript in browsers but is a separate technology with its own binary format and execution model. It does not require JavaScript, and many of its most interesting use cases are outside the browser entirely.
- **Wasm is not an assembly language**: despite the name, Wasm is a high-level bytecode format that is validated and type-checked before execution. It is closer to the JVM bytecode model than to x86 assembly.
- **Sandboxing is strict by default**: a Wasm module cannot access the file system, network, or environment unless the host explicitly provides those capabilities through imported functions or WASI.
- **Core modules still expose low-level types**: core Wasm has more than just integers and floats now, but it still does not natively model strings, lists, records, or results. The Component Model adds those richer interface types on top.
- **Wasm is single-threaded by default**: the core Wasm specification has no threading model. The threads proposal (used by `wasm32-wasip1-threads` in Rust) adds shared memory and atomics but is not universally supported.
- **Not all Rust crates work in Wasm**: crates that depend on OS-specific functionality (file I/O, networking, process spawning) will not compile for `wasm32-unknown-unknown`. They may work with WASI targets if they use WASI-compatible APIs.

## Further reading

- [WebAssembly specification](https://webassembly.github.io/spec/): the official spec
- [WebAssembly on MDN](https://developer.mozilla.org/en-US/docs/WebAssembly): Mozilla's introduction and reference
- [Bytecode Alliance](https://bytecodealliance.org/): the organization behind Wasmtime, WASI, and the Component Model
- [WASI](https://wasi.dev/): the WebAssembly System Interface
- [Component Model specification](https://github.com/WebAssembly/component-model): the repository for the Component Model proposal
- [Rust and WebAssembly book](https://rustwasm.github.io/docs/book/): the official guide to using Rust with Wasm (focused on browser use cases)
- [Getting Started with Swift SDKs for WebAssembly](https://www.swift.org/documentation/articles/wasm-getting-started.html): official Swift.org guide to the Wasm SDK workflow
- [SwiftWasm](https://swiftwasm.org/): Swift's Wasm support project
