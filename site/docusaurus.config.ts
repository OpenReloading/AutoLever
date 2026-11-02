import { execFileSync } from 'node:child_process'
import { basename } from 'node:path'
import type { Options as DocsOptions } from '@docusaurus/plugin-content-docs'
import type { Options as ThemeOptions } from '@docusaurus/theme-classic'
import type { UserThemeConfig } from '@docusaurus/theme-common'
import type { Config } from '@docusaurus/types'
import { repoFacts } from './scripts/repo-facts.mts'
// title, description, address and repository: also read by tools/site_config.py (social card, browser check)
import site from './site.json'

// GitHub Pages: DOCS_URL is the site origin, DOCS_BASE_URL the path of the edition (pages.yml builds main under /AutoLever/next/)
const baseUrl = process.env.DOCS_BASE_URL ?? site.baseUrl
const repo = `https://github.com/${site.repo}`

const config = async (): Promise<Config> => ({
  title: site.title,
  tagline: site.description,
  url: process.env.DOCS_URL ?? site.url,
  baseUrl,
  favicon: 'assets/favicon.svg',
  trailingSlash: true,
  titleDelimiter: '-',
  onBrokenLinks: 'throw',
  onBrokenAnchors: 'throw',
  markdown: {
    hooks: { onBrokenMarkdownLinks: 'throw' },
    // every page's description (link preview, search engines) is the site's; Docusaurus would take the first
    // paragraph, which is the safety text. Partials (_*.mdx) take no front matter.
    parseFrontMatter: async (params) => {
      const result = await params.defaultParseFrontMatter(params)
      if (!basename(params.filePath).startsWith('_')) result.frontMatter.description ??= site.description
      return result
    },
  },
  // the search box of src/theme/SearchBar.tsx: it reads the index next to this script
  stylesheets: [`${baseUrl}pagefind/pagefind-component-ui.css`],
  scripts: [{ src: `${baseUrl}pagefind/pagefind-component-ui.js`, defer: true }],
  // the pieces of the classic preset the site uses, without its blog, pages, SVG-as-component and search plugins
  themes: [
    [
      '@docusaurus/theme-classic',
      // brand.css: tokens and their mapping, shared by the OpenReloading sites; autolever.css: this site's layout
      { customCss: ['./src/css/brand.css', './src/css/autolever.css'] } satisfies ThemeOptions,
    ],
  ],
  plugins: [
    // no sidebar: the pages are the navbar tabs, previous and next come from each page's front matter
    ['@docusaurus/plugin-content-docs', { routeBasePath: '/', sidebarPath: false } satisfies DocsOptions],
    '@docusaurus/plugin-sitemap',
    // data/buildguide.json is written by main.py (python main.py)
    ['@openreloading/docusaurus-plugin-buildguide', { data: '../data/buildguide.json' }],
    // the search index of the built site (scripts/search.mts), in its own process: the config loader cannot
    // require the ESM-only pagefind package
    ({ siteDir }) => ({
      name: 'search-index',
      postBuild: ({ outDir }) => {
        execFileSync(process.execPath, ['scripts/search.mts', outDir], { cwd: siteDir, stdio: 'inherit' })
      },
    }),
  ],
  themeConfig: {
    // link previews: og:image and twitter:image from `image`, the rest on every page (404 included); X reads
    // og:title and og:description where twitter:title and twitter:description are missing
    image: 'assets/social-card.png',
    metadata: [
      { name: 'description', content: site.description },
      { property: 'og:description', content: site.description },
      { property: 'og:type', content: 'website' },
      { property: 'og:site_name', content: site.title },
      { property: 'og:image:type', content: 'image/png' },
      { property: 'og:image:width', content: '1200' },
      { property: 'og:image:height', content: '630' },
      { property: 'og:image:alt', content: `${site.title}: ${site.description}` },
    ],
    navbar: {
      title: site.title,
      // black on the light navbar, white on the dark one; the title next to it names the site
      logo: { alt: '', src: 'assets/autolever.svg', srcDark: 'assets/autolever-white.svg' },
      items: [
        { type: 'doc', docId: 'index', label: 'Introduction', position: 'left' },
        { type: 'doc', docId: 'bom', label: 'BOM', position: 'left' },
        { type: 'doc', docId: 'wiring', label: 'Wiring', position: 'left' },
        { type: 'doc', docId: 'tubing', label: 'Tubing', position: 'left' },
        // read once per build, the browser makes no request to GitHub
        { type: 'custom-repo', repo: site.repo, facts: await repoFacts(site.repo), position: 'right' },
        { type: 'search', position: 'right' },
      ],
    },
    footer: {
      links: [
        { label: 'Repository', href: repo },
        { label: 'Discord', href: 'https://discord.gg/hUCSjDYNaa' },
        { label: 'MIT licence', href: `${repo}/blob/main/LICENSE` },
      ],
    },
    colorMode: { respectPrefersColorScheme: true },
    // code in the token colours: the commands on the pages have no language to highlight
    prism: { theme: { plain: { color: 'var(--ink)', backgroundColor: 'var(--surface-alt)' }, styles: [] } },
  } satisfies UserThemeConfig,
})

export default config
