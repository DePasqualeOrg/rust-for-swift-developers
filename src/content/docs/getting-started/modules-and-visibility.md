---
title: Modules and Visibility
sidebar:
  order: 3
---

Every nontrivial program needs a way to organize code into logical units and control what is visible to the outside world. Swift and Rust both provide this, but they approach it differently. Swift uses file-scoped access control (`public`, `internal`, `fileprivate`, `private`) within a module that corresponds to a build target. Rust uses an explicit module tree that you build up with `mod` declarations, with visibility controlled by `pub` and its variants.

## The module tree

In Swift, every source file in a target is automatically part of that target's module. You do not declare the module structure – you simply create files, and the compiler collects them. Access control is file-scoped: `internal` (the default) means "visible within this module," `private` means "visible within this file's scope," and so on.

Rust works differently. Every crate has an explicit module tree rooted at `src/lib.rs` (for libraries) or `src/main.rs` (for binaries). Modules are declared with the `mod` keyword, and the compiler only includes code that is reachable from the root through `mod` declarations. Creating a file is not enough – you must also tell the compiler about it.

Here is a small example. Suppose you have this file structure:

```
src/
  lib.rs
  network.rs
  storage.rs
```

In Swift, these files would all be part of the same module automatically. In Rust, `src/lib.rs` must explicitly declare the other modules:

```rust
// src/lib.rs
mod network;
mod storage;
```

Without those `mod` declarations, `network.rs` and `storage.rs` would be ignored by the compiler entirely – no errors, no warnings, just silence. This is one of the most common surprises for developers coming from Swift.

## Defining modules

There are two ways to define a module in Rust.

### Inline modules

You can define a module directly inside a file:

```rust
mod math {
    pub fn add(a: i32, b: i32) -> i32 {
        a + b
    }

    fn internal_helper() -> i32 {
        42
    }
}

// math::internal_helper(); // error: function is private
```

This is analogous to defining a Swift enum used purely as a namespace:

```swift
// Swift
enum Math {
    static func add(_ a: Int, _ b: Int) -> Int {
        a + b
    }

    private static func internalHelper() -> Int {
        42
    }
}
```

### File-based modules

For anything beyond a few lines, you will want each module in its own file. When you write `mod network;` in `lib.rs`, the compiler looks for the module's contents in one of two places:

- `src/network.rs` (the modern convention)
- `src/network/mod.rs` (the older convention)

Both are equivalent. The community has largely moved to the flat-file convention (`network.rs`), and that is what this guide uses. The `mod.rs` style is still valid and appears in older codebases.

### Submodules and nested directories

Modules can be nested. If `network` has a submodule called `http`, the structure looks like this:

```
src/
  lib.rs
  network.rs
  network/
    http.rs
```

```rust
// src/lib.rs
mod network;
```

```rust
// src/network.rs
mod http;

pub fn connect() {
    // ...
}
```

```rust
// src/network/http.rs
pub fn get(url: &str) -> String {
    format!("GET {url}")
}
```

Notice the pattern: when a module (`network`) has submodules, the submodule files go in a directory named after the parent module (`network/`), and the parent module's own code stays in `network.rs`. The parent module declares its children with `mod http;`.

In Swift, this hierarchical structure does not exist – all files in a target are peers. The closest equivalent would be organizing files into folders for readability, but the compiler does not assign any semantic meaning to the folder structure.

## Visibility modifiers

Rust's default visibility is private – items are visible only within the module that defines them (and its submodules). This is stricter than Swift's default of `internal`, which makes items visible across the entire module (target).

Here is how the visibility modifiers compare:

| Rust | Swift | Visible to |
|---|---|---|
| (no modifier) | No exact equivalent – see below | The current module and its submodules |
| `pub(crate)` | `internal` | Anywhere within the same crate |
| `pub(super)` | (no direct equivalent) | The parent module |
| `pub` | `public` | External crates that depend on this one |

The mapping is not exact, so let's look at each one in detail.

### Private by default

In Rust, if you do not write `pub`, an item is private:

```rust
mod database {
    fn connect() -> String {
        String::from("connected")
    }

    pub fn query(sql: &str) -> String {
        let conn = connect(); // OK: same module
        format!("{conn}: {sql}")
    }
}

// database::connect(); // error: function `connect` is private
```

In Swift, the equivalent would be marking `connect` as `fileprivate` or `private`. But there is no need for any keyword in Rust – privacy is the default.

One subtlety: in Rust, submodules can see their parent's private items, but the parent cannot see a submodule's private items. Privacy flows downward:

```rust
mod parent {
    fn secret() -> i32 { 42 }

    mod child {
        pub fn reveal() -> i32 {
            super::secret() // OK: child can access parent's private items
        }
    }
}
```

This has no direct equivalent in Swift, where sibling files within a module all share `internal` visibility and there is no parent-child file relationship.

### pub(crate): internal to the crate

`pub(crate)` makes an item visible anywhere within the same crate, but not to external dependents. This is the closest match to Swift's `internal`:

```rust
// src/lib.rs
mod database;
mod api;
```

```rust
// src/database.rs
pub(crate) fn connect() -> String {
    String::from("connected")
}
```

```rust
// src/api.rs
use crate::database;

pub fn handle_request() -> String {
    let conn = database::connect(); // OK: same crate
    format!("handled with {conn}")
}
```

If `connect` were just `pub`, it would also be accessible to any external crate that depends on this library. With `pub(crate)`, it stays internal.

### pub: public API

`pub` makes an item part of your crate's public API:

```rust
// src/lib.rs
mod internal;

pub fn public_function() -> String {
    internal::helper()
}
```

```rust
// src/internal.rs
pub(crate) fn helper() -> String {
    String::from("helping")
}
```

