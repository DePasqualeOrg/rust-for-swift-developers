---
title: The Evolving Wasm Landscape
sidebar:
  order: 36
---

WebAssembly is a moving target. The core specification continues to evolve, new proposals advance through the standardization process, and the tooling ecosystem around Rust and Wasm grows denser every year. This final chapter surveys the current state of the landscape – what has shipped, what is in progress, and where things are headed. Because this space moves quickly, treat this chapter as a starting point and verify details against current sources.

## WebAssembly 3.0

The WebAssembly 3.0 specification (sometimes called "Wasm 3.0") bundles proposals that have reached the core spec. In practice, support still lands feature-by-feature and engine-by-engine: browsers and standalone runtimes do not all ship every 3.0 feature at the same time.

### Exception handling

Wasm 3.0 adds native `try`/`catch`/`throw` instructions to the core bytecode. Before this, languages that use exceptions (C++, C#, Kotlin) had to emulate them with JavaScript interop in the browser or use costly stack-unwinding workarounds. Native exception handling means:

- Languages that depend on stack unwinding have a real exception mechanism in core Wasm
- Interop with C++ code compiled to Wasm is more practical
- Rust may benefit in configurations that use `panic = "unwind"`, though many Wasm workflows still prefer `panic = "abort"`

Rust itself does not use exceptions for error handling, so this feature is most relevant when linking with C++ libraries or when using `panic = "unwind"` instead of `panic = "abort"`.

### Garbage collection (GC)

The GC proposal adds managed reference types and struct/array heap types to Wasm. This allows languages with garbage collectors (Java, Kotlin, Dart, Go) to compile to Wasm without shipping their own GC runtime, reducing binary size and improving interop with the host's GC (particularly the browser's JavaScript GC).

For Rust developers, the GC proposal has limited direct impact – Rust manages memory through ownership and does not need a garbage collector. However, it matters for the broader Wasm ecosystem because it enables more languages to target Wasm efficiently, which means more components to compose with your Rust code.

### Memory64

Memory64 lifts the 4 GiB address-space limitation of Wasm's original 32-bit memory model by allowing 64-bit indexes for memories and tables. The practical limits still depend on the embedder and runtime, but it removes the original 32-bit ceiling that constrained large-data workloads.

To use Memory64 from Rust, the module must be compiled with a 64-bit memory target. Toolchain support is advancing but not yet the default.

### Tail calls

The tail call proposal adds `return_call` and `return_call_indirect` instructions that perform guaranteed tail-call optimization. This prevents stack overflow in recursive code by reusing the current call frame instead of pushing a new one.

Rust does not guarantee TCO at the language level (though LLVM sometimes optimizes tail calls). The Wasm tail-call instructions allow backends to emit guaranteed tail calls when the source language requires them, which benefits functional languages compiling to Wasm and enables certain patterns (state machines, interpreters) that rely on deep recursion.

### Relaxed SIMD and the broader SIMD story

Wasm 3.0 adds relaxed vector instructions on top of the earlier 128-bit SIMD work that was standardized before 3.0. For Rust developers, the important point is that Wasm SIMD support keeps getting richer: code using `std::simd` or architecture-specific intrinsics can compile to Wasm SIMD instructions where the runtime supports them, improving performance for:

- Image and audio processing
- Cryptographic operations
- Mathematical computations
- String searching and parsing

Rust's `wasm32` targets support SIMD through the `#[target_feature(enable = "simd128")]` attribute and the `std::arch::wasm32` intrinsics module. The newer relaxed-SIMD instructions matter mostly to engine implementers and compilers, but they are part of the broader trend toward better data-parallel performance in Wasm.

## In-progress proposals

Several proposals are actively being developed and have not yet reached full standardization. These represent the next wave of Wasm capabilities.

### Threads and shared-everything threads

Wasm has had basic thread support (shared memory and atomics) for a while, enabling `SharedArrayBuffer`-style parallelism in browsers. The **shared-everything threads** proposal goes further: it allows multiple threads to share not just linear memory but also Wasm tables, globals, and other state.

For Rust developers, this means that multi-threaded Rust programs using `std::thread`, `Arc`, `Mutex`, and channels could eventually compile to Wasm with richer shared-state semantics. Today, mainstream Wasm workflows are still mostly single-threaded, though Rust does have a `wasm32-wasip1-threads` target for runtimes that support the legacy `wasi-threads` path. Rust's own target documentation still describes that target as being in flux.

