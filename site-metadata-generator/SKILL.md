---
name: site-metadata-generator
description: Generate, audit, and implement site metadata for web projects, including SEO meta tags, Open Graph and Twitter cards, canonical URLs, robots.txt, sitemaps, and Schema.org JSON-LD. Use when Codex is asked to improve SEO, add metadata, create social sharing previews, generate sitemap.xml, add structured data, audit crawlability, or implement metadata in Next.js, Astro, Gatsby, React, Vue/Nuxt, or static HTML sites.
---

# Site Metadata Generator

## Purpose

Use this skill to make a web project understandable to search engines, social platforms, and AI crawlers. Produce framework-native metadata, structured data, crawlability files, and a concise audit trail rather than generic SEO copy.

## Operating Model

Treat metadata as semantic communication. The correct output describes what the page actually is, who it serves, and how machines should classify it.

Prioritize:

1. Accurate page meaning and user intent
2. Crawlability, canonical URLs, robots.txt, and sitemap coverage
3. Framework-native metadata APIs and existing project conventions
4. Unique titles, descriptions, and social tags per important page
5. JSON-LD only for content that is genuinely present on the page
6. Performance and mobile issues that affect discoverability

Before implementing, establish:

- Framework, router, build tool, and metadata conventions already present
- Site name, canonical domain, locale, default social image, and brand voice
- Page types: home, product, service, article, documentation, FAQ, contact, legal, or app-only
- Whether the request is an audit, implementation, sitemap generation, structured-data work, or all of them
- Which checks can be run locally without credentials or production access

## Contracts

- Do not invent production domains, ratings, prices, review counts, author names, publish dates, addresses, phone numbers, or social handles. Ask or leave a clearly named project-local placeholder when those facts are required.
- Canonical URLs, `og:url`, sitemap URLs, and robots sitemap links must use the same production origin and trailing-slash policy.
- Sitemaps must include only canonical URLs intended for indexing. Exclude admin, API, auth, search result, redirect, draft, duplicate, and `noindex` pages.
- JSON-LD must be valid JSON, injected in a way the framework renders correctly, and limited to content visible or verifiable on the page.
- Metadata ownership should be singular. Avoid competing title, canonical, Open Graph, or JSON-LD definitions across layout, route, component, and CMS layers.
- Social image URLs should resolve in production. Use absolute URLs unless the framework reliably expands relative assets from a configured metadata base.

Ask one concise question before editing when the canonical production domain, target locale, or required business facts cannot be discovered and would materially change generated URLs or structured data. Otherwise proceed with a conservative implementation and document assumptions.

## Capabilities and Deliverables

Use this skill to:

- Audit current metadata, crawlability, sitemap, robots, social tags, and JSON-LD coverage
- Implement missing metadata through the project's native framework pattern
- Generate or update `robots.txt`, framework robots routes, `sitemap.xml`, or framework sitemap routes
- Add page-appropriate Schema.org JSON-LD without fabricating content
- Produce a focused findings summary with blocking issues, quick wins, changed files, and verification results

Expected deliverables may include:

- Edited route, layout, SEO helper, content/frontmatter, config, public asset, robots, or sitemap files
- A page-type map showing which metadata pattern applies where
- A short audit report when the user asks for review rather than implementation
- Local validation output and a clear note for checks that require deployed URLs or external accounts

## Reference Files

Load only the reference needed for the current task.

| Topic | File | Use When |
|-------|------|----------|
| Audit checklist | [analysis-checklist.md](references/analysis-checklist.md) | Reviewing current SEO, crawlability, social tags, schema, performance, or mobile basics |
| Framework patterns | [framework-implementations.md](references/framework-implementations.md) | Implementing metadata in Next.js, Astro, Gatsby, React, Vue/Nuxt, or static HTML |
| Complete tag reference | [meta-tags-complete.md](references/meta-tags-complete.md) | Choosing exact meta, Open Graph, Twitter, canonical, robots, or verification tags |
| Structured data | [structured-data-schemas.md](references/structured-data-schemas.md) | Adding Organization, WebSite, Article, Product, FAQPage, BreadcrumbList, LocalBusiness, Event, or HowTo JSON-LD |

