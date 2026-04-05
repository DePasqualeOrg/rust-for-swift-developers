# The published devcontainer-base image, pinned by digest so every host builds on the same base.
# Update the pin after devcontainer-base publishes a new image.
FROM ghcr.io/depasqualeorg/devcontainer-base:4663053@sha256:18d0bc78346523ea14ce8c093aa779413a0afc84f92179551e4c89a4909c2b31

# Pin the pnpm store to a project-local path so it lands on the dedicated named
# volume (see docker-compose.dev.yml) instead of $HOME or the host bind mount.
ENV npm_config_store_dir=/workspace/.pnpm-store

# Pre-create the store dir as the node user so the named volume mounted here inherits
# node ownership. An empty named volume would otherwise be root-owned, and pnpm (running
# as node) would fail with EACCES trying to write the store.
RUN mkdir -p /workspace/.pnpm-store

# Copy manifest + lockfile first so this layer stays cached unless deps change, then let
# Corepack (enabled in devcontainer-base) fetch the pnpm version package.json pins.
COPY --chown=node:node package.json pnpm-lock.yaml pnpm-workspace.yaml ./
RUN pnpm --version

# Install dependencies inside the image (never on the host).
RUN pnpm install --frozen-lockfile --ignore-scripts \
  && rm -rf /home/node/.local/share/pnpm/store

# Astro dev server
EXPOSE 4321

# Keep the container running
CMD ["tail", "-f", "/dev/null"]
