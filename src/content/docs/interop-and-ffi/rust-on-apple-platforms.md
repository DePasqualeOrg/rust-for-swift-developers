---
title: Rust on Apple Platforms
sidebar:
  order: 29
---

The previous chapter covered C FFI in the abstract – calling C from Rust and exposing Rust to C callers. This chapter makes it concrete: how do you actually get Rust code running inside an iOS or macOS app? The answer involves cross-compilation, static libraries, and binding generators that turn raw FFI into ergonomic Swift APIs.

If you are a Swift developer interested in writing performance-critical libraries in Rust – or porting existing Rust libraries to your Apple apps – this chapter walks through the practical toolchain, from adding compilation targets to generating Swift packages with UniFFI.

## Cross-compiling Rust for Apple targets

Rust's compiler supports Apple platforms as first-class targets. You add them with `rustup`:

```sh
# macOS (Apple Silicon)
rustup target add aarch64-apple-darwin

# macOS (Intel)
rustup target add x86_64-apple-darwin

# iOS (physical devices)
rustup target add aarch64-apple-ios

# iOS Simulator (Apple Silicon Mac)
rustup target add aarch64-apple-ios-sim

# iOS Simulator (Intel Mac)
rustup target add x86_64-apple-ios
```

These are the most common triples for macOS and iOS work. tvOS, watchOS, visionOS, and Mac Catalyst have their own target triples as well; check the current Rust platform-support documentation when you need to expand beyond this basic matrix.

Once installed, you can cross-compile with `--target`:

```sh
cargo build --release --target aarch64-apple-ios
```

