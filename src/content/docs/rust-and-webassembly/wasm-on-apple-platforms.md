---
title: Wasm on Apple Platforms
sidebar:
  order: 35
---

The previous chapters covered building Rust code into Wasm modules and components. This chapter explores the other side: running those Wasm binaries inside Swift applications on iOS, macOS, and other Apple platforms. This is a relatively new area, and the ecosystem is still maturing, but the combination of Wasm's sandboxing guarantees with Apple's platform capabilities opens up interesting possibilities for plugin systems, portable computation, and security-sensitive workloads.

## Why embed a Wasm runtime?

In [Chapter 29](../../interop-and-ffi/rust-on-apple-platforms/), we covered using FFI and UniFFI to call Rust code directly from Swift. That remains the default interop approach today for most first-party integrations. But embedding a Wasm runtime offers a different set of tradeoffs:

| Aspect | Native FFI / UniFFI | Embedded Wasm runtime |
|--------|--------------------|-----------------------|
| **Performance** | Near-native (direct function calls) | Slower (interpretation or AOT overhead) |
| **Binary size** | Only your library code | Library code + runtime (often multi-megabyte) |
| **Sandboxing** | Shares process memory | Runtime-enforced sandbox with isolated guest memory |
| **Portability** | Must compile per architecture | Same `.wasm` binary runs anywhere |
| **Plugin safety** | Plugins can crash the host | Plugins are far more constrained by the runtime sandbox |
| **Build complexity** | Cross-compilation per target | Single Wasm build, runtime handles the rest |

Native FFI is the right choice when you control all the code and want maximum performance. Embedded Wasm makes sense when you need to run untrusted or third-party code safely, or when you want a single compiled artifact that works across platforms.

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

