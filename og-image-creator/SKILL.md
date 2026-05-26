---
name: og-image-creator
description: "Webプロジェクト向けに、ブランドに合ったOpen Graph画像とSNSプレビュー画像を生成、レビュー、統合する。OG画像、SNSカード、`og:image` や `twitter:image` metadataの追加、ソーシャル共有画像の監査、Next.js/Astro/React/Gatsby/static HTML/blog/docs/product/landing page向けのルート対応OG画像パイプライン作成を求められたときに使う。"
---

# OG Image Creator

## Purpose

Create Open Graph images that feel native to the site being shared. Inspect the codebase first, extract routes and brand signals, generate reviewable 1200x630 assets, and integrate metadata in the framework's native style.

## Operating Model

An OG image is part of the page contract and brand system, not a standalone poster. Optimize for accurate previews, readability in small social cards, and repeatable regeneration.

Prioritize:
1. Correct route metadata, dimensions, URLs, and accessibility.
2. Authentic brand fit from existing colors, fonts, logos, components, and tone.
3. Thumbnail readability with strong hierarchy and safe padding.
4. A maintainable generation path instead of one-off manual images.

Before acting, establish:
- Framework and routing model: Next.js App Router, Pages Router, Astro, Gatsby, React SPA, static HTML, or custom.
- Current metadata owner: page exports, layout component, SEO component, HTML head, MD/MDX frontmatter, or CMS data.
- Brand sources: logo files, CSS variables, Tailwind/theme config, fonts, components, screenshots, and existing image style.
- Static vs dynamic need: fixed marketing pages, many content routes, user-generated routes, or per-slug article cards.
- Canonical site URL for absolute `og:image` and `twitter:image` values.

## Capabilities

- Analyze a web project and produce `og-analysis.json` with framework, routes, metadata, brand colors, fonts, and logos.
- Generate route-specific images in `public/og/` plus `manifest.json` and `preview.html` for review.
- Update framework-native metadata so pages expose correct Open Graph and Twitter card tags.
- Audit existing OG images for generic design, stale metadata, missing absolute URLs, poor contrast, bad dimensions, or over-large files.

## Reference Files

| Topic | File | Use When |
|-------|------|----------|
| OG specs and validation | [og-specifications.md](references/og-specifications.md) | Checking dimensions, metadata, URLs, image alt text, file size, and platform preview behavior |
| Design and content principles | [design-principles.md](references/design-principles.md) | Choosing layouts, typography, hierarchy, brand usage, and page-type variations |
| Framework workflows | [framework-workflows.md](references/framework-workflows.md) | Integrating metadata in Next.js, Astro, React SPA, Gatsby, or static HTML |

## Workflow

### 1. Discover Existing State

Use the analyzer as a first pass, then inspect the code manually where it reports gaps.

```bash
SKILL_ROOT="${CODEX_HOME:-$HOME/.codex}/skills/og-image-creator"
python3 "$SKILL_ROOT/scripts/analyze_codebase.py" /path/to/project
```

The script writes `/path/to/project/og-analysis.json`. Review it before generating images. If routes or brand signals are missing, inspect framework files directly with `rg`, then patch the JSON or improve the analyzer result before generation. Dynamic routes are marked with `dynamic: true`; generate concrete per-slug entries from real data instead of treating `[slug]`, `:id`, or `*` routes as final static pages.

Discovery targets:
- `package.json`, framework config, route folders, route config, SEO components, layout components, and MD/MDX frontmatter.
- Existing `<Head>`, `metadata`, `generateMetadata`, `Helmet`, or HTML `<meta>` ownership.
- `public/`, `src/assets/`, CSS files, Tailwind config, theme tokens, favicon/app icons, and logo assets.
- Existing generated images and any social preview references.

### 2. Choose The Strategy

Use static generated images for stable routes and brand-critical pages. Use dynamic framework image generation only when route count or user-generated content makes static assets impractical.

Choose page-type-specific treatments:
- Landing: brand-forward, large value statement, minimal supporting copy.
- Article/blog: category/date when available, title, excerpt, publisher mark.
- Product/feature: product name, core benefit, actual visual or UI cue when available.
- Documentation: topic label, structured feel, high clarity, restrained accents.
- About/company: logo and identity-forward, professional and direct.