The compiled library lands in `target/aarch64-apple-ios/release/`. For a library crate, this produces a `.rlib` (Rust's native format) and, if configured, a static library (`.a`) or dynamic library (`.dylib`).

### Producing a static library

To generate a C-compatible static library, set the crate type in `Cargo.toml`:

```toml
[lib]
crate-type = ["staticlib"]
```

This produces a `libmy_crate.a` file that Xcode can link against. You also need a C header file that declares the `extern "C"` functions – either written by hand or generated with `cbindgen` (covered in the previous chapter).

## Building static libraries for Xcode

A typical workflow for including a Rust static library in an Xcode project:

1. **Build for each architecture** you need (device and simulator).
2. **Package the slices as an XCFramework** (preferred), or use `lipo` only for older workflows that still need a fat binary.
3. **Add the `.a` file and header** to your Xcode project.
4. **Configure linker flags** in your Xcode build settings.

```sh
# Build for iOS device and simulator
cargo build --release --target aarch64-apple-ios
cargo build --release --target aarch64-apple-ios-sim

# Create an XCFramework (preferred over lipo for modern Xcode)
xcodebuild -create-xcframework \
    -library target/aarch64-apple-ios/release/libmy_crate.a \
    -headers include/ \
    -library target/aarch64-apple-ios-sim/release/libmy_crate.a \
    -headers include/ \
    -output MyRustLib.xcframework
```

The XCFramework bundles per-platform slices with their headers, making it straightforward to distribute and integrate in Xcode. This is the same format Apple uses for its own binary frameworks.

### Build automation with `build.rs`

For larger projects, you can automate the header generation step using `cbindgen` in a Cargo build script:

```rust
// build.rs
fn main() {
    let crate_dir = std::env::var("CARGO_MANIFEST_DIR").unwrap();
    cbindgen::Builder::new()
        .with_crate(&crate_dir)
        .with_language(cbindgen::Language::C)
        .generate()
        .expect("Unable to generate bindings")
        .write_to_file("include/my_crate.h");
}
```

## UniFFI: generating Swift bindings from Rust

Writing C headers and `UnsafePointer`-based Swift wrappers by hand is tedious and error-prone. [UniFFI](https://mozilla.github.io/uniffi-rs/) (developed by Mozilla) automates this: you define your API in Rust and UniFFI generates idiomatic Swift bindings complete with a Swift package.

### How UniFFI works

UniFFI reads your Rust function signatures and type definitions (annotated with UniFFI macros), generates a C FFI layer internally, and produces language-specific bindings on top. For Swift, it outputs:

- A `.swift` file with native Swift types, classes, and functions.
- The underlying C header and module map.
- Bindings that you package together with a Rust library you build separately (typically as a `staticlib` or `cdylib`).

The generated Swift code uses value types, enums, and error handling that feel natural – not raw pointer manipulation.

### A minimal UniFFI example

Here is a small Rust library exposed to Swift via UniFFI.

First, add UniFFI to your package. Use the current UniFFI release rather than copying a stale version number from a guide:

```sh
cargo add uniffi
cargo add --build uniffi --features build
```

Then configure the library target in `Cargo.toml`:

```toml
[lib]
name = "my_math"
crate-type = ["staticlib", "cdylib"]
```

`staticlib` is convenient when you plan to package an XCFramework for Apple targets. Keeping `cdylib` alongside it also matches UniFFI's broader C-compatible interop workflows.

Create a `build.rs` to run UniFFI's scaffolding generator:

```rust
// build.rs
fn main() {
    uniffi::generate_scaffolding("src/my_math.udl").unwrap();
}
```

Define the interface in a UDL (UniFFI Definition Language) file:

```
// src/my_math.udl
namespace my_math {
    double hypotenuse(double a, double b);
    Statistics compute_stats(sequence<double> values);
};

dictionary Statistics {
    double mean;
    double median;
    double std_dev;
};
```

Implement the functions in Rust:

```rust
// src/lib.rs
uniffi::include_scaffolding!("my_math");

pub fn hypotenuse(a: f64, b: f64) -> f64 {
    (a * a + b * b).sqrt()
}

pub struct Statistics {
    pub mean: f64,
    pub median: f64,
    pub std_dev: f64,
}

pub fn compute_stats(values: Vec<f64>) -> Statistics {
    if values.is_empty() {
        return Statistics { mean: 0.0, median: 0.0, std_dev: 0.0 };
    }

    let n = values.len() as f64;
    let mean = values.iter().sum::<f64>() / n;

    let mut sorted = values.clone();
    sorted.sort_by(f64::total_cmp);
    let median = if sorted.len() % 2 == 0 {
        let mid = sorted.len() / 2;
        (sorted[mid - 1] + sorted[mid]) / 2.0
    } else {
        sorted[sorted.len() / 2]
    };

    let variance = values.iter()
        .map(|x| (x - mean).powi(2))
        .sum::<f64>() / n;
    let std_dev = variance.sqrt();

    Statistics { mean, median, std_dev }
}
```

### Using the proc-macro approach

UniFFI also supports a proc-macro approach that avoids the UDL file entirely. You annotate your Rust code directly:

```rust
// src/lib.rs
uniffi::setup_scaffolding!();

#[derive(uniffi::Record)]
pub struct Statistics {
    pub mean: f64,
    pub median: f64,
    pub std_dev: f64,
}

#[uniffi::export]
pub fn hypotenuse(a: f64, b: f64) -> f64 {
    (a * a + b * b).sqrt()
}

#[uniffi::export]
pub fn compute_stats(values: Vec<f64>) -> Statistics {
    if values.is_empty() {
        return Statistics { mean: 0.0, median: 0.0, std_dev: 0.0 };
    }

    let n = values.len() as f64;
    let mean = values.iter().sum::<f64>() / n;
    let mut sorted = values.clone();
    sorted.sort_by(f64::total_cmp);
    let median = if sorted.len() % 2 == 0 {
        let mid = sorted.len() / 2;
        (sorted[mid - 1] + sorted[mid]) / 2.0
    } else {
        sorted[sorted.len() / 2]
    };
    let variance = values.iter().map(|x| (x - mean).powi(2)).sum::<f64>() / n;
    let std_dev = variance.sqrt();
    Statistics { mean, median, std_dev }
}
```

Generating the foreign-language bindings is a separate step from compiling the Rust library itself. The exact `uniffi-bindgen` workflow changes across UniFFI releases, so treat the current [UniFFI user guide](https://mozilla.github.io/uniffi-rs/) as authoritative rather than copying an old one-line command from a blog post.

### The generated Swift code

After building and running `uniffi-bindgen`, you get Swift code that looks like this:

```swift
// Generated by UniFFI
public func hypotenuse(a: Double, b: Double) -> Double { ... }

public struct Statistics {
    public var mean: Double
    public var median: Double
    public var stdDev: Double
}

public func computeStats(values: [Double]) -> Statistics { ... }
```

Notice that UniFFI automatically converts naming conventions – `std_dev` in Rust becomes `stdDev` in Swift, and `Vec<f64>` becomes `[Double]`. The generated functions handle all the pointer manipulation, memory management, and type conversion internally.

### Using the generated bindings in Swift

```swift
// Swift
import MyMath

let h = hypotenuse(a: 3.0, b: 4.0)
print("Hypotenuse: \(h)") // Hypotenuse: 5.0

let stats = computeStats(values: [1.0, 2.0, 3.0, 4.0, 5.0])
print("Mean: \(stats.mean)")       // Mean: 3.0
print("Median: \(stats.median)")   // Median: 3.0
print("Std Dev: \(stats.stdDev)")  // Std Dev: 1.4142135623730951
```

This is the experience UniFFI is designed for – you write Rust, and Swift callers get a native-feeling API without touching any unsafe code.

### UniFFI type mappings

UniFFI supports a range of type mappings between Rust and Swift:

| Rust type | Swift type |
|---|---|
| `String` | `String` |
| `Vec<T>` | `[T]` |
| `HashMap<K, V>` | `[K: V]` |
| `Option<T>` | `T?` |
| `Result<T, E>` | `throws` |
| `bool` | `Bool` |
| `f64` / `f32` | `Double` / `Float` |
| `i32`, `u64`, etc. | `Int32`, `UInt64`, etc. |
| Structs (with `#[derive(uniffi::Record)]`) | Swift structs |
| Enums (with `#[derive(uniffi::Enum)]`) | Swift enums |
| `Arc<T>` (with `#[derive(uniffi::Object)]`) | Swift classes (reference types) |

UniFFI also maps Rust's `Result<T, E>` to Swift's `throws` pattern, so error handling feels natural on both sides.

## Alternative tools

### `swift-bridge`

[`swift-bridge`](https://github.com/chinedufn/swift-bridge) takes a different approach from UniFFI. Rather than using an intermediate definition file, you declare the bridge inline in Rust:

```rust
// Rust
#[swift_bridge::bridge]
mod ffi {
    extern "Rust" {
        fn add(a: i32, b: i32) -> i32;
    }
}

fn add(a: i32, b: i32) -> i32 {
    a + b
}
```

`swift-bridge` generates both the C FFI layer and Swift wrapper code. It supports passing owned and borrowed strings, `Vec<T>`, `Option<T>`, and custom types. It is more lightweight than UniFFI but has a smaller community and fewer features.

### `cargo-xcode`

[`cargo-xcode`](https://crates.io/crates/cargo-xcode) generates an Xcode project from a Cargo workspace, allowing Xcode to build your Rust code as part of the normal build process. It does not generate Swift bindings – it focuses on the build integration problem. You would combine it with hand-written C headers or another binding generator.

## Practical considerations

### Binary size

Rust static libraries pull in code from the Rust standard library and your crate's dependencies, which adds to your app's binary size. For a minimal library, expect roughly 1 – 3 MB of additional binary size after stripping and optimization. You can reduce this with:

```toml
# Cargo.toml
[profile.release]
opt-level = "z"    # optimize for size
lto = true         # link-time optimization
strip = true       # strip debug symbols
codegen-units = 1  # better optimization at cost of compile time
```

Do not treat that number as a hard rule: Rust does not bring a large managed runtime, but you are still shipping another compiled codebase and its dependencies, so measure the final app binary rather than assuming parity with a native Swift implementation.

### Build integration

The biggest practical challenge is integrating Rust's build system (Cargo) with Xcode's build system. The common approaches are:

- **Run Script build phase**: add a shell script to your Xcode target that runs `cargo build` with the appropriate target.
- **Makefile or shell script**: build the Rust library separately and check the artifacts into the project (simpler but less maintainable).
- **`cargo-xcode`**: generates an Xcode project that wraps the Cargo build.

Each approach has tradeoffs. The Run Script phase keeps everything in sync but slows down Xcode builds. Building separately is faster during iteration but risks stale artifacts.

### Debugging

Debugging Rust code called from Swift is challenging. Xcode's debugger (LLDB) can step into Rust code if debug symbols are present, but the experience is rough – Rust's types do not display neatly in Xcode's variable inspector. Practical strategies include:

- **Logging**: use the `log` crate in Rust and forward messages to `os_log` or print to stderr.
- **Testing in isolation**: test your Rust library with `cargo test` before integrating with Swift. Rust's test tooling is more convenient for debugging Rust code than stepping through it in Xcode.
- **Debug builds**: compile with `cargo build` (not `--release`) to preserve debug symbols and disable optimizations.

## Key differences and gotchas

**Platform-specific builds are required**: Xcode hides most target-triple and SDK-selection details behind schemes and destinations, but Rust requires explicit cross-compilation for each target triple. You must build separately for `aarch64-apple-ios` and `aarch64-apple-ios-sim`, then package them into an XCFramework.

**Two build systems, two dependency managers**: your project now has both `Package.swift` (or an Xcode project) and `Cargo.toml`. Keeping these in sync and automating the build pipeline is the main source of friction.

**UniFFI generates code at build time**: the generated Swift bindings must be regenerated whenever the Rust API changes. If the generation step is not part of your build pipeline, the Swift and Rust sides can drift apart, causing runtime crashes rather than compile errors.

**Async bridging varies by tool**: Recent UniFFI releases can map Rust's `async fn` to Swift `async` APIs, but the generated bindings still need to drive Rust futures from the foreign-language side. Check the current UniFFI guide when you adopt async APIs rather than assuming every older example still applies unchanged.

**Thread safety annotations are lost**: Rust's `Send` and `Sync` traits, which express thread safety at compile time, have no equivalent in the C FFI layer. When Swift code calls Rust across threads, the Rust library must ensure its own thread safety – the Swift compiler will not help enforce it at the boundary.

## Further reading

- [UniFFI User Guide](https://mozilla.github.io/uniffi-rs/): the official guide for generating multi-language bindings
- [Building a Rust library for iOS](https://bignerdranch.com/blog/building-an-ios-app-in-rust-part-1/): a practical tutorial
- [`swift-bridge` documentation](https://chinedufn.github.io/swift-bridge/): the alternative to UniFFI for Rust-Swift interop
- [Rust cross-compilation](https://rust-lang.github.io/rustup/cross-compilation.html): the `rustup` guide to cross-compilation targets
- [`cargo-xcode`](https://crates.io/crates/cargo-xcode): Xcode project generation for Cargo workspaces
