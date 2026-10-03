# Project Agent Rules

- Never run `npm`, `pnpm` or `node` on the host for this repository. Dependency installation, builds, previews and anything else that would run package code go through the dev container.
- Run them with `scripts/dx`, for example `scripts/dx pnpm build`, or `scripts/dx serve pnpm dev` for the dev server, which `scripts/dx stop` stops. The VS Code devcontainer workflow uses the same container.
- Check visual changes with `scripts/screenshots [out-dir] [viewport...]` after `scripts/dx pnpm build`. It renders the built site in WebKit at phone, iPad and desktop sizes in both color schemes, writes PNGs to `.screenshots/` by default, and checks the sidebar toggle, the menus and that page navigation runs a view transition.
- Astro caches rendered Markdown in `.astro/` and `node_modules/.astro/`, including the link to Expressive Code's stylesheet. After changing `expressiveCode` options, delete both caches (`rm -rf .astro` and `scripts/dx rm -rf node_modules/.astro`) before building, or pages link a stylesheet that no longer exists.
