---
title: Cargo and Project Structure
sidebar:
  order: 2
---

Cargo is Rust's build system, package manager, and project orchestrator. If you have used Swift Package Manager, the concepts will be familiar – but Cargo is more opinionated about project layout, more integrated into the development workflow, and more central to the ecosystem than SPM is to Swift's.

## Cargo.toml vs Package.swift

Every Rust project has a `Cargo.toml` file at its root. This is the project manifest – it declares the package name, version, edition, dependencies, and build configuration. It serves the same role as `Package.swift` in SPM, but it uses the TOML format instead of Swift code.

Here is a side-by-side comparison:

```toml
# Rust: Cargo.toml
[package]
name = "my_app"
version = "0.1.0"
edition = "2024"

[dependencies]
serde = { version = "1.0", features = ["derive"] }
tokio = { version = "1", features = ["full"] }
```

```swift
// Swift – Package.swift
// swift-tools-version: 6.0
import PackageDescription

let package = Package(
    name: "MyApp",
    dependencies: [
        .package(url: "https://github.com/apple/swift-argument-parser", from: "1.0.0"),
    ],
    targets: [
        .executableTarget(
            name: "MyApp",
            dependencies: [.product(name: "ArgumentParser", package: "swift-argument-parser")]),
    ]
)
```

Several differences stand out:

