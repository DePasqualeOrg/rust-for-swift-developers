---
title: Setting Up Your Environment
sidebar:
  order: 1
---

Before writing any Rust, you need a toolchain and an editor. If you have been working in the Apple ecosystem, you are used to a single monolithic install – Xcode – that gives you the compiler, build system, package manager, debugger, and IDE in one bundle. Rust takes a more Unix-like approach: small, composable tools that you can mix and match.

## Installing Rust with rustup

The entry point for Rust development is [rustup](https://rustup.rs/), a toolchain manager that installs the Rust compiler (`rustc`), the package manager and build system (`cargo`), and the standard library. It also lets you switch between stable, beta, and nightly release channels, and manage cross-compilation targets.

On macOS or Linux, the standard install is a one-liner:

```sh
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
```

After installation, verify that everything is in place:

```sh
rustc --version
cargo --version
```

### How rustup compares to Xcode toolchain management

If you have ever used `xcode-select` to switch between Xcode versions, or installed a Swift toolchain snapshot from swift.org, you already understand the problem rustup solves. The difference is in granularity and flexibility:

| Concept | Swift / Xcode | Rust / rustup |
|---|---|---|
| Install the toolchain | Download Xcode from the App Store or developer portal | `curl ... \| sh` or `rustup install stable` |
| Switch versions | `xcode-select -s /path/to/Xcode.app` | `rustup default stable` or `rustup default nightly` |
| Per-project overrides | Use `.swift-version` or toolchain bundles | `rustup override set <version>` or commit a `rust-toolchain.toml` file |
| Add cross-compilation support | Xcode includes all Apple platform SDKs | `rustup target add aarch64-apple-ios` or `rustup target add wasm32-wasip1` |
| Update | Download a new Xcode | `rustup update` |

One thing that may feel different: Rust stable releases ship every six weeks, and updating is fast and non-disruptive. There is no multi-gigabyte download or reboot involved.

In practice, many Rust repositories check in a `rust-toolchain.toml` file so the required toolchain travels with the project. That is the closest analogue to pinning a Swift toolchain for a repository rather than just your local machine.

### Channels and editions

Rust has three release channels:

- **stable**: the default, recommended for all production work
- **beta**: the next stable release, useful for testing compatibility
- **nightly**: bleeding-edge features gated behind feature flags

You will use stable almost exclusively. The main exception is if you need an experimental feature or a specific Wasm-related tool that requires nightly – the guide will note this when it comes up.

Rust also has a concept of *editions* (2015, 2018, 2021, 2024) that allow the language to evolve without breaking existing code. Think of editions as similar to Swift language version modes (`-swift-version 5` vs. `-swift-version 6`). Your project's edition is declared in `Cargo.toml`, and crates compiled with different editions interoperate freely.

## Cargo: the build system and package manager

If you have used Swift Package Manager, Cargo will feel familiar – but more fully featured. Cargo handles building, testing, running, dependency resolution, documentation generation, and publishing packages to the [crates.io](https://crates.io/) registry.

Where SPM uses `Package.swift` to describe a package, Cargo uses `Cargo.toml`. Where SPM invokes `swift build` and `swift test`, Cargo uses `cargo build` and `cargo test`. The mental model is similar; the details are covered in the [next chapter](../cargo-and-project-structure/).

For now, the key commands to know:

| Task | Swift / SPM | Rust / Cargo |
|---|---|---|
| Create a new project | `swift package init` | `cargo new project_name` |
| Build | `swift build` | `cargo build` |
| Type-check without linking | No exact equivalent | `cargo check` |
| Run | `swift run` | `cargo run` |
| Test | `swift test` | `cargo test` |

## Creating and running your first program

Let's create a project and make sure everything works:

```sh
cargo new hello_rust
cd hello_rust
```

This generates the following structure:

```
hello_rust/
  Cargo.toml
  src/
    main.rs
```

`Cargo.toml` is the project manifest (like `Package.swift`), and `src/main.rs` is the entry point. Open `src/main.rs` and you will see:

```rust
fn main() {
    println!("Hello, world!");
}
```

The Swift equivalent:

```swift
// Swift
print("Hello, world!")
```

A few things to notice:

- **`fn` instead of `func`**: same concept, shorter keyword.
- **`println!` is a macro**, not a function – the `!` suffix indicates this. Macros are expanded at compile time. You can think of `println!` as similar to Swift's `print()` for now; macros are covered in detail in [Chapter 27](../../rust-ecosystem/macros/).
- **No `import` needed**: `println!` is a macro provided by the standard library, available in every Rust program without an explicit import.
- **Explicit `main` function required**: unlike ordinary Swift scripts or playgrounds, Rust binaries do not allow arbitrary top-level executable statements in crate source files. A binary crate uses a `fn main()`. In examples throughout this guide, we omit `fn main()` when it is not relevant to the concept being demonstrated.

Run the program:

```sh
cargo run
```

You should see:

```
   Compiling hello_rust v0.1.0 (/path/to/hello_rust)
    Finished `dev` profile [unoptimized + debuginfo] target(s)
     Running `target/debug/hello_rust`
Hello, world!
```

That first run compiles the code and then executes the resulting binary. Subsequent runs only recompile if the source has changed – Cargo tracks file modifications and dependencies automatically.

## IDE setup

Rust does not have an IDE as tightly integrated as Xcode is with Swift. Instead, most Rust developers use one of two options:

### VS Code with rust-analyzer

This is the most popular setup in the Rust community. Install [Visual Studio Code](https://code.visualstudio.com/) and add the [rust-analyzer](https://marketplace.visualstudio.com/items?itemName=rust-lang.rust-analyzer) extension.

rust-analyzer provides:

- Real-time type checking and error highlighting
- Inline type hints (helpful when Rust's type inference hides the types from you)
- Go-to-definition, find-references, and rename
- Code completion with type information
- Macro expansion preview
- Integrated terminal for running `cargo` commands

If you are comfortable in VS Code, this setup is excellent and free. The experience is comparable to using Xcode's editor with Swift – you get continuous feedback from the compiler as you type.

### RustRover

[RustRover](https://www.jetbrains.com/rust/) is JetBrains' dedicated Rust IDE. If you have used AppCode or any other JetBrains IDE, RustRover will feel immediately at home. It offers deeper refactoring support and a more integrated debugging experience than VS Code.

### Other options

Neovim and Helix both have strong rust-analyzer integration via LSP. Zed, a newer editor written in Rust, also works well. The key requirement is LSP support for rust-analyzer – any editor that provides it will give you a solid experience.

### A note on compiler feedback

One of Rust's strengths is the quality of its compiler diagnostics. When your code does not compile, `rustc` typically tells you *why* and often suggests a fix. This is similar to Swift's "Fix-it" suggestions in Xcode, but Rust's error messages tend to be longer and more detailed, especially around ownership and borrowing. Learning to read these messages carefully is one of the most valuable skills you will develop.

## Code quality tools

Swift developers often rely on [SwiftLint](https://github.com/realm/SwiftLint) and [SwiftFormat](https://github.com/nicklockwood/SwiftFormat) to enforce style and catch common issues. These are third-party tools that you install and configure separately. Rust ships equivalent tools as official, first-party components.

### rustfmt: automatic code formatting

`rustfmt` is Rust's official code formatter. With rustup's default profile it is installed as an official toolchain component; if you use the minimal profile, add it with `rustup component add rustfmt`. It enforces a consistent style across the ecosystem, and nearly all Rust projects use the default formatting rules. Run it with:

```sh
cargo fmt
```

This reformats all source files in your project. To check formatting without modifying files (useful in CI):

```sh
cargo fmt --check
```

The closest Swift equivalent would be running `swift-format` or SwiftFormat, but the cultural difference is significant: in Rust, there is essentially one style. Formatting debates are settled by the tool, and nearly every open-source Rust project expects contributors to run `cargo fmt`.

### clippy: the linter

`clippy` is Rust's official linter. It catches common mistakes, suggests more idiomatic code, and flags potential performance issues. Run it with:

```sh
cargo clippy
```

clippy has hundreds of lints organized by category (correctness, style, performance, complexity, and more). It is analogous to SwiftLint, but again, it is built-in and widely adopted as standard practice.

A typical development workflow looks like:

```sh
cargo check     # fast type-checking during iteration
cargo build     # compile
cargo test      # run tests
cargo clippy    # lint
cargo fmt       # format
```

Automatic formatting on save is common. Running `cargo clippy` on every save is possible, but it is heavier; many teams instead run it before commit or in CI.

## Key differences and gotchas

**No Xcode equivalent**: there is no single application that bundles everything. This can feel disorienting at first, but it also means each tool is lighter and more focused. You can use any editor, any terminal, and any operating system.

**Compilation can be slow – initially**: Rust's first compile of a project downloads and builds all dependencies, which can take a while. Incremental builds after that are typically fast. This is similar to the first time you resolve SPM dependencies in Xcode.

**The `target/` directory**: Cargo places all build artifacts in a `target/` directory at the project root. This is analogous to Xcode's DerivedData. You can safely delete it to reclaim disk space, and it is typically included in `.gitignore`.

**Binary location**: after `cargo build`, your debug binary is at `target/debug/<project_name>`. After `cargo build --release`, the optimized binary is at `target/release/<project_name>`.

**Cross-compilation is a first-class feature**: adding a new compilation target is as simple as `rustup target add <target-triple>`. This is particularly relevant for WebAssembly – you can add `wasm32-wasip2`, `wasm32-wasip1`, or `wasm32-unknown-unknown` and compile with `cargo build --target <target-triple>`. Cross-compilation with Swift is tightly coupled to Xcode and Apple's SDKs; in Rust, it is part of the standard workflow.

## Further reading

- [The rustup book](https://rust-lang.github.io/rustup/): official documentation for rustup
- [The Cargo book](https://doc.rust-lang.org/cargo/): comprehensive guide to Cargo
- [rust-analyzer user manual](https://rust-analyzer.github.io/manual.html): configuring rust-analyzer in your editor
- [Rust Compiler Error Index](https://doc.rust-lang.org/error_codes/error-index.html): explanations for every compiler error code
- [clippy lints list](https://rust-lang.github.io/rust-clippy/master/): browse all available clippy lints