// Demonstrates loading a core Wasm module (not a component).
// The Component Model API is more involved; this is a starting point.
func runWasmModule(at path: String) throws {
    // Create an engine with default configuration
    let engine = wasm_engine_new()
    defer { wasm_engine_delete(engine) }

    // Create a store (holds runtime state)
    let store = wasmtime_store_new(engine, nil, nil)
    defer { wasmtime_store_delete(store) }
    _ = wasmtime_store_context(store)

    // Load the Wasm binary
    let wasmBytes = try Data(contentsOf: URL(fileURLWithPath: path))
    var module: OpaquePointer?
    wasmBytes.withUnsafeBytes { buffer in
        wasmtime_module_new(
            engine,
            buffer.baseAddress?.assumingMemoryBound(to: UInt8.self),
            buffer.count,
            &module
        )
    }
    defer { wasmtime_module_delete(module) }

    // Instantiate and call exported functions here.
    // The exact calling sequence depends on the module's exports.
}
```

### Community wrappers

Rather than using the C API directly, you can either depend on WasmKit directly as a Swift package or look for community-maintained wrappers around runtimes like Wasmtime. These projects vary widely in maturity, so verify their current maintenance status before adopting them in production.

## iOS-specific considerations

### JIT restrictions

Third-party iOS apps cannot rely on a traditional just-in-time (JIT) compilation pipeline. The operating system enforces W^X (write XOR execute) memory protection, which makes the usual JIT model difficult or unavailable for App Store apps. This is a fundamental constraint for Wasm runtimes, which often want to JIT-compile Wasm bytecode to native machine code at load time.

The workaround is **ahead-of-time (AOT) compilation**: compile the Wasm binary to native code ahead of time, then bundle the precompiled artifact with the app. Wasmtime supports this through its `wasmtime compile` command:

```sh
# Precompile a Wasm module to a compiled artifact
wasmtime compile my_module.wasm -o my_module.cwasm
```

The resulting `.cwasm` file contains precompiled machine code that the runtime can load and execute without JIT. In practice you still need to make sure the compiled artifact matches the exact target architecture and runtime configuration you plan to ship.

The source `.wasm` file stays portable, but each AOT-compiled `.cwasm` artifact is target-specific. On iOS, that means AOT can reintroduce some of the per-architecture packaging work that raw Wasm normally avoids.

Alternatively, some runtimes (WasmKit, Wasm3) operate as interpreters and do not require JIT at all. Interpretation is slower but avoids the JIT restriction entirely.

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
- Prefer AOT-compiled modules or interpreter-based runtimes over runtime code generation
- Avoid architectures that depend on fetching new executable Wasm after review unless you have a very clear policy justification

This is a policy-sensitive area. Read the exact guideline text for your distribution model and avoid assuming that a technically sandboxed Wasm design will automatically satisfy App Review.

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

For apps that need to run user-provided or third-party logic – formula evaluators, scripting engines, rule engines – Wasm provides stronger isolation than running code in-process. A Wasm guest does not get direct access to host memory or arbitrary syscalls, and guest failures typically surface as traps or runtime errors that the host can handle. Runtime bugs are still possible, so think of this as strong isolation rather than an absolute guarantee.

### Portable computation libraries

If you maintain a library that needs to run on iOS, Android, the web, and server-side, compiling it to a Wasm component means you build once and embed the same binary everywhere. Each platform uses its own Wasm runtime, but the library code is identical. This avoids maintaining separate FFI bindings for each platform.

## Comparing approaches: native FFI vs embedded Wasm

For a concrete comparison, consider a Markdown-to-HTML conversion library written in Rust:

**Native FFI approach (Chapter 29):**
- Compile the Rust library for each Apple target (`aarch64-apple-ios`, `aarch64-apple-darwin`, etc.)
- Generate a C header or use UniFFI to create Swift bindings
- Link the static library into the Xcode project
- Result: fast, small, but requires cross-compilation per target

**Embedded Wasm approach:**
- Compile the Rust library to a Wasm module or component once
- Bundle the `.wasm` file (or a runtime-specific precompiled artifact such as `.cwasm`) with the app
- Load it through the embedded runtime and call the exported function
- Result: portable, sandboxed, but adds runtime overhead and binary size

For most first-party libraries, native FFI is simpler and faster. Wasm embedding becomes compelling when you need the sandboxing guarantees or when the same binary must run across very different host environments.

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

- **JIT restrictions on iOS**: you must use AOT compilation or an interpreter-only runtime. This is the single biggest practical constraint on Apple platforms.
- **Binary size**: Wasm runtimes are not small. Factor the runtime size into your app size budget, especially for iOS apps.
- **Component Model support varies**: not all runtimes support the full Component Model. If you are building Wasm components (not just core modules), verify that your chosen runtime can load them.
- **Performance overhead**: Wasm execution is workload-dependent and is usually materially slower than native FFI in the hot path, especially when you cross the host boundary frequently.
- **Ecosystem maturity**: Swift-to-Wasm runtime bindings are still early. Expect rough edges, breaking API changes, and limited documentation compared to the native FFI path.
- **App Store guidelines**: section 2.5.2 is strict about downloading or executing code that changes app functionality. Be conservative – bundle modules at build time and prefer AOT compilation or interpretation over post-review code delivery.
- **Debugging**: debugging Wasm code running inside a Swift app is harder than debugging native code. Source maps and DWARF support for Wasm are improving but not yet seamless.

## Further reading

- [Wasmtime C API documentation](https://docs.wasmtime.dev/c-api/): reference for embedding Wasmtime
- [WasmKit repository](https://github.com/swiftwasm/WasmKit): pure Swift Wasm runtime
- [Wasmer documentation](https://docs.wasmer.io/): runtime documentation and embedding guides
- [Wasm3 repository](https://github.com/wasm3/wasm3): lightweight C interpreter
- [SwiftWasm project](https://swiftwasm.org/): Swift-to-Wasm toolchain and ecosystem
- [Apple App Store Review Guidelines](https://developer.apple.com/app-store/review/guidelines/): section 2.5.2 on code execution