Current status: the proposal is still very early. It is not something stable Rust Wasm targets expose today, so treat it as a direction of travel rather than a production feature.

### Stack switching

The stack switching proposal adds the ability to suspend and resume execution stacks. This is the foundation for:

- **Green threads**: lightweight threads managed by the runtime rather than the OS
- **Native async**: suspending a Wasm function while waiting for I/O without blocking the host thread
- **Coroutines and generators**: yield-style control flow

Stack switching is particularly important for WASI 0.3's async model. Without it, async operations require complex callback-based lifting and lowering between the component and the host. With stack switching, a component can simply suspend when it hits an `await` point, and the host resumes it when the result is ready.

For Rust, this could eventually mean that `async fn` in Wasm components works as naturally as it does in native Rust – the component suspends at `.await` points and the host drives the event loop.

Current status: the proposal is in phase 2 (proposed spec text available). It is promising, but it is still not something most production Wasm deployments can assume.

### JavaScript Promise Integration (JSPI)

JSPI is a browser-specific extension that bridges synchronous Wasm calls with JavaScript's asynchronous `Promise` model. When a Wasm function calls an imported JavaScript function that returns a `Promise`, JSPI automatically suspends the Wasm execution and resumes it when the promise resolves.

This is relevant for Rust code running in the browser that needs to call asynchronous browser APIs (fetch, IndexedDB, Web Crypto) without restructuring the Rust code into a callback-based architecture. With JSPI, synchronous Rust code can call async JavaScript transparently.

Current status: JS Promise Integration is a phase-4 proposal with experimental browser implementations, but support is still browser-specific and not something you should assume is universally available.

## Rust's evolving Wasm targets

Rust maintains several Wasm compilation targets, each corresponding to a different level of the Wasm platform:

- **`wasm32-unknown-unknown`**: bare Wasm with no system interface. Used for browser targets and custom host environments. Stable.
- **`wasm32-wasip1`** (formerly `wasm32-wasi`): targets WASI 0.1 (preview1). Stable but being superseded.
- **`wasm32-wasip1-threads`**: a preview1-oriented threading target for runtimes that implement `wasi-threads`. Usable, but still documented as experimental/in flux.
- **`wasm32-wasip2`**: targets WASI 0.2, producing Wasm components. It exists on stable Rust today, though the platform-support docs still describe it as a new/experimental target and note that the Rust project does not test it in CI.
- **`wasm32-wasip3`**: the early Tier 3 target for the next stage of WASI async support. It exists upstream, but the official platform-support page still describes it as extremely early, notes that WASIp3 itself is not yet approved, and says extra patching is currently required before it builds.

The progression from `wasip1` to `wasip2` to `wasip3` mirrors the evolution of WASI itself. The `wasip1-threads` target is more of a side branch for legacy preview1 runtimes than part of that main line.

### `wasm32-wasip3` and native async

The `wasm32-wasip3` target is aimed at the next stage of WASI async support, including `stream<T>` and `future<T>` concepts in WIT interfaces. In practice, this is still a design target rather than a workflow you should budget a project around today, but the long-term goal is that a Rust component could export an async function like:

```wit
// A WASI 0.3 interface with async
interface processor {
    // Returns a stream of processed chunks
    process: func(input: list<u8>) -> stream<list<u8>>;
}
```

The Rust implementation would use `async` and yield values into the stream. The host runtime would drive the async execution, suspending and resuming the component as needed. This aligns with WASI 0.3's goal of first-class async support in the Component Model.

## The growing component ecosystem

Beyond the core specifications, the ecosystem around Wasm components is expanding in several directions.

### WIT interface registries

The `warg` (WebAssembly Registry) protocol and tools like `wa.dev` are building infrastructure for discovering, publishing, and depending on WIT interfaces and pre-built components. This is analogous to crates.io for Rust or Swift Package Registry for Swift – a centralized place to find reusable component interfaces.

As more standard interfaces are published (beyond the core WASI ones), it becomes practical to compose components from different authors and languages. A Rust image-processing component could be composed with a Python ML inference component and a Go HTTP handler, all communicating through typed WIT interfaces.

### Composition tooling

The `wac` (WebAssembly Composition) tool, together with lower-level utilities from `wasm-tools`, lets you link multiple components together into a single composed component at build time. This is like static linking, but at the component level – you resolve imports and exports between components before deployment.

