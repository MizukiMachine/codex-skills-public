# OG Image Design Principles

## Design Goal

Create a trustworthy preview of the page. The image should make the shared link recognizable, legible, and specific to the content.

## Priority Order

1. Accurate title and page context.
2. Readability at feed thumbnail size.
3. Brand fit through real tokens and assets.
4. Visual variation that matches page purpose.
5. Decorative polish only after the first four are satisfied.

## Page Type Patterns

| Page Type | Primary Job | Recommended Treatment |
|-----------|-------------|-----------------------|
| Landing | Communicate brand and value quickly | Centered or bold left-aligned headline, logo, short support line |
| Article/blog | Sell the read | Category/date if useful, large title, excerpt, publisher mark |
| Product/feature | Show value | Split or asymmetrical layout, product name, benefit, real UI/product cue |
| Documentation | Signal clarity | Topic label, structured spacing, restrained accents, concise description |
| About/company | Build identity | Logo/name emphasis, tagline, clean professional hierarchy |
| General page | Identify destination | Title, short description, subtle brand accent |

## Brand Extraction

Prefer signals from the user's project over invented styling:

- CSS variables and theme tokens.
- Tailwind config or design-system config.
- Logo, favicon, app icon, and product mark files.
- Existing UI components, buttons, cards, nav, and hero sections.
- Actual screenshots or product media when available.

If the project lacks a mature brand, create a restrained style that matches the current UI rather than adding a loud standalone campaign look.

## Typography

- Keep the main title large and short.
- Reduce font size for long titles instead of allowing overflow.
- Use the site's font family when it can render reliably.
- Avoid more than two font families.
- Do not rely on all caps unless the brand already uses it.

## Color And Contrast

- Use brand colors as background, accent, or framing based on contrast.
- Avoid text in low-contrast brand colors.
- Avoid palettes that turn every card into the same gradient.
- If using a photo or screenshot, add a solid overlay or panel so text stays readable.

## Content Rules

- Use page metadata, frontmatter, H1 text, or route-specific CMS content.
- Rewrite only to fit the card while preserving meaning.
- Do not use lorem ipsum, generic route names, or placeholder page titles in final images.
- Include author/date/category only when it improves recognition or credibility.

## Review Checklist

- Title fits and is readable at small size.
- Visual hierarchy has one clear dominant message.
- Logo or brand mark is present but not overpowering.
- Layout matches the page type.
- The image looks connected to the actual website.
- No important content sits near the edges.
- The generated set has controlled variation, not random novelty.
