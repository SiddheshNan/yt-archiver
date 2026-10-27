import { defineConfig } from 'vitepress'

// Set SITE_URL to where the site is published, e.g. https://example.com/yt-archiver/
const siteUrl = process.env.SITE_URL ? new URL(process.env.SITE_URL) : null
const base = siteUrl ? siteUrl.pathname.replace(/\/?$/, '/') : '/'

export default defineConfig({
  title: 'YT Archiver',
  description: 'Your own YouTube archive. Save videos and whole channels to your server and watch them from a web UI.',
  base,
  cleanUrls: true,
  lastUpdated: true,
  ignoreDeadLinks: 'localhostLinks',
  sitemap: siteUrl ? { hostname: siteUrl.origin + base } : undefined,
  head: [['link', { rel: 'icon', type: 'image/svg+xml', href: `${base}logo.svg` }]],

  themeConfig: {
    logo: '/logo.svg',

    nav: [
      { text: 'Docs', link: '/docs/', activeMatch: '^/docs/(?!reference/)' },
      { text: 'Reference', link: '/docs/reference/configuration', activeMatch: '^/docs/reference/' },
      { text: 'Changelog', link: '/changelog' },
    ],

    sidebar: {
      '/docs/': [
        {
          text: 'Getting started',
          items: [
            { text: 'What is YT Archiver?', link: '/docs/' },
            { text: 'Installation', link: '/docs/installation' },
          ],
        },
        {
          text: 'Using it',
          items: [
            { text: 'Archiving', link: '/docs/archiving' },
            { text: 'Chrome extension', link: '/docs/extension' },
            { text: 'Cookies and 1080p', link: '/docs/cookies' },
            { text: 'Security', link: '/docs/security' },
            { text: 'Upgrading', link: '/docs/upgrading' },
          ],
        },
        {
          text: 'Reference',
          items: [
            { text: 'Configuration file', link: '/docs/reference/configuration' },
            { text: 'Runtime folder', link: '/docs/reference/runtime-folder' },
            { text: 'API', link: '/docs/reference/api' },
          ],
        },
      ],
    },

    search: { provider: 'local' },
    outline: [2, 3],

    editLink: {
      pattern: 'https://github.com/SiddheshNan/yt-archiver/edit/main/website/:path',
      text: 'Edit this page on GitHub',
    },

    socialLinks: [{ icon: 'github', link: 'https://github.com/SiddheshNan/yt-archiver' }],

    footer: {
      message: 'Released under the MIT license.',
    },
  },
})