### 3. Generate Reviewable Images

Install the rendering dependency in the target environment if it is missing:

```bash
python3 -m pip install playwright
python3 -m playwright install chromium
```

```bash
SKILL_ROOT="${CODEX_HOME:-$HOME/.codex}/skills/og-image-creator"
python3 "$SKILL_ROOT/scripts/generate_og_images.py" /path/to/project
```

Expected outputs:
- `public/og/<route>.png`
- `public/og/manifest.json`
- `public/og/preview.html`

Open or screenshot `preview.html` when visual quality matters. Regenerate after editing `og-analysis.json`, routes, metadata, assets, or the generator.

The generator skips dynamic parameterized routes by default. Use `--include-dynamic` only when intentionally producing a fallback image for a route pattern.

### 4. Integrate Metadata

Read [framework-workflows.md](references/framework-workflows.md) for the detected framework. Prefer the existing metadata abstraction if the project already has one. If no abstraction exists and several pages need metadata, create a small shared SEO helper rather than duplicating long tag blocks.

Use absolute URLs for deployed social tags when the framework does not resolve them automatically. Include `og:image:width`, `og:image:height`, and `og:image:alt` when possible.

### 5. Verify

Run checks matched to the failure modes:
- Image dimensions are 1200x630.
- Text fits the safe area and remains readable at small preview sizes.
- File sizes are reasonable; prefer under 200 KB when practical.
- Metadata points to reachable absolute image URLs in deployed HTML.
- Social preview tools show the intended image after cache refresh.
- No unrelated user changes were overwritten while integrating metadata.

## Command Patterns

Analyze a project and write a custom analysis path:

```bash
SKILL_ROOT="${CODEX_HOME:-$HOME/.codex}/skills/og-image-creator"
python3 "$SKILL_ROOT/scripts/analyze_codebase.py" . --output ./tmp/og-analysis.json
```

Generate from a reviewed analysis file:

```bash
SKILL_ROOT="${CODEX_HOME:-$HOME/.codex}/skills/og-image-creator"
python3 "$SKILL_ROOT/scripts/generate_og_images.py" . --analysis ./tmp/og-analysis.json --out-dir ./public/og
```

Generate only a few routes while iterating:

```bash
SKILL_ROOT="${CODEX_HOME:-$HOME/.codex}/skills/og-image-creator"
python3 "$SKILL_ROOT/scripts/generate_og_images.py" . --limit 3
```

Generate fallback images for dynamic route patterns only when that is the intended result:

```bash
SKILL_ROOT="${CODEX_HOME:-$HOME/.codex}/skills/og-image-creator"
python3 "$SKILL_ROOT/scripts/generate_og_images.py" . --include-dynamic
```

## Anti-Patterns

**Generating before discovery**

Why bad: The result usually misses routes, uses the wrong metadata owner, and looks detached from the product.

Better: Run analysis, inspect route and brand sources, then generate.

**One layout for every route**

Why bad: Landing pages, docs, articles, and products communicate different jobs.

Better: Vary layout, hierarchy, labels, and visual emphasis by page type.

**Generic gradient plus title**

Why bad: It could belong to any site and weakens brand recognition.

Better: Use actual brand tokens, logo assets, component shapes, spacing, and typography patterns.

**Relative social image URLs in final metadata**

Why bad: Some crawlers require absolute public URLs and cannot resolve local paths.

Better: Resolve images through the site's canonical origin or framework metadata base.

**Overcrowded cards**

Why bad: Social previews are often rendered as thumbnails.

Better: Use one dominant idea, short supporting copy, large type, and safe padding.

## Variation Guidance

Vary based on:
- Page type, content density, audience, and share context.
- Brand maturity: established design systems should reuse exact tokens; young projects may need a restrained generated style aligned with current UI.
- Asset availability: use real product or UI visuals when they help; avoid decorative placeholders.
- Scale: a few static routes can be hand-reviewed; hundreds of routes need templating and dynamic generation.

Avoid converging on:
- Identical title/logo placement for every page.
- A single dominant hue if the site itself has a richer palette.
- Long titles squeezed into tiny type.
- Metadata edits that ignore the project's established SEO pattern.