For example, you could compose a logger component with your application component so that its logging imports are satisfied internally, without the host needing to provide them:

```sh
# Compose two components together
wac plug app.wasm --plug logger.wasm -o composed.wasm
```

### Language support

The number of languages that can produce Wasm components is growing:

- **Rust**: first-class support via `cargo-component` and the `wasm32-wasip2` target
- **Go**: Component Model support via TinyGo (the standard Go toolchain only produces core modules requiring JS)
- **Python**: via `componentize-py`, which bundles a Python interpreter into a component
- **JavaScript**: via `componentize-js`, using the StarlingMonkey JS engine
- **C/C++**: via `wasi-sdk` and LLVM's Wasm backend

This means your Rust components can interoperate with libraries and plugins written in any of these languages, as long as they share WIT interfaces.

## Where is the ecosystem headed?

Several trends are shaping the future of Wasm, particularly for Rust developers:

**Wasm as a universal plugin format.** If current tooling continues to mature, the Component Model makes it feasible to load and run code from many languages behind a sandboxed, typed interface. Applications that currently embed Lua, JavaScript, or Python for extensibility may adopt Wasm components instead, gaining stronger sandboxing and better language flexibility.

**Server-side Wasm.** Projects like Spin (Fermyon), wasmCloud, and Cloudflare's edge platform have used Wasm as part of their server-side or edge execution model. Rust's efficient Wasm output and lack of a garbage collector make it particularly well-suited for these environments, where startup time and memory footprint matter.

**Embedded and edge computing.** Wasm's small footprint and deterministic execution make it attractive for IoT devices, edge nodes, and embedded systems. WASI provides a standard system interface that abstracts over the underlying hardware, and Wasm's sandboxing provides isolation without a full operating system.

**Convergence with native toolchains.** As Wasm components gain richer type systems and async support, the gap between "compile to native" and "compile to Wasm" narrows. For Rust libraries that do not need direct hardware access, compiling to a Wasm component may become the default distribution format – a single artifact that runs everywhere a Wasm runtime exists.

## Key differences and gotchas

- **Stable vs in-progress**: features associated with WebAssembly 3.0 are standardized, but real support still varies by feature, browser, and runtime. Proposals like shared-everything threads and stack switching are not yet ready to assume in production.
- **Browser vs standalone**: not all features land simultaneously in browsers and standalone runtimes. JSPI is browser-only. Component Model support is more advanced in standalone runtimes (Wasmtime) than in browsers.
- **Component Model status is uneven**: the ecosystem is practical enough to use in parts of the Bytecode Alliance stack, but the proposal itself is still Phase 1 in the WebAssembly process. Treat today's tooling as fast-moving, not fully frozen.
- **Target names change**: Rust's Wasm target names have evolved (`wasm32-wasi` to `wasm32-wasip1` to `wasm32-wasip2`). Old tutorials may reference deprecated target names.
- **Async is not here yet**: WASI 0.3 and `wasm32-wasip3` are under active development. For now, interface-level async for Wasm components is still experimental, so design current production systems around synchronous component boundaries.
- **Tooling maturity varies**: `cargo-component`, `wasm-tools`, and `wac` are usable but still evolving. Expect breaking changes between versions.
- **Verify current status**: the information in this chapter reflects the state of the ecosystem as of April 2026. Proposals advance, runtimes ship updates, and tooling improves continuously. Check the [WebAssembly proposals repository](https://github.com/WebAssembly/proposals) and the [WASI project](https://github.com/WebAssembly/WASI) for the latest status.

## Further reading

- [WebAssembly proposals](https://github.com/WebAssembly/proposals): all active and completed proposals
- [WebAssembly specification](https://webassembly.github.io/spec/): the formal specification
- [WASI roadmap](https://github.com/WebAssembly/WASI/blob/main/Proposals.md): WASI proposals and their phases
- [Bytecode Alliance blog](https://bytecodealliance.org/articles): news on Wasmtime, WASI, and the Component Model
- [Fermyon Spin](https://developer.fermyon.com/spin): server-side Wasm framework with strong Rust support
- [Component Model documentation](https://component-model.bytecodealliance.org/): the canonical reference for Wasm components
- [cargo-component](https://github.com/bytecodealliance/cargo-component): Cargo plugin for building Wasm components from Rust
- [wa.dev](https://wa.dev/): WebAssembly component registry
