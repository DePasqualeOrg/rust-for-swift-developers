---
title: Introduction to WebAssembly
sidebar:
  order: 31
---

WebAssembly (Wasm) is a binary instruction format that a runtime can validate and execute. Rust can compile to it, just as it can compile to a native machine-code target. The difference is that a Wasm program runs against an explicitly supplied host environment rather than directly against an operating system’s native ABI.

## From source to execution

A typical deployment has three parts:

1. A compiler translates the program into a `.wasm` artifact.
2. A host supplies the artifact’s imports, such as a logging function or access to a file.
3. A runtime validates the artifact, instantiates its state, and executes exported functions.

A browser already includes a Wasm engine; JavaScript commonly supplies imports and calls exports. A standalone application instead embeds a runtime or invokes a command-line runtime such as Wasmtime. The core format does not assume a browser, a DOM, or JavaScript.

Runtimes may interpret instructions or compile them to native code before execution. These strategies have different startup costs, steady-state performance, and platform requirements. The `.wasm` source artifact remains distinct from a runtime’s native compiled cache.

## Memory and host access

Core Wasm defines functions, tables, globals, and linear memories. A linear memory is a growable array of bytes addressed by the guest. An out-of-bounds access traps rather than becoming an arbitrary read or write in the host’s address space. This check does not know the boundaries of every Rust allocation inside that memory: unsafe guest code can still corrupt other data within the guest’s memory.

The guest accesses external services through imports. For example, an imported logging function might read a message from guest memory and send it to the host’s logger. The host must validate the arguments and define which operations that import permits. Exposing an unrestricted file-reading import would give the guest that authority, regardless of the memory sandbox.

Memory isolation also does not impose a CPU or memory budget. A host running untrusted code needs execution and allocation limits, plus a way to handle traps and terminate work. Runtime vulnerabilities remain part of the threat model. Wasm isolation takes place within a process unless the host separately creates a process boundary.

## Core modules, components, and WASI

These names describe different layers:

| Layer | Responsibility |
|---|---|
| Core Wasm module | Instructions, linear memory, and typed low-level imports and exports |
| Wasm component | Rich interface types and composition around module implementations |
| WASI | Standard interfaces for capabilities such as files, clocks, random values, and HTTP |

A core module can export a function using integers, floats, or supported reference types. A component interface can instead describe a string, record, result, or resource handle. The [Component Model and WIT](../component-model-and-wit/) chapter explains how those values cross the boundary; it is the reference for interface mechanics in this book.

WASI is one possible set of imports. A pure computation library may need none, and a host can define application-specific imports without WASI. The [WASI chapter](../wasi/) explains the standard interfaces and how a host grants access to actual resources.

## What makes an artifact portable?

A host can run a `.wasm` artifact only if it supports the artifact’s required instructions, binary format, and imports. Matching the CPU architecture is not enough, and having some Wasm runtime is not enough either. A browser module importing JavaScript functions and a WASI command importing filesystem interfaces require different environments.

The same distinction applies to components: a runtime that loads core modules may not load components. A component using one version of a WIT interface needs compatible imports. A runtime’s native precompiled artifact can have additional architecture and configuration dependencies.

The [targets chapter](../wasm-targets-and-tooling/) turns these requirements into a concrete choice of Rust target and build workflow. For the tradeoffs against native FFI and UniFFI, see [From FFI to the Component Model](../../interop-and-ffi/from-ffi-to-component-model/).

## Rust as the guest language

Rust can produce Wasm without bundling a garbage collector. Ownership, borrowing, and most ordinary language rules stay the same; the target changes which system services and dependencies are available. `Vec` and `String` still allocate guest memory, and `Rc` or `Arc` still incur their respective reference-counting costs when used.

Libraries that mostly parse, transform, or compute over data can be easier to port than libraries closely tied to an OS. Check transitive dependencies too: a small API can still rely on a native library or an unsupported system call. Use an optimized build for deployment measurements, while retaining debug builds for development.

Swift can also target Wasm. Choosing Rust may make sense for its libraries, ownership model, or component tooling; Wasm portability alone does not require a language rewrite. The rest of this section uses Rust so the ownership and interface decisions build on the preceding chapters.

## Further reading

- [WebAssembly specification](https://webassembly.github.io/spec/): core execution and validation rules.
- [WebAssembly security model](https://webassembly.org/docs/security/): isolation and its limits.
- [Wasmtime documentation](https://docs.wasmtime.dev/): running and embedding a runtime.
- [Swift SDKs for WebAssembly](https://www.swift.org/documentation/articles/wasm-getting-started.html): Swift’s target workflow.
- [Wasm status appendix](../../appendices/wasm-status/): a dated reference for features and proposals, separate from the instructional sequence.