## Workflow

1. Discover the project shape.

   ```bash
   rg --files | rg '(^|/)(package\.json|next\.config\.(js|mjs|ts)|astro\.config\.(mjs|ts)|gatsby-config\.(js|ts)|nuxt\.config\.(js|ts)|vite\.config\.(js|ts)|index\.html|robots\.txt|sitemap\.xml|src/|app/|pages/|public/|static/)'
   rg -n "metadata|generateMetadata|<Head|next/head|react-helmet|Helmet|useHead|<title>|meta name=|property=\"og:|twitter:|application/ld\\+json|canonical|robots" .
   ```

   Narrow searches to the target route or page folder when output is large.

2. Run the bundled analyzer when useful.

   ```bash
   python3 <skill-dir>/scripts/analyze_seo.py <project-path>
   ```

   Replace `<skill-dir>` with the directory containing this `SKILL.md`. Use the output as a starting point, not as a complete judgment. It detects common files and tags, but cannot understand all dynamic metadata or content strategy.

3. Identify page types and metadata ownership.

   Decide whether metadata belongs in a root layout, route-level file, page component, content collection, CMS data, or shared helper. Reuse existing helpers and naming conventions before adding a new abstraction.

4. Define the metadata contract for the site.

   Lock the canonical origin, trailing slash policy, default locale, site name, default social image, noindex rules, and source of page facts. If any of these are unknown and necessary for the requested output, ask before writing production URLs.

5. Write metadata from page truth.

   Titles should be unique and usually 50-60 characters. Descriptions should be unique, accurate, and usually 150-160 characters. Social metadata may be more click-oriented but must still match the content.

6. Add structured data only when supported by visible content.

   Prefer JSON-LD with `@context: "https://schema.org"`. Use `@graph` when a page needs multiple connected schemas. Do not add Product, Review, FAQ, Event, or LocalBusiness properties that the page does not actually expose.

7. Add crawlability files if missing.

   Create or update `robots.txt`, framework-native robots routes, static `sitemap.xml`, or framework-native sitemap routes. Include only indexable canonical URLs in sitemaps.

8. Verify locally.

   Run the narrowest available project checks, inspect rendered HTML when possible, and validate generated XML/JSON. Use external validators only when the user asks or the local environment already has access.

## Implementation Guidance

### Metadata Essentials

Every indexable page should have:

```html
<title>Page Title | Site Name</title>
<meta name="description" content="Accurate page-specific summary.">
<link rel="canonical" href="https://example.com/page">
<meta property="og:type" content="website">
<meta property="og:url" content="https://example.com/page">
<meta property="og:title" content="Page Title">
<meta property="og:description" content="Accurate page-specific summary.">
<meta property="og:image" content="https://example.com/og-image.png">
<meta name="twitter:card" content="summary_large_image">
```

Adapt this to the framework's metadata API instead of hand-editing tags when the framework provides one.

### Page Type Decisions

| Page Type | Metadata Priority | Structured Data |
|-----------|-------------------|-----------------|
| Home or landing | Brand, category, primary value, default social image | Organization, WebSite, BreadcrumbList if relevant |
| Product or commerce | Product name, category, price/availability if present | Product, Offer, AggregateRating only when visible and true |
| Article or blog | Article title, author, publish/update dates, image | Article or BlogPosting, BreadcrumbList |
| Documentation | Precise task or concept, version if relevant | TechArticle, HowTo, FAQPage only for actual Q/A or steps |
| FAQ | Question-oriented title and summary | FAQPage |
| Local business | Service, city/region, contact intent | LocalBusiness with real address/hours/contact |
| Legal or account-only | Basic metadata, often noindex | Usually none |

### Sitemaps

Use the generator for static projects or as a route discovery aid:

```bash
python3 <skill-dir>/scripts/generate_sitemap.py <project-path> --domain https://example.com --output <project-path>/public/sitemap.xml
```

Replace `<skill-dir>` with the directory containing this `SKILL.md`. Prefer framework-native sitemap routes for Next.js App Router, Astro integrations, Gatsby plugins, or Nuxt modules when the project already uses them. Exclude admin, API, auth, search-result, duplicate, noindex, redirect, and unpublished pages.

### Robots.txt

For a public site, start from a permissive default and block only known private or non-indexable areas:

```txt
User-agent: *
Allow: /

Disallow: /admin/
Disallow: /api/
Disallow: /private/

Sitemap: https://example.com/sitemap.xml
```

Check staging and preview deployments carefully. A production `Disallow: /` is a blocking issue; an unblocked staging site may also be a blocking issue.

## Audit Mode

When the user asks for a review or audit, lead with findings rather than implementation notes. Order issues by severity:

1. Blocking: deindexing risks, broken canonical host, invalid JSON-LD, sitemap full of noncanonical URLs, missing metadata on critical pages
2. Major: duplicated titles/descriptions, absent social metadata on shareable pages, missing structured data for key page types, mobile or performance issues affecting crawl/render
3. Minor: wording refinements, optional verification tags, lower-priority schema opportunities, metadata consistency cleanup

For each finding, include the affected file or route, why it matters, and the concrete fix. Keep general SEO advice out of the report unless it maps to an observed issue.

## Anti-Patterns

**Keyword stuffing**

Why bad: Repetition creates spammy snippets and misrepresents page value.

Better: Write a specific title and description that match the actual page and search intent.

**One description everywhere**

Why bad: Search engines may ignore duplicated descriptions and users cannot distinguish pages.

Better: Generate page-specific descriptions for important routes and use a sensible default only for low-priority pages.

**Schema for invisible content**

Why bad: Structured data that claims reviews, FAQs, prices, events, or locations not shown on the page can violate search guidelines.

Better: Add schema only for information a user can see or reasonably verify on the page.

**Framework bypass**

Why bad: Manual `<head>` tags can be deduplicated, overridden, or missed by server rendering.

Better: Use the project's metadata API, layout conventions, head component, or plugin system.

**Sitemap as route dump**

Why bad: Including noncanonical, private, duplicate, or noindex URLs wastes crawl budget and sends contradictory signals.

Better: Include only canonical URLs intended for indexing.

## Variation Guidance

Vary by:

- Framework: Next.js metadata API, Astro layout props, Gatsby Head exports, React Helmet, Vue/Nuxt head helpers, or static HTML
- Industry: ecommerce, SaaS, local services, documentation, editorial, portfolio, event, or app shell
- Locale and domain: canonical host, hreflang, region, and translated metadata
- Page importance: comprehensive metadata for key pages, lightweight defaults for low-value pages
- Content source: hardcoded pages, markdown/frontmatter, CMS records, database routes, or generated docs

Avoid converging on:

- The same title format for every page type
- Generic descriptions such as "Welcome to our website"
- Social images with missing dimensions or relative-only production URLs
- JSON-LD copied from examples without matching the site
- Adding broad SEO dependencies when a small native change is enough

## Verification

Use the checks that fit the project:

```bash
python3 <skill-dir>/scripts/analyze_seo.py .
python3 -m py_compile <skill-dir>/scripts/*.py
```

Also verify:

- Project lint, typecheck, tests, or build pass when available
- Rendered HTML contains one title, one canonical URL, expected description, social tags, and valid JSON-LD
- `robots.txt` and `sitemap.xml` are reachable in the app's public output or framework route
- Sitemap XML parses and contains canonical URLs only
- JSON-LD parses with no trailing comments or framework escaping issues
- Open Graph image URL is absolute in production contexts and resolves to a real image

Report any checks that require production credentials, deployed URLs, Search Console, or external validators and were not run.
