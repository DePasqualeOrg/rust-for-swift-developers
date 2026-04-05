---
title: Crates and Dependencies
sidebar:
  order: 25
---

Rust's package ecosystem is one of the language's greatest strengths. While earlier chapters introduced Cargo and project structure, this chapter takes a deeper look at how Rust developers discover, evaluate, and integrate third-party code – and how the ecosystem compares to what you know from Swift.

If you have worked with Swift Package Manager and the Swift Package Index, the concepts will be familiar. But the Rust ecosystem is larger, more centralized, and more convention-driven. Understanding how it works will help you move faster and make better choices when building real projects.

## The registry: crates.io vs Swift Package Index

Rust has a single, official package registry: [crates.io](https://crates.io/). Every open-source Rust library (called a *crate*) is published there. When you add a dependency by name in `Cargo.toml`, Cargo resolves it from crates.io by default.

Swift's ecosystem is more fragmented. There is no official Apple-run package registry equivalent to crates.io. The [Swift Package Index](https://swiftpackageindex.com/) is a community-run discovery tool that indexes packages from GitHub, but it is not a registry in the same sense – SPM resolves packages directly from Git URLs, not from a central store. The [Swift Package Registry](https://github.com/apple/swift-package-manager/blob/main/Documentation/PackageRegistry/PackageRegistryUsage.md) specification exists, but adoption is limited.

This difference has practical consequences:

- **Discovery**: crates.io has built-in search, download counts, and categorization. You can evaluate a crate's popularity and maintenance status directly. The Swift Package Index provides similar metadata but is not the source of truth for resolution.
- **Publishing**: publishing a Rust crate is a `cargo publish` command. Publishing a Swift package means pushing to a Git repository and optionally registering it with the Swift Package Index.
- **Naming**: crate names are globally unique on crates.io. Swift packages are identified by their Git URL, so naming conflicts are less of a concern but discoverability is harder.

For a curated alternative to crates.io's search, [lib.rs](https://lib.rs/) offers better categorization and editorial recommendations.

## Adding dependencies

Adding a dependency in Rust is a one-line change to `Cargo.toml`:

```toml
# Rust: Cargo.toml
[dependencies]
serde = "1.0"
```

Or use the command line:

```sh
cargo add serde
```

In Swift, you edit `Package.swift`:

```swift
// Swift – Package.swift
let package = Package(
    name: "MyApp",
    dependencies: [
        .package(url: "https://github.com/apple/swift-argument-parser", from: "1.0.0"),
    ],
    targets: [
        .executableTarget(
            name: "MyApp",
            dependencies: [
                .product(name: "ArgumentParser", package: "swift-argument-parser"),
            ]
        ),
    ]
)
```

Notice that Swift requires both a package-level dependency declaration *and* a per-target dependency reference. Rust's model is simpler: dependencies are declared once in `[dependencies]` and are available throughout the crate.

## Semantic versioning and the `^` operator

Cargo uses [semantic versioning](https://semver.org/) for all version resolution. When you write `"1.0"` in `Cargo.toml`, it is shorthand for `"^1.0"` – meaning any semver-compatible version from 1.0.0 up to (but not including) 2.0.0.

The `^` operator is the default and most common choice. It allows patch and minor updates while preventing breaking changes:

| Cargo specifier | Accepted range | SPM equivalent |
|---|---|---|
| `"1.0"` or `"^1.0"` | >= 1.0.0, < 2.0.0 | `.upToNextMajor(from: "1.0.0")` |
| `"~1.0.3"` | >= 1.0.3, < 1.1.0 | `.upToNextMinor(from: "1.0.3")` |
| `"=1.0.4"` | Exactly 1.0.4 | `.exact("1.0.4")` |
| `">=1.2, <1.5"` | >= 1.2.0, < 1.5.0 | `.package(url:..., "1.2.0"..<"1.5.0")` |

There is a subtlety with versions below 1.0.0. Under semver, 0.x versions make no stability guarantees. Cargo treats this range more conservatively: `"^0.2.3"` means >= 0.2.3 and < 0.3.0 (not < 1.0.0). This means even a minor version bump in a 0.x crate is treated as potentially breaking.

SPM uses `.upToNextMajor(from:)` as its default, which behaves the same way for 1.x+ versions. The pre-1.0 behavior differs slightly – SPM's `.upToNextMajor(from: "0.2.0")` allows up to < 1.0.0 unless you use `.upToNextMinor`.

## Cargo.lock vs Package.resolved

When you build for the first time, Cargo generates a `Cargo.lock` file that pins the exact version of every dependency in the tree. This is directly analogous to Swift's `Package.resolved`.

The lockfile serves the same purpose as `Package.resolved`, but the commit convention is worth calling out explicitly:

- **When in doubt, commit it**: current Cargo guidance is to check `Cargo.lock` into version control by default, including for libraries. This keeps local development and CI deterministic.
- **Library compatibility is still tested separately**: if you maintain a library, you can still run `cargo update` or a dedicated latest-dependencies CI job to verify that your semver ranges resolve cleanly against newer compatible releases.

To update pinned versions within the allowed semver range:

```sh
# Rust
cargo update

# Swift
swift package update
```

## Cargo features

Cargo features are one of the most powerful aspects of the dependency system and have no direct equivalent in SPM. Features let a crate define optional functionality that consumers can enable or disable at compile time.

Consider the `serde` crate for serialization. Its core library provides the serialization traits, but the derive macros are behind a feature flag:

```toml
# Without derive macros
serde = "1.0"

# With derive macros enabled
serde = { version = "1.0", features = ["derive"] }
```

The `reqwest` HTTP client uses features to control which TLS backend it uses and whether it includes JSON support:

```toml
reqwest = { version = "0.12", features = ["json", "rustls-tls"] }
```

Features work through conditional compilation. Inside the crate's source code, feature-gated code uses `#[cfg(feature = "...")]`:

```rust
// Fragment – inside a library's impl block
#[cfg(feature = "json")]
pub fn json_body(&self) -> Result<serde_json::Value, Error> {
    // only compiled when the "json" feature is enabled
    ...
}
```

As a crate author, you define features in your `Cargo.toml`:

```toml
[features]
default = ["json"]
json = ["dep:serde_json"]
rustls-tls = ["dep:rustls"]
```

The `default` feature is enabled when a consumer adds your crate without specifying features. Consumers can opt out of defaults:

```toml
my_crate = { version = "1.0", default-features = false, features = ["json"] }
```

In Swift, the closest equivalent is conditional compilation with build settings and `#if` flags, but there is no standard mechanism for a package to advertise optional feature sets that consumers can toggle. SPM's build settings are more limited – you can pass `-D` flags, but there is no structured feature system.

## Documentation with `///` and docs.rs

Rust has a strong documentation culture, and the tooling supports it well. Doc comments use `///` for items and `//!` for modules, with full Markdown support:

```rust
/// Parses a configuration file from the given path.
///
/// Returns an error if the file does not exist or contains
/// invalid syntax.
///
/// # Examples
///
/// ```
/// use my_crate::parse_config;
///
/// let config = parse_config("config.toml").unwrap();
/// assert_eq!(config.name, "my_app");
/// ```
pub fn parse_config(path: &str) -> Result<Config, ConfigError> {
    // ...
}
```

The `# Examples` section contains executable Rust code that is compiled and run during `cargo test`. These are called *doc tests*, and they ensure your documentation examples do not go stale. This is analogous to DocC's code snippets in Swift, but Rust doc tests are tested automatically as part of the standard test suite.

Generate documentation locally with:

```sh
cargo doc --open
```

This builds HTML documentation for your project and all its dependencies, then opens it in your browser.

Every crate published to crates.io automatically gets documentation generated and hosted at [docs.rs](https://docs.rs/). This means you can read the API documentation for any published crate without downloading it – just visit `docs.rs/<crate_name>`. There is no equivalent centralized documentation host in the Swift ecosystem; you typically rely on a package's README or manually generated DocC archives.

In Swift, you use `///` comments with DocC syntax:

```swift
// Swift
/// Parses a configuration file from the given path.
///
/// - Parameter path: The file path to read.
/// - Returns: A parsed `Config` value.
/// - Throws: `ConfigError` if the file is missing or malformed.
func parseConfig(path: String) throws -> Config {
    // ...
}
```

The markup style differs – Swift uses DocC's `-` Parameter and `- Returns` conventions, while Rust uses `# Section` headers – but the intent is the same.

## Notable crates

The Rust ecosystem has a rich set of libraries. Here are some of the most widely used crates and their closest Swift counterparts:

### serde: serialization and deserialization

[serde](https://docs.rs/serde) is the standard serialization framework. It provides traits (`Serialize` and `Deserialize`) that can be derived on your types, plus format-specific crates like `serde_json` and `toml`.

```rust
use serde::{Deserialize, Serialize};

#[derive(Debug, Serialize, Deserialize)]
struct User {
    name: String,
    age: u32,
    email: String,
}

fn main() {
    let user = User {
        name: "Alice".to_string(),
        age: 30,
        email: "alice@example.com".to_string(),
    };

    let json = serde_json::to_string_pretty(&user).unwrap();
    println!("{json}");

    let parsed: User = serde_json::from_str(&json).unwrap();
    println!("{:?}", parsed);
}
```

In Swift, the equivalent is `Codable` (`Encodable` + `Decodable`) with `JSONEncoder`/`JSONDecoder`. The mental model is nearly identical – both use compiler-generated implementations that you can customize when needed. serde is more flexible in terms of supported formats (JSON, TOML, YAML, MessagePack, bincode, and many more), while Swift's `Codable` is tightly integrated with Foundation's encoders and decoders.

### clap: CLI argument parsing

[clap](https://docs.rs/clap) is the standard library for parsing command-line arguments. With its derive API, you define your CLI interface as a struct:

```rust
use clap::Parser;

/// A simple greeting program
#[derive(Parser, Debug)]
struct Args {
    /// Name of the person to greet
    #[arg(short, long)]
    name: String,

    /// Number of times to greet
    #[arg(short, long, default_value_t = 1)]
    count: u8,
}

fn main() {
    let args = Args::parse();
    for _ in 0..args.count {
        println!("Hello, {}!", args.name);
    }
}
```

The Swift equivalent is [swift-argument-parser](https://github.com/apple/swift-argument-parser), which uses a similar derive-style approach with `ParsableCommand`. Both libraries generate help text and validate input automatically.

### reqwest: HTTP client

[reqwest](https://docs.rs/reqwest) is the most popular HTTP client library, providing both blocking and async APIs:

```rust
// Fragment – requires reqwest and tokio dependencies
#[tokio::main]
async fn main() -> Result<(), reqwest::Error> {
    let body = reqwest::get("https://httpbin.org/get")
        .await?
        .text()
        .await?;
    println!("{body}");
    Ok(())
}
```

In Swift, `URLSession` is the built-in HTTP client. reqwest fills the same role but as a third-party crate, since Rust's standard library does not include HTTP functionality.

### tokio: async runtime

[tokio](https://docs.rs/tokio) is the most widely used async runtime for Rust. Unlike Swift, where the async runtime is built into the language, Rust's `async`/`await` syntax requires an external runtime to execute futures. tokio provides that runtime along with async I/O, timers, channels, and other concurrency primitives.

```rust
// Fragment – requires tokio dependency
#[tokio::main]
async fn main() {
    let handle = tokio::spawn(async {
        // runs concurrently
        42
    });

    let result = handle.await.unwrap();
    println!("Got: {result}");
}
```

There is no Swift equivalent because Swift's async runtime is part of the language itself. The closest analogy is that tokio is to Rust what the Swift concurrency runtime (the cooperative thread pool that powers `async`/`await`, `Task`, and `TaskGroup`) is to Swift – except in Rust, you choose and configure it explicitly.

### rand: random number generation

[rand](https://docs.rs/rand) provides random number generation. Rust's standard library does not include random number utilities, so this crate fills a gap that Swift covers with its standard library.

```rust
// Fragment – requires rand 0.9+ dependency
use rand::Rng;

fn main() {
    let mut rng = rand::rng();
    let n: u32 = rng.random_range(1..=100);
    println!("Random number: {n}");

    let coin: bool = rng.random();
    println!("Coin flip: {coin}");
}
```

In Swift, you would use `Int.random(in: 1...100)` or `Bool.random()` – these are built into the standard library.

## Key differences and gotchas

**Smaller standard library**: Rust's standard library is intentionally minimal compared to Swift's Foundation framework. Functionality that Swift developers take for granted – HTTP networking, JSON parsing, random numbers, date/time handling, regex – requires third-party crates in Rust. This is a design choice: the standard library moves slowly and maintains strict backward compatibility, so the ecosystem relies on crates that can evolve independently.

**Feature flags matter**: when adding a crate, check its documentation for available features. Many crates ship with a minimal default feature set and require you to opt into additional functionality. Forgetting to enable a feature is a common source of confusion when a function or type seems to be missing.

**Version 0.x crates are common**: many widely used, production-quality crates have not reached version 1.0. This does not necessarily indicate instability – it often means the authors have not committed to a stable API. In practice, 0.x crates like `tokio` (which was 0.x for years before reaching 1.0) are battle-tested and widely deployed. Check download counts and maintenance activity rather than relying on the version number alone.

**Crate selection can be overwhelming**: crates.io hosts hundreds of thousands of crates. For common tasks, the community has converged on standard choices (serde for serialization, tokio for async, clap for CLI parsing), but for less common needs, evaluating options takes time. The [Blessed.rs](https://blessed.rs/crates) guide and lib.rs categories can help.

**No dynamic linking by default**: Rust crates are statically linked into your binary. This means your final executable is self-contained with no shared library dependencies to manage, but it also means compile times grow with your dependency tree. Swift frameworks and dynamic libraries have no direct equivalent in the standard Rust build process.

## Further reading

- [The Cargo Book – Specifying Dependencies](https://doc.rust-lang.org/cargo/reference/specifying-dependencies.html): version requirements, features, and dependency sources
- [crates.io](https://crates.io/): the Rust package registry
- [lib.rs](https://lib.rs/): curated crate discovery with better search and categorization
- [docs.rs](https://docs.rs/): automatically generated documentation for every published crate
- [Blessed.rs](https://blessed.rs/crates): community-curated recommendations for common tasks
- [The Cargo Book – Features](https://doc.rust-lang.org/cargo/reference/features.html): how features work in detail
- [serde.rs](https://serde.rs/): the serde framework's documentation site
- [Tokio tutorial](https://tokio.rs/tokio/tutorial): getting started with the tokio async runtime
