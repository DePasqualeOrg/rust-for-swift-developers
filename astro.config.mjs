import { defineConfig } from 'astro/config';
import starlight from '@astrojs/starlight';

const githubOwner =
  process.env.GITHUB_REPOSITORY_OWNER ?? process.env.GITHUB_REPOSITORY?.split('/')[0];
const githubRepository = process.env.GITHUB_REPOSITORY?.split('/')[1];
const repositoryUrl =
  githubOwner && githubRepository
    ? `https://github.com/${githubOwner}/${githubRepository}`
    : 'https://github.com/DePasqualeOrg/rust-for-swift-developers';
const isUserPagesRepository =
  githubOwner &&
  githubRepository &&
  githubRepository.toLowerCase() === `${githubOwner.toLowerCase()}.github.io`;
const basePath =
  process.env.BASE_PATH ??
  (githubRepository && !isUserPagesRepository ? `/${githubRepository}` : '/');

export default defineConfig({
  redirects: {
    '/rust-and-webassembly/evolving-wasm-landscape/': `${basePath.replace(/\/$/, '')}/appendices/wasm-status/`,
  },
  server: {
    // Bind to 0.0.0.0 so the dev server is reachable inside the dev container. Dev-only;
    // ignored by the production build.
    host: true,
  },
  vite: {
    server: {
      // No host port is published (see docker-compose.dev.yml); the dev server is reached
      // via OrbStack's container domain. Allow .orb.local so Vite doesn't reject the Host
      // header.
      allowedHosts: ['.orb.local'],
    },
  },
  // Override these for a custom domain or non-standard Pages URL.
  site: process.env.SITE_URL ?? (githubOwner ? `https://${githubOwner}.github.io` : 'http://localhost:4321'),
  base: basePath,
  integrations: [
    starlight({
      title: 'Rust for Swift Developers',
      disable404Route: true,
      customCss: ['./src/styles/starlight.css'],
      components: {
        MobileTableOfContents: './src/components/MobileTableOfContents.astro',
        Search: './src/components/Search.astro',
        Sidebar: './src/components/Sidebar.astro',
        SiteTitle: './src/components/SiteTitle.astro',
      },
      head: [
        {
          // Decide whether the docked sidebar starts hidden before the page renders, so the
          // layout never shifts. Touch screens never dock it: it slides over the content instead.
          // Otherwise the choice from the sidebar toggle wins, and narrow windows start without it.
          tag: 'script',
          content: `(() => {
            let stored = null;
            try { stored = localStorage.getItem('sidebar'); } catch {}
            const collapsed = matchMedia('(pointer: coarse)').matches
              || (stored ? stored === 'collapsed' : matchMedia('(max-width: 64rem)').matches);
            if (collapsed) document.documentElement.setAttribute('data-sidebar-collapsed', '');
          })();`,
        },
      ],
      expressiveCode: {
        themes: ['vitesse-dark', 'vitesse-light'],
        useStarlightUiThemeColors: true,
        styleOverrides: {
          borderRadius: '0.625rem',
          borderColor: 'var(--sl-color-hairline-light)',
          codeFontSize: '0.875rem',
          codeLineHeight: '1.65',
          codePaddingBlock: '0.875rem',
          codePaddingInline: '1.125rem',
          frames: {
            shadowColor: 'transparent',
            editorActiveTabIndicatorTopColor: 'var(--sl-color-accent)',
          },
        },
      },
      social: [{ icon: 'github', label: 'GitHub', href: repositoryUrl }],
      sidebar: [
        {
          label: 'Introduction',
          link: '/',
        },
        {
          label: 'Getting Started',
          items: [{ autogenerate: { directory: 'getting-started' } }],
        },
        {
          label: 'Language Fundamentals',
          items: [{ autogenerate: { directory: 'language-fundamentals' } }],
        },
        {
          label: 'The Ownership System',
          items: [{ autogenerate: { directory: 'ownership-system' } }],
        },
        {
          label: 'Abstraction and Composition',
          items: [{ autogenerate: { directory: 'abstraction-and-composition' } }],
        },
        {
          label: 'Error Handling',
          items: [{ autogenerate: { directory: 'error-handling' } }],
        },
        {
          label: 'Memory and Smart Pointers',
          items: [{ autogenerate: { directory: 'memory-and-smart-pointers' } }],
        },
        {
          label: 'Concurrency',
          items: [{ autogenerate: { directory: 'concurrency' } }],
        },
        {
          label: 'The Rust Ecosystem',
          items: [{ autogenerate: { directory: 'rust-ecosystem' } }],
        },
        {
          label: 'Interop and FFI',
          items: [{ autogenerate: { directory: 'interop-and-ffi' } }],
        },
        {
          label: 'Rust and WebAssembly',
          items: [{ autogenerate: { directory: 'rust-and-webassembly' } }],
        },
        {
          label: 'Appendices',
          items: [{ autogenerate: { directory: 'appendices' } }],
        },
      ],
    }),
  ],
});
