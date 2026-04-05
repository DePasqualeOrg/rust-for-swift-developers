---
title: "Appendix D: WebAssembly Status (September 2026)"
sidebar:
  order: 103
---

**Checked on 27 September 2026.** This appendix is a snapshot, not a prerequisite for the Wasm chapters. Specifications, Rust targets, binding generators, and runtimes have separate release schedules. A proposal’s status does not prove that a particular deployment supports it.

For build commands and target selection, use [Wasm Targets and Tooling](../../rust-and-webassembly/wasm-targets-and-tooling/). For interface semantics, use [The Component Model and WIT](../../rust-and-webassembly/component-model-and-wit/) and [WASI](../../rust-and-webassembly/wasi/).

## Core WebAssembly features

WebAssembly 3.0 incorporates several features whose availability must still be checked in the chosen engine. The [core specification](https://webassembly.github.io/spec/) and [finished-proposals list](https://github.com/WebAssembly/proposals/blob/main/finished-proposals.md) describe the standardized set.

| Feature | What it adds | What it means for Rust |
|---|---|---|
| Exception handling | Exception tags and instructions such as `try_table` and `throw` | Relevant to supported panic-unwinding configurations and interoperability with exception-using languages. |
| Garbage collection | Managed references and struct/array heap types | Enables language implementations that target the engine’s collector; ordinary Rust ownership does not require one. |
| Memory64 | 64-bit addressing for memories and tables | Requires an appropriate compilation target and engine support; it does not enlarge a `wasm32` program’s pointers. |
| Tail calls | Explicit tail-call instructions | Helps backends implement tail calls; Rust still does not promise tail-call optimization for ordinary recursion. |
| Relaxed SIMD | Additional vector operations with specified latitude in results | Useful to compatible code generators and intrinsics; check instruction support and numerical requirements. |

Stable Rust exposes Wasm-specific intrinsics through `std::arch::wasm32`. Portable [`std::simd`](https://doc.rust-lang.org/std/simd/) remains a nightly API at this review date.

## Proposal status

The [WebAssembly proposal tracker](https://github.com/WebAssembly/proposals) lists the following phases at the review date. Phase numbers describe standardization progress, not a ranking of production readiness.

| Proposal | Phase | Deployment implication |
|---|---|---|
| JavaScript Promise Integration (JSPI) | 5: standardized | Bridges Wasm suspension and JavaScript promises; browser support must be checked separately. |
| Threads | 4: standardize the feature | Shared linear memory and atomics need compatible runtime and embedding support. |
| Stack switching | 3: implementation | Adds explicit stack suspension/resumption; do not assume every engine implements it. |
| Component Model | 1: feature proposal | Implementations can be useful before the proposal completes; verify the particular runtime and binding versions. |
| Shared-everything threads | 1: feature proposal | Extends sharing beyond linear memory; it is distinct from the existing threads proposal. |

Stack switching and component async are related implementation topics, but WASI async support does not require the core stack-switching proposal to finish standardization first.

## WASI and Rust target support

The [WASI project](https://github.com/WebAssembly/WASI) identifies WASI 0.3/preview3 as its current preview. It adds native component async interfaces using `future` and `stream`. WASI 0.2 represents asynchronous I/O through resource-based streams and polling instead. The examples in this book’s WASI chapter use 0.2 deliberately.

| Rust target | Interface generation | Status to account for |
|---|---|---|
| `wasm32-wasip1` | WASI preview1 core imports | For hosts and dependencies using the older interface. |
| `wasm32-wasip2` | WASI 0.2 components | Available as a Tier 2 target on stable Rust. |
| `wasm32-wasip3` | WASI 0.3 components | Listed as Tier 3; verify build requirements, bindings, and runtime support together. |
| `wasm32-wasip1-threads` | Preview1 plus `wasi-threads` | A separate threading workflow, not an alias for component async. |

Consult the Rust platform-support pages for [wasip2](https://doc.rust-lang.org/rustc/platform-support/wasm32-wasip2.html), [wasip3](https://doc.rust-lang.org/rustc/platform-support/wasm32-wasip3.html), and [preview1 threads](https://doc.rust-lang.org/rustc/platform-support/wasm32-wasip1-threads.html). A dated warning inside those pages may describe an earlier state; compare it with the toolchain release you actually use.

## Checking a deployment

For a concrete project, record the compiler version, target, interface versions, binding-generator version, and runtime version. Validate the compiled artifact and instantiate it in that exact host. Exercise its imports and failure paths, including cancellation if the interface is asynchronous.

Browser execution, server embedding, and Apple app distribution have different constraints. Success in one host does not establish support in another. Prefer a demonstrated workflow for a shipping requirement; treat a proposal or roadmap as a reason to investigate, not as an implemented dependency.
