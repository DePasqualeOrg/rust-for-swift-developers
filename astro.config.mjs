import { defineConfig } from 'astro/config';
import starlight from '@astrojs/starlight';
import starlightThemeNova from 'starlight-theme-nova';

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

export default defineConfig({
  // Override these for a custom domain or non-standard Pages URL.
  site: process.env.SITE_URL ?? (githubOwner ? `https://${githubOwner}.github.io` : 'http://localhost:4321'),
  base:
    process.env.BASE_PATH ??
    (githubRepository && !isUserPagesRepository ? `/${githubRepository}` : '/'),
  integrations: [
    starlight({
      title: 'Rust for Swift Developers',
      disable404Route: true,
      customCss: ['./src/styles/starlight.css'],
      plugins: [starlightThemeNova()],
      social: [{ icon: 'github', label: 'GitHub', href: repositoryUrl }],
      sidebar: [
        {
          label: 'Introduction',
          link: '/',
        },
        {
          label: 'Getting Started',
          autogenerate: { directory: 'getting-started' },
        },
        {
          label: 'Language Fundamentals',
          autogenerate: { directory: 'language-fundamentals' },
        },
        {
          label: 'The Ownership System',
          autogenerate: { directory: 'ownership-system' },
        },
        {
          label: 'Abstraction and Composition',
          autogenerate: { directory: 'abstraction-and-composition' },
        },
        {
          label: 'Error Handling',
          autogenerate: { directory: 'error-handling' },
        },
        {
          label: 'Memory and Smart Pointers',
          autogenerate: { directory: 'memory-and-smart-pointers' },
        },
        {
          label: 'Concurrency',
          autogenerate: { directory: 'concurrency' },
        },
        {
          label: 'The Rust Ecosystem',
          autogenerate: { directory: 'rust-ecosystem' },
        },
        {
          label: 'Interop and FFI',
          autogenerate: { directory: 'interop-and-ffi' },
        },
        {
          label: 'Rust and WebAssembly',
          autogenerate: { directory: 'rust-and-webassembly' },
        },
        {
          label: 'Appendices',
          autogenerate: { directory: 'appendices' },
        },
      ],
    }),
  ],
});
