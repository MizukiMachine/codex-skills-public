# Open Graph Specifications

## Core Contract

- Standard image size: 1200x630 px, 1.91:1.
- Minimum practical size: 600x314 px.
- Preferred format: PNG for text-heavy generated cards; JPEG for photo-heavy cards.
- Keep important content inside a safe area of roughly 80 px left/right and 60 px top/bottom.
- Prefer files under 200 KB when practical, while preserving text clarity.
- Serve final images from a public HTTPS URL.

## Essential Metadata

```html
<meta property="og:title" content="Page title">
<meta property="og:description" content="Page description">
<meta property="og:type" content="website">
<meta property="og:url" content="https://example.com/page">
<meta property="og:image" content="https://example.com/og/page.png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="Concise description of the preview image">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:image" content="https://example.com/og/page.png">
```

Use framework helpers when available, but verify the rendered HTML contains equivalent tags.

## Text And Layout

- Headline: usually 48-72 px, depending on title length.
- Supporting text: usually 24-34 px.
- Use high contrast. Text should remain readable in a small link preview.
- Keep headline to 2-3 visual lines when possible.
- Avoid small icons or long metadata strings that disappear at thumbnail size.

## Validation

Validate the deployed URL, not only local files:

- OpenGraph preview tools for cross-platform inspection.
- LinkedIn Post Inspector for LinkedIn cache and rendering.
- Facebook Sharing Debugger for Facebook cache and detected tags.
- X/Twitter card preview or a live post draft where available.
- Browser devtools or curl against deployed HTML to confirm head tags.

## Common Failures

**Image missing**

Likely causes: relative URL, non-public file, auth wall, wrong path, non-HTTPS deployment, cache.

First fixes: use an absolute deployed URL, verify a direct image request returns 200, refresh platform cache.

**Wrong image**

Likely cause: crawler cache.

First fixes: refresh the platform debugger, change image filename when cache busting is needed.

**Content cut off**

Likely cause: important content outside safe area or an aspect ratio mismatch.

First fixes: regenerate at 1200x630, move content inward, reduce text density.

**Preview looks generic**

Likely cause: generated template ignored brand tokens and page type.

First fixes: inspect real UI, reuse colors/fonts/logo/components, vary layout by route type.
