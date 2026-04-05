---
title: Wasm on Apple Platforms
sidebar:
  order: 35
---

This chapter considers running Rust-generated Wasm inside Swift applications. An embedded runtime can provide isolation for plugins and portable computation, but its feature support, packaging, and platform restrictions need to be evaluated alongside native FFI.

## Choosing an embedding strategy

Use the [interop comparison](../../interop-and-ffi/from-ffi-to-component-model/) to decide whether runtime isolation and portable guest artifacts justify embedding Wasm. On Apple platforms, the next questions are concrete: can the runtime load your binary format, can it execute under the target’s memory and signing rules, and how will you package it with the app?

A runtime supporting core modules is not necessarily a component host. Choose the required interfaces before selecting the runtime, and distinguish macOS support from iOS support.

## Available Wasm runtimes

Several Wasm runtimes can be embedded into Apple platform apps:

- **Wasmtime**: the reference runtime from the Bytecode Alliance. Written in Rust, it provides both a Rust API and a C API (`wasmtime-c-api`). Component Model and WASI 0.2 support are strongest here, especially in the Rust embedding story.
- **Wasmer**: another mature runtime with a C API and support for multiple compilation backends. If you are evaluating it for Apple apps, check the current state of Component Model support and packaging carefully; the main Wasmer project does not currently publish an official Swift package.
- **WasmKit**: a pure Swift Wasm runtime developed by the SwiftWasm project. The current Swift.org Wasm SDK workflow uses WasmKit in recent compatible toolchains and snapshots on macOS and Linux. As an embeddable runtime, it integrates naturally with Swift Package Manager and is lighter-weight than the bigger optimizing runtimes, but its README still lists WASI 0.1 as the implemented host-API surface, and full Component Model support is still in progress.
- **Wasm3**: a fast interpreter written in C. Small footprint, easy to embed, but interpreter-only (no AOT compilation) and limited to the core Wasm specification.

For projects that need Component Model and WASI 0.2 support today, Wasmtime is the most capable default, especially if you are willing to package its C or Rust artifacts yourself. For simpler use cases or smaller binary footprints, WasmKit and Wasm3 are worth considering.

## Using Wasmtime from Swift

Wasmtime's C API can be called from Swift through a C bridging header or a Swift package that wraps the C library. The general approach:

1. Build or obtain the Wasmtime C library (`libwasmtime`) for your target platform
2. Create a Swift package or bridging header that imports the C API
3. Use the API to load, instantiate, and call Wasm modules

Here is a sketch of what loading and running a core Wasm module looks like using the C API from Swift. This is simplified – a production integration would need more robust error handling and memory management:

```swift
import Foundation
import CWasmtime // Bridging header or Swift package wrapping the C API

enum WasmRunError: Error {
    case allocationFailed
    case compilationFailed
}

// Demonstrates loading a core Wasm module (not a component).
// The Component Model API is more involved; this is a starting point.
func runWasmModule(at path: String) throws {
    // Create an engine with default configuration
    guard let engine = wasm_engine_new() else {
        throw WasmRunError.allocationFailed
    }
    defer { wasm_engine_delete(engine) }

    // Create a store (holds runtime state)
    guard let store = wasmtime_store_new(engine, nil, nil) else {
        throw WasmRunError.allocationFailed
    }
    defer { wasmtime_store_delete(store) }
    _ = wasmtime_store_context(store)

    // Load the Wasm binary
    let wasmBytes = try Data(contentsOf: URL(fileURLWithPath: path))
    var module: OpaquePointer?
    let compilationError = wasmBytes.withUnsafeBytes { buffer in
        wasmtime_module_new(
            engine,
            buffer.baseAddress?.assumingMemoryBound(to: UInt8.self),
            buffer.count,
            &module
        )
    }
    if let compilationError {
        wasmtime_error_delete(compilationError)
        throw WasmRunError.compilationFailed
    }
    guard let compiledModule = module else {
        throw WasmRunError.compilationFailed
    }
    defer { wasmtime_module_delete(compiledModule) }

    // Instantiate and call exported functions here.
    // The exact calling sequence depends on the module's exports.
}
```

### Community wrappers

Rather than using the C API directly, you can either depend on WasmKit directly as a Swift package or look for community-maintained wrappers around runtimes like Wasmtime. These projects vary widely in maturity, so verify their current maintenance status before adopting them in production.

## iOS-specific considerations

### JIT restrictions

Third-party iOS apps cannot rely on a traditional just-in-time (JIT) compilation pipeline. The operating system enforces W^X (write XOR execute) memory protection, which makes the usual JIT model difficult or unavailable for App Store apps. This is a fundamental constraint for Wasm runtimes, which often want to JIT-compile Wasm bytecode to native machine code at load time.

Ahead-of-time compilation avoids compilation at load time, but does not by itself solve iOS executable-memory and code-signing restrictions. On platforms that permit loading native compiled artifacts, Wasmtime can precompile a module:

```sh
# Precompile a Wasm module to a compiled artifact
wasmtime compile my_module.wasm -o my_module.cwasm
```

A native `.cwasm` artifact contains machine code that Wasmtime must map as executable memory. Bundling it as a resource does not make it signed executable code acceptable to iOS. The artifact also depends on the target architecture and compatible runtime configuration; only deserialize artifacts from a trusted source.