- **Declarative format**: `Cargo.toml` is static TOML data, not executable code. You cannot run arbitrary logic in your manifest. SPM's `Package.swift` is real Swift, which allows conditional logic but also makes it harder to parse externally.
- **No target declarations for simple projects**: Cargo infers targets from the filesystem. If you have `src/main.rs`, it is a binary. If you have `src/lib.rs`, it is a library. You only need explicit target configuration for non-standard layouts.
- **Registry-first dependencies**: Cargo resolves dependencies from [crates.io](https://crates.io/) by default. You specify a crate name and a version requirement – no URLs needed. SPM requires a full Git URL for each dependency.
- **Features**: Rust crates can define feature flags that enable optional functionality. This is more granular than anything SPM offers natively. In the example above, `serde` is included with its `derive` feature enabled, which adds support for derive macros.

### Cargo.lock

When you build for the first time, Cargo generates a `Cargo.lock` file that pins the exact versions of every dependency in the tree. This is analogous to `Package.resolved` in SPM.

Current Cargo guidance is simpler than a lot of older blog posts suggest: when in doubt, check `Cargo.lock` into version control, including for libraries. Keeping it gives you reproducible local builds and CI runs. Library authors who want to verify compatibility with newly resolved dependency versions usually do that with an extra CI job such as `cargo update` rather than by omitting the lockfile entirely.

## Project layout

Cargo uses a conventional directory structure. If you follow the conventions, no extra configuration is needed:

```
my_project/
  Cargo.toml
  Cargo.lock
  src/
    main.rs          # binary entry point (optional)
    lib.rs           # library root (optional)
    utils.rs         # additional module
    utils/
      helpers.rs     # submodule
  tests/
    integration.rs   # integration tests
  benches/
    benchmark.rs     # benchmarks
  examples/
    demo.rs          # example programs
```

Compared to a typical SPM project:

| Concept | Swift / SPM | Rust / Cargo |
|---|---|---|
| Project manifest | `Package.swift` | `Cargo.toml` |
| Source directory | `Sources/TargetName/` | `src/` |
| Binary entry point | `Sources/TargetName/main.swift` or `@main` | `src/main.rs` |
| Library root | No single root file – all files in `Sources/TargetName/` are peers | `src/lib.rs` |
| Tests | `Tests/TargetNameTests/` | `tests/` (integration) and `src/` (unit tests inline) |
| Examples | Not built-in (sometimes a separate target) | `examples/` |

### Binary, library, or both

A Cargo project can produce a binary, a library, or both. The presence of `src/main.rs` creates a binary target; `src/lib.rs` creates a library target. Having both files means the project is simultaneously a runnable program and a library that other crates can depend on.

In SPM, you would declare separate targets in `Package.swift` for this – one `.executableTarget` and one `.target`. With Cargo, the convention is filesystem-driven.

### Unit tests live next to the code

One of Rust's most distinctive conventions is that unit tests go *inside* the source files they test, in a conditionally compiled module:

```rust
// src/lib.rs

pub fn add(a: i32, b: i32) -> i32 {
    a + b
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_add() {
        assert_eq!(add(2, 3), 5);
    }
}
```

The `#[cfg(test)]` attribute tells the compiler to include this module only when running tests. This is different from Swift's convention of placing tests in a separate target – in Rust, unit tests have direct access to private functions and types because they live in the same module.

Integration tests – tests that exercise your public API from the outside – go in the `tests/` directory. Each `.rs` file there is compiled as a separate crate that depends on your library, similar to how a separate test target works in SPM.

## Dependencies and crates.io

Rust's package registry is [crates.io](https://crates.io/). Adding a dependency is a one-line edit to `Cargo.toml`:

```toml
[dependencies]
serde = "1.0"
```

Or use the command line:

```sh
cargo add serde
```

### Version requirements

Cargo uses [semver](https://semver.org/) for version resolution. The version string `"1.0"` is shorthand for `"^1.0"`, meaning "any semver-compatible version from 1.0.0 up to (but not including) 2.0.0." This is similar to SPM's `.upToNextMajor(from: "1.0.0")`.

Common version specifiers:

| Specifier | Meaning | SPM equivalent |
|---|---|---|
| `"1.0"` or `"^1.0"` | >= 1.0.0, < 2.0.0 | `.upToNextMajor(from: "1.0.0")` |
| `"~1.0.3"` | >= 1.0.3, < 1.1.0 | `.upToNextMinor(from: "1.0.3")` |
| `"=1.0.4"` | Exactly 1.0.4 | `.exact("1.0.4")` |

### Dependency sources

While crates.io is the default, Cargo also supports dependencies from Git repositories and local paths:

```toml
[dependencies]
# From crates.io (default)
serde = "1.0"

# From a Git repository
my_crate = { git = "https://github.com/user/my_crate", branch = "main" }

# From a local path (useful during development)
my_local_crate = { path = "../my_local_crate" }
```

This maps closely to SPM's `.package(url:)` and local package references.

## Workspaces

A Cargo workspace groups multiple related packages under a single top-level `Cargo.toml`. All packages in the workspace share a single `target/` directory and a single `Cargo.lock`, which ensures consistent dependency versions across the project.

```toml
# Cargo.toml (workspace root)
[workspace]
members = [
    "core",
    "cli",
    "wasm-bindings",
]
```

Each member is a full Cargo package with its own `Cargo.toml` and `src/` directory. They can depend on each other using path dependencies:

```toml
# cli/Cargo.toml
[dependencies]
core = { path = "../core" }
```

This is analogous to a Swift package with multiple targets:

```swift
// Swift – Package.swift with multiple targets
let package = Package(
    name: "MyProject",
    targets: [
        .target(name: "Core"),
        .executableTarget(name: "CLI", dependencies: ["Core"]),
    ]
)
```

The difference is that each workspace member in Rust is a fully independent package that could, in principle, be published to crates.io separately. SPM targets within a single package are more tightly coupled.

Workspaces are particularly useful when you have a shared core library with multiple frontends – a CLI, a Wasm module, and a native library, for instance. This is a common pattern in the Rust ecosystem and one you will likely use if you are building cross-platform code.

## Build profiles

Cargo has two built-in build profiles that correspond directly to Xcode's Debug and Release configurations:

| Profile | Cargo command | Optimizations | Debug info | Xcode equivalent |
|---|---|---|---|---|
| `dev` | `cargo build` | Off (`opt-level = 0`) | Full | Debug |
| `release` | `cargo build --release` | On (`opt-level = 3`) | Limited (line tables only) | Release |

The performance difference between dev and release builds is dramatic in Rust – much more so than in Swift. Unoptimized Rust code can be 10–100x slower than optimized code, particularly for computation-heavy workloads. Always benchmark with `--release`.

You can customize profiles in `Cargo.toml`:

```toml
[profile.dev]
opt-level = 1  # slight optimization for faster dev builds

[profile.release]
lto = true     # link-time optimization for smaller/faster binaries
```

You can also define entirely custom profiles that inherit from the built-in ones – something that requires scheme configuration in Xcode.

## Essential Cargo commands

Here is a summary of the commands you will use most often, with their Swift equivalents:

| Command | What it does | Swift equivalent |
|---|---|---|
| `cargo new name` | Create a new binary project | `swift package init --type executable` |
| `cargo new name --lib` | Create a new library project | `swift package init --type library` |
| `cargo build` | Compile (dev profile) | `swift build` |
| `cargo check` | Type-check quickly without linking | No exact equivalent |
| `cargo build --release` | Compile (release profile) | `swift build -c release` |
| `cargo run` | Build and run | `swift run` |
| `cargo test` | Run all tests | `swift test` |
| `cargo doc --open` | Generate and open documentation | No direct equivalent |
| `cargo clippy` | Run the linter | SwiftLint |
| `cargo fmt` | Format code | SwiftFormat / swift-format |
| `cargo add crate_name` | Add a dependency | Edit `Package.swift` manually |
| `cargo update` | Update dependencies | `swift package update` |
| `cargo clean` | Delete build artifacts | Delete DerivedData |

### cargo doc

`cargo doc` deserves special mention. It generates HTML documentation from your code's doc comments and the documentation of all your dependencies. Running `cargo doc --open` builds the docs and opens them in your browser. The result is similar to what you get from DocC in Swift, but it happens automatically for every dependency – you always have local, searchable documentation for your entire dependency tree.

Doc comments in Rust use `///` (for items) or `//!` (for modules), and support Markdown:

```rust
/// Adds two numbers together.
///
/// # Examples
///
/// ```
/// let result = my_crate::add(2, 3);
/// assert_eq!(result, 5);
/// ```
pub fn add(a: i32, b: i32) -> i32 {
    a + b
}
```

The code in `# Examples` blocks is actually compiled and run during `cargo test` – a feature called *doc tests*. This ensures that your documentation examples stay in sync with your code.

## Key differences and gotchas

**No Xcode project files**: there is no `.xcodeproj` or `.xcworkspace`. The project structure is defined entirely by the filesystem layout and `Cargo.toml`. This means no merge conflicts on project files – a genuine relief if you have ever dealt with `.pbxproj` conflicts.

**Crate vs. package**: in Rust terminology, a *crate* is a compilation unit (either a library or a binary), and a *package* is one or more crates described by a `Cargo.toml`. In practice, most packages contain a single crate, and the terms are often used interchangeably. When you add a dependency, you are depending on a crate published from a package.

**Build times**: Rust's initial compile of a project with many dependencies can be slow – significantly slower than the equivalent in Swift. The trade-off is that the compiler does more work upfront (monomorphization, borrow checking, LLVM optimization). Incremental rebuilds during development are usually fast, but clean builds of large projects can take several minutes.

**No built-in REPL**: Swift has the `swift` REPL and Xcode Playgrounds for interactive exploration. Rust has no official REPL. The [Rust Playground](https://play.rust-lang.org/) is a web-based alternative, and [evcxr](https://github.com/evcxr/evcxr) provides a third-party REPL, but rapid experimentation typically happens through small test functions or example programs.

**`Cargo.toml` is not code**: unlike `Package.swift`, you cannot use conditional logic in `Cargo.toml`. If you need platform-specific dependencies or conditional compilation, you use `#[cfg(...)]` attributes in your source code and `[target.'cfg(...)'.dependencies]` sections in the manifest.

## Further reading

- [The Cargo Book](https://doc.rust-lang.org/cargo/): the definitive reference for Cargo
- [Cargo.toml format](https://doc.rust-lang.org/cargo/reference/manifest.html): complete manifest reference
- [Specifying Dependencies](https://doc.rust-lang.org/cargo/reference/specifying-dependencies.html): version requirements, features, and dependency sources
- [Workspaces](https://doc.rust-lang.org/cargo/reference/workspaces.html): managing multi-crate projects
- [crates.io](https://crates.io/): the Rust package registry
- [lib.rs](https://lib.rs/): an alternative crates.io frontend with better search and categorization
- [Rust Playground](https://play.rust-lang.org/): run Rust code in your browser
