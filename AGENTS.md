# Project Agent Rules

- Never run `npm`, `pnpm` or `node` on the host for this repository. Dependency installation, builds, previews and anything else that would run package code go through the dev container.
- Run them with `scripts/dx`, for example `scripts/dx pnpm build`, or `scripts/dx serve pnpm dev` for the dev server, which `scripts/dx stop` stops. The VS Code devcontainer workflow uses the same container.