Here, `public_function` is part of the public API. `helper` is visible within the crate but hidden from consumers. This layering – `pub` for the API surface, `pub(crate)` for shared internals, and private for everything else – is a common Rust pattern.

### pub(super): visible to the parent

`pub(super)` restricts visibility to the parent module. It is useful when a submodule needs to expose something to its parent without making it available crate-wide:

```rust
mod network {
    mod internal {
        pub(super) fn raw_connect() -> String {
            String::from("raw connection")
        }
    }

    pub fn connect() -> String {
        internal::raw_connect() // OK: parent of `internal`
    }
}
```

Swift has no direct equivalent – the closest analogy is `fileprivate`, which limits visibility to the file rather than to a parent scope.

## Paths and the use keyword

To refer to items from other modules, you use paths. Rust has three path roots:

- **`crate`**: the root of the current crate (like writing the full module path)
- **`self`**: the current module
- **`super`**: the parent module

```rust
mod models {
    pub struct User {
        pub name: String,
    }
}

mod services {
    use crate::models::User;

    pub fn create_user(name: &str) -> User {
        User {
            name: name.to_string(),
        }
    }
}
```

The `use` keyword brings items into scope, similar to Swift's `import`. The difference is granularity: in Swift, `import ModuleName` imports everything from a module. In Rust, `use` can import specific items, entire modules, or groups:

```rust
// Import a single item
use std::collections::HashMap;

// Import multiple items from the same path
use std::io::{self, Read, Write};

// Import everything (generally discouraged, like `using namespace` in C++)
use std::collections::*;
```

The Swift analogy:

```swift
// Swift
import Foundation          // import the whole module
import struct Foundation.URL  // import a specific type (rarely used)
```

In Rust, the fine-grained `use` style is the norm. You explicitly name what you need, which makes dependencies within a file clear at a glance.

## Re-exports

Sometimes you want to expose an item from a submodule as if it were part of the parent module's API. Rust allows this with `pub use`:

```rust
// src/lib.rs
mod models;
mod services;

// Re-export User so consumers can write `my_crate::User` instead of `my_crate::models::User`
pub use models::User;
```

This is a powerful tool for API design. You can organize your internal code however you like and then curate a clean, flat public API through re-exports. The pattern is similar to Swift's `@_exported import`, but `pub use` is stable and idiomatic.

Re-exports are also how the standard library presents a clean API. Types like `Vec`, `String`, and `Option` are defined in nested modules but re-exported into the prelude or top-level namespace so you never need to write their full paths.

## Mapping the module tree to the filesystem

Here is a complete example that ties everything together. Given this file structure:

```
src/
  lib.rs
  config.rs
  network.rs
  network/
    http.rs
    websocket.rs
```

The module tree is declared as follows:

```rust
// src/lib.rs
pub mod config;
pub mod network;

pub use config::AppConfig;
```

```rust
// src/config.rs
pub struct AppConfig {
    pub api_url: String,
    pub timeout_secs: u64,
}

impl AppConfig {
    pub fn default_config() -> Self {
        Self {
            api_url: String::from("https://api.example.com"),
            timeout_secs: 30,
        }
    }
}
```

```rust
// src/network.rs
pub mod http;
pub mod websocket;

pub use http::get;
```

```rust
// src/network/http.rs
pub fn get(url: &str) -> String {
    format!("GET {url}")
}
```

```rust
// src/network/websocket.rs
pub fn connect(url: &str) -> String {
    format!("WS {url}")
}
```

A consumer of this crate can now write:

```rust
use my_crate::AppConfig;           // re-exported from config
use my_crate::network::get;        // re-exported from network::http
use my_crate::network::websocket;  // the module itself
```

## Key differences and gotchas

**Files are not automatically included**: this bears repeating because it is the single most common source of confusion. If you create a new `.rs` file, you must add a corresponding `mod` declaration somewhere in the module tree, or the compiler will not see it. There will be no error – the file will simply be ignored.

**Private is stricter than Swift's default**: Rust's default (no modifier) is closer to Swift's `private` than to `internal`. If you want the equivalent of Swift's `internal`, you need `pub(crate)`. This is a deliberate design choice: Rust encourages you to expose the minimum necessary API at every level of the module hierarchy.

**Struct field visibility is separate from struct visibility**: even if a struct is `pub`, its fields are private by default. You must mark each field as `pub` individually:

```rust
pub struct User {
    pub name: String,    // accessible from outside the module
    email: String,       // private to the module
}
```

In Swift, stored properties have their own access levels too; making a struct `public` does not automatically make all of its properties `public`. In Rust, you always opt in to field visibility explicitly with `pub`.

**Module names use snake_case**: Rust convention is `mod network_client`, not `mod NetworkClient`. Files follow the same convention: `network_client.rs`, not `NetworkClient.swift`. This is purely cosmetic but worth noting to avoid confusion.

**Circular crate dependencies are not allowed**: if crate A depends on crate B and crate B depends on crate A, Cargo will reject the dependency graph. Within a single crate, however, modules can freely reference each other. Swift allows circular references between files within the same module because all files are compiled together – Rust allows the same between modules within a crate, but not between separate crates.

## Further reading

- [Rust modules](https://doc.rust-lang.org/book/ch07-00-managing-growing-projects-with-packages-crates-and-modules.html): the official book's coverage of packages, crates, and modules
- [Rust Reference: Visibility](https://doc.rust-lang.org/reference/visibility-and-privacy.html): formal rules for visibility and privacy
- [API Guidelines: Re-exports](https://rust-lang.github.io/api-guidelines/necessities.html): conventions for organizing public APIs
- [Path clarity RFC](https://rust-lang.github.io/rfcs/2126-path-clarity.html): the RFC that introduced the 2018 edition's module path improvements
