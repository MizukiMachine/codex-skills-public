# Framework Workflows

## Next.js App Router

Detect routes in `app/**/page.{ts,tsx,js,jsx}` or `src/app/**/page.{ts,tsx,js,jsx}`.

Use existing `metadata` or `generateMetadata` exports when present. Set `metadataBase` at the root layout when using relative image paths.

```tsx
export const metadata = {
  title: "Home",
  description: "Welcome to Example",
  openGraph: {
    title: "Home",
    description: "Welcome to Example",
    images: [
      {
        url: "/og/home.png",
        width: 1200,
        height: 630,
        alt: "Example homepage preview",
      },
    ],
  },
  twitter: {
    card: "summary_large_image",
    images: ["/og/home.png"],
  },
}
```

For dynamic content, prefer `generateMetadata` and either:

- Pre-generate static images for known slugs.
- Use `next/og` for large or user-generated route sets.

Do not integrate the analyzer's `[slug]` pattern image as if it were a finished per-page card. The generator skips parameterized routes by default; add concrete route records from CMS/build data or pass `--include-dynamic` only for deliberate fallback images.

## Next.js Pages Router

Detect routes in `pages/**/*.{ts,tsx,js,jsx}` or `src/pages/**/*.{ts,tsx,js,jsx}`. Ignore `_app`, `_document`, `_error`, and `api`.

Use the existing SEO component when available. If not, use `next/head` or introduce a shared helper for multiple pages.

```tsx
import Head from "next/head"

export function Seo({ title, description, path, image = "/og/home.png" }) {
  const siteUrl = "https://example.com"
  const imageUrl = new URL(image, siteUrl).toString()
  const pageUrl = new URL(path, siteUrl).toString()

  return (
    <Head>
      <title>{title}</title>
      <meta name="description" content={description} />
      <meta property="og:title" content={title} />
      <meta property="og:description" content={description} />
      <meta property="og:url" content={pageUrl} />
      <meta property="og:image" content={imageUrl} />
      <meta property="og:image:width" content="1200" />
      <meta property="og:image:height" content="630" />
      <meta name="twitter:card" content="summary_large_image" />
      <meta name="twitter:image" content={imageUrl} />
    </Head>
  )
}
```

## Astro

Detect routes in `src/pages/**/*.{astro,md,mdx}`.

Prefer a shared layout with `Astro.site` for absolute URLs.

```astro
---
const {
  title,
  description,
  ogImage = "/og/home.png",
} = Astro.props

const ogImageUrl = new URL(ogImage, Astro.site).toString()
---
<title>{title}</title>
<meta name="description" content={description} />
<meta property="og:title" content={title} />
<meta property="og:description" content={description} />
<meta property="og:image" content={ogImageUrl} />
<meta property="og:image:width" content="1200" />
<meta property="og:image:height" content="630" />
<meta name="twitter:card" content="summary_large_image" />
<meta name="twitter:image" content={ogImageUrl} />
```

For Markdown and MDX, store `title`, `description`, and `ogImage` in frontmatter when the layout consumes them.

## React SPA

React-only single page apps often do not provide route-specific metadata to social crawlers because many crawlers do not execute client JavaScript.

Preferred options:

- Add SSR/SSG if the project supports it.
- Pre-render important marketing routes.
- Use server middleware or hosting rewrites to serve crawler-visible metadata.
- Use a static default card only when per-route social previews are impossible.

If the app already uses `react-helmet-async`, update it for in-browser metadata too, but do not assume this solves crawler previews without SSR/prerendering.

## Gatsby

Detect file routes in `src/pages/**/*.{ts,tsx,js,jsx}` and inspect `gatsby-node.*` for programmatic routes.

Use the project's SEO component or `react-helmet`. For programmatic routes, generate images from source data and pass the image path through page context or GraphQL.

## Static HTML

Detect `*.html` files while ignoring build/cache directories.

Add tags directly to each `<head>` or through the site's template/build step. Avoid hand-editing generated `dist/` files when a source template exists.

```html
<meta property="og:title" content="Home">
<meta property="og:description" content="Welcome to Example">
<meta property="og:image" content="https://example.com/og/home.png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:image" content="https://example.com/og/home.png">
```

## Integration Review

Before finishing:

- Verify the rendered/deployed HTML contains the expected tags.
- Confirm the image URL is absolute or framework-resolved to an absolute URL.
- Confirm dynamic routes use route-specific titles and images where feasible.
- Keep metadata changes in source files, not generated build output.