The source `.wasm` file stays portable, but each AOT-compiled `.cwasm` artifact is target-specific. On iOS, that means AOT can reintroduce some of the per-architecture packaging work that raw Wasm normally avoids.

Interpreters such as WasmKit and Wasm3 execute bytecode without generating native code at runtime. Wasmtime also offers the [Pulley interpreter](https://docs.wasmtime.dev/examples-pulley.html). Verify the chosen runtime’s build support for your Apple target; interpretation avoids native JIT allocation but is not an App Review approval guarantee.

### Binary size

Embedding a Wasm runtime adds to your app's binary size. The impact varies:

- **Wasmtime**: on the order of megabytes; it is a full optimizing runtime
- **Wasmer**: also on the order of megabytes, depending on the compilation backend
- **WasmKit**: lighter, as it is a Swift-native interpreter
- **Wasm3**: very small, as it is a pure interpreter

For apps where binary size is critical, an interpreter-based runtime may be preferable despite the performance tradeoff.

### App Store review

Apple's App Store Review Guidelines section 2.5.2 explicitly says apps may not download, install, or execute code that changes the app's features or functionality. For Wasm on iOS, the conservative guidance is:

- Bundle all Wasm modules with the app at submission time (no runtime downloading of new components)
- Use a runtime and packaging strategy compatible with the platform’s executable-memory and signing rules.
- Avoid architectures that depend on fetching new executable Wasm after review unless you have a very clear policy justification

Section 2.5.2 has limited exceptions, and section 4.7 permits certain categories of software offered within apps under additional conditions. Neither is a blanket permission to download arbitrary Wasm. Check the [current guidelines](https://developer.apple.com/app-store/review/guidelines/) for your app’s distribution model.

## Use cases

### Plugin systems

Wasm's sandboxing makes it well-suited for plugin architectures. A document editor, creative tool, or automation app could let users install third-party plugins compiled to Wasm, with guarantees that plugins cannot access the filesystem, network, or other plugins' state unless explicitly permitted.

The Component Model makes this particularly practical: you define a WIT interface that plugins must implement, and any language that compiles to Wasm components (Rust, C, Go, Python, JavaScript) can provide plugins.

```wit
// A plugin interface for a text processing app
package myapp:plugins;

interface text-plugin {
    record context {
        selection: string,
        document-title: string,
    }

    transform: func(input: context) -> string;
    name: func() -> string;
}

world plugin {
    export text-plugin;
}
```

Plugins implementing this interface would be loaded by the Swift host app, which calls `transform` with the current selection and displays the result.

### Sandboxed execution

For user-provided formulas, scripts, or rules, Wasm provides an isolation boundary within the host process. Guest code cannot directly access arbitrary host memory or system calls. Configure memory limits and execution budgets as well as import permissions: a memory sandbox alone does not prevent resource exhaustion, and runtime bugs can still compromise isolation.

## Practical example: loading a Wasm module with WasmKit

WasmKit provides a Swift-native API that integrates with Swift Package Manager. The exact API evolves quickly, so treat the following as illustrative pseudocode showing the typical flow:

```swift
import WasmKit

func runModule() async throws {
    // Parse the Wasm binary
    let module = try parseWasm(filePath: "transform.wasm")

    // Create a runtime
    let runtime = Runtime()

    // Instantiate the module
    let instance = try runtime.instantiate(module: module)

    // Call an exported function
    let result = try runtime.invoke(instance, function: "add", with: [.i32(2), .i32(3)])
    print("Result: \(result)")  // [.i32(5)]
}
```

For modules that use WASI APIs (filesystem, clocks, etc.), WasmKit includes WASI support you attach to the runtime before instantiation, but the exact surface area and API shape depend on the library version.

## Key differences and gotchas

- **JIT restrictions on iOS**: an interpreter is the straightforward option for ordinary apps. Native AOT artifacts still face executable-memory and code-signing requirements.
- **Binary size**: Wasm runtimes are not small. Factor the runtime size into your app size budget, especially for iOS apps.
- **Component Model support varies**: not all runtimes support the full Component Model. If you are building Wasm components (not just core modules), verify that your chosen runtime can load them.
- **Performance overhead**: Wasm execution is workload-dependent and is usually materially slower than native FFI in the hot path, especially when you cross the host boundary frequently.
- **Ecosystem maturity**: Swift-to-Wasm runtime bindings are still early. Expect rough edges, breaking API changes, and limited documentation compared to the native FFI path.
- **App Store guidelines**: evaluate sections 2.5.2 and 4.7 for the software your app runs. Technical sandboxing alone does not establish policy compliance.
- **Debugging**: verify source-level debugging and profiling support in the runtime you embed. A tool that works in a standalone runtime may not work inside your Swift application.

## Further reading

- [Wasmtime C API documentation](https://docs.wasmtime.dev/c-api/): reference for embedding Wasmtime
- [WasmKit repository](https://github.com/swiftwasm/WasmKit): pure Swift Wasm runtime
- [Wasmer documentation](https://docs.wasmer.io/): runtime documentation and embedding guides
- [Wasm3 repository](https://github.com/wasm3/wasm3): lightweight C interpreter
- [SwiftWasm project](https://swiftwasm.org/): Swift-to-Wasm toolchain and ecosystem
- [Apple App Store Review Guidelines](https://developer.apple.com/app-store/review/guidelines/): section 2.5.2 on code execution
