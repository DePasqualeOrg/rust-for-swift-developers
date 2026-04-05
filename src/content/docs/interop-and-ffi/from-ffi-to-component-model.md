---
title: From FFI to the Component Model
sidebar:
  order: 30
---

C FFI, UniFFI, and WebAssembly components solve different integration problems. The choice depends on who controls the code, which hosts must run it, and what the boundary must express. This chapter compares those choices; the following chapters explain how Wasm execution and component interfaces work.

## What crosses the boundary?

Consider a Rust parser that accepts text and returns either a configuration or a parsing error. Within Rust, its signature can use `&str` and `Result<Config, ParseError>`. Across a language boundary, the implementation needs an agreed representation for those values and a rule for releasing their storage.

With **C FFI**, you design that agreement. Text might be a pointer and length, a configuration an opaque handle, and failure a status code plus an error message. C can represent tagged alternatives and optional values through structs and conventions, but a C header does not express Rust’s borrow lifetimes or Swift’s isolation rules. Both sides must uphold the documented contract. [C FFI Basics](../c-ffi-basics/) shows the pointer, layout, and ownership mechanics.

With **UniFFI**, a generator supplies much of the agreement and its binding code. Swift callers can receive a Swift value or a thrown error while the generated layer converts values and manages handles. The Rust library still runs as native code, with access to the host process’s memory. It needs a native build for each target, and bindings must match the library’s API. The [Apple integration chapter](../rust-on-apple-platforms/) covers packaging those builds.

With the **Component Model**, the interface describes values using WIT, and a defined ABI specifies their representation across the boundary. A Wasm runtime executes the implementation and mediates its access to the host. The source `.wasm` artifact can be portable across compatible hosts, but each host still needs runtime support and suitable bindings. The [WIT chapter](../../rust-and-webassembly/component-model-and-wit/) explains the interface types, resource handles, and conversions.

## Comparing the choices

| Question | C FFI | UniFFI | Component Model |
|---|---|---|---|
| How is the API described? | C declarations and documented conventions | Rust/UDL definitions plus generated language bindings | WIT and component type information |
| Who handles conversions? | Your wrappers | Generated code, with limits imposed by supported types | Generated bindings and runtime ABI support |
| What is distributed? | Native binaries for each target | Native binaries plus matching bindings | Wasm components for compatible hosts |
| What isolates library code? | No additional isolation inside the process | No additional isolation inside the process | The runtime’s guest-memory boundary and host-controlled imports |
| What must the application include? | The library and its native dependencies | The library, bindings, and their dependencies | A compatible runtime, unless the host already provides one |
| Where do call costs come from? | Calling convention, ownership transfer, conversion | Generated conversion and ownership code | Runtime execution and component-boundary conversion |

Native FFI can avoid a copy when caller and callee agree on borrowing. Generated bindings or isolated memories can require copies instead. Neither API style has a fixed overhead: payload size, call frequency, allocation, and the work inside the function determine the cost. Compare the actual call pattern before choosing an architecture for performance.

## Choosing for a Swift application

**Use C FFI for an existing C API or a small boundary you can specify precisely.** It also suits low-level integration that depends on a native memory layout or platform calling convention. Keep the unsafe details in a wrapper that enforces a safe contract for its callers.

**Use UniFFI to expose a Rust library through generated Swift APIs.** It reduces handwritten conversion code when its supported types fit your interface. Account for native cross-compilation and binding generation as part of the build, and define cancellation and error behavior for async calls. Consult the [language-support documentation](https://mozilla.github.io/uniffi-rs/next/) when adding consumers beyond Swift.

**Use components when isolation, portable artifacts, or component composition justify a runtime.** A plugin host might benefit from restricting each plugin’s capabilities. A library embedded in several products might benefit from one portable guest artifact. Verify the required interfaces and Wasm features on every intended host before treating that artifact as deployable there.

These choices can coexist. A Swift app can call a native Rust library through UniFFI, and that library can host third-party Wasm plugins. Native code implements platform services; explicit component imports expose only the operations available to plugins.

## What portability does not remove

A portable binary does not make an OS-specific dependency portable. A crate using process creation, a native C library, or architecture-specific instructions needs a supported backend or a different implementation for Wasm. Even a library using only Rust’s standard library can require host interfaces that a particular target does not provide.

Likewise, an embedded Wasm runtime does not remove platform packaging rules. A native precompiled artifact is target-specific, and an iOS app still faces executable-memory, signing, and distribution constraints. Those requirements are covered in [Wasm on Apple Platforms](../../rust-and-webassembly/wasm-on-apple-platforms/).

## Where to continue

Read [Introduction to WebAssembly](../../rust-and-webassembly/introduction-to-webassembly/) for the execution model, [Wasm Targets and Tooling](../../rust-and-webassembly/wasm-targets-and-tooling/) for build commands, and [The Component Model and WIT](../../rust-and-webassembly/component-model-and-wit/) for interface design. [WASI](../../rust-and-webassembly/wasi/) explains standard host capabilities. The separate [Wasm status appendix](../../appendices/wasm-status/) records a dated view of proposals and toolchain support.
