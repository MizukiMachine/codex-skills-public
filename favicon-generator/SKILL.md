---
name: favicon-generator
description: "洗練されたfavicon、アプリアイコン、ブラウザタブアイコン、サイトアイコン、PWAアイコン一式を生成する。新規favicon、差し替え用favicon、フレームワークのアイコンmetadata、既存プロジェクトのfaviconアイデンティティレビューが必要なときに使う。Python CLI、ブラウザプレビュー、レイヤー効果ガイド、テンプレート、Lucideアイコン、文字モノグラム、絵文字モードを含む。"
metadata:
  short-description: "favicon一式を生成"
---

# Favicon Generator

## What It Does

Creates production-ready favicon suites that match an app's existing brand identity. It can generate PNG, ICO, and SVG assets, preview icons at real browser sizes, and update framework metadata such as Next.js `metadata.icons` or standard HTML `<link>` tags.

## Reference Files

| Topic | File | Use When |
|-------|------|----------|
| Rendering effects | [references/effects-guide.md](references/effects-guide.md) | You need implementation details for shadows, glow, highlight, noise, scaling, or color handling |
| Python generator | [scripts/generate_favicon.py](scripts/generate_favicon.py) | You need deterministic files in a project directory or CI-friendly generation |
| Browser studio | [scripts/generate_favicon.html](scripts/generate_favicon.html) | You need quick visual exploration, manual tuning, or side-by-side previews |

## Operating Model

Favicons are small brand artifacts, not decorations. The priority order is:

1. Match the project's real brand mark, icon library, and colors.
2. Stay readable at 16px and 32px.
3. Add polish through subtle layered effects.
4. Produce the complete asset set and wire it into the app.

Use the same logo/icon the app already uses when it exists. If there is no brand icon, choose a simple letter, Lucide icon, or emoji that maps to the product's function and audience.

## Discovery First

Before generating, inspect the target project:

```bash
rg "from.*lucide-react|from.*@lucide" --type ts --type tsx
rg "Logo|Header|Nav|Brand|Icon" --type ts --type tsx
rg "favicon|apple-touch-icon|manifest|metadata" .
rg "primary|brand|--.*color|themeColor" .
```

Extract:

- Existing logo or brand icon
- Current favicon files and where public assets live
- Brand colors from CSS variables, Tailwind config, theme files, or design tokens
- Framework entry point for icon metadata

Do not invent a generic icon when the codebase already has a recognizable brand mark.

## Generation Options

Use the CLI for final project assets:

```bash
python3 /home/mizuki2/.codex/skills/favicon-generator/scripts/generate_favicon.py \
  --letter A --style modern --output ./public

python3 /home/mizuki2/.codex/skills/favicon-generator/scripts/generate_favicon.py \
  --lucide rocket --style vibrant --output ./public

python3 /home/mizuki2/.codex/skills/favicon-generator/scripts/generate_favicon.py \
  --letter N --bg "#0f172a" --bg2 "#1e293b" --fg "#22d3ee" \
  --shadow 0.5 --highlight 0.3 --glow 0.2 --noise 0.04 \
  --radius 0.22 --output ./public
```

Dependencies:

```bash
python3 -m pip install Pillow
# Lucide rendering also needs:
python3 -m pip install cairosvg
```

If the local Python has no `pip` or you want an isolated one-off run, use `uv`:

```bash
uv run --with Pillow --with cairosvg python \
  /home/mizuki2/.codex/skills/favicon-generator/scripts/generate_favicon.py \
  --lucide rocket --style vibrant --output ./public
```

Use the browser studio when visual iteration matters:

```bash
xdg-open /home/mizuki2/.codex/skills/favicon-generator/scripts/generate_favicon.html
```

## Templates

| Template | Character | Good For |
|----------|-----------|----------|
| `modern` | clean indigo/purple | SaaS and productivity |
| `vibrant` | energetic pink/orange | consumer and social apps |
| `minimal` | dark and restrained | developer tools and utilities |
| `glass` | blue/cyan with shine | dashboards and analytics |
| `neon` | dark with cyan glow | games and creative tools |
| `warm` | amber/red | food, lifestyle, community |
| `forest` | green/teal | health, environment, finance |
| `mono` | black/white | neutral or adaptable brands |

Built-in Lucide icons:

`package-plus`, `rocket`, `zap`, `star`, `heart`, `code`, `box`, `compass`, `flame`, `globe`, `layers`, `music`, `send`, `shield`, `sparkles`, `sun`, `target`, `terminal`, `wand`

If the project uses a Lucide icon that is not built in, read its definition from `node_modules/lucide-react/dist/esm/icons/<icon-name>.js`, extract the SVG path elements, and add a local one-off entry to the generator or create a small project-specific script.

## Output Contract

The CLI writes:

```text
output/
├── favicon.ico
├── favicon.svg
├── favicon-16x16.png
├── favicon-32x32.png
├── favicon-48x48.png
├── favicon-64x64.png
├── favicon-128x128.png
├── apple-touch-icon.png
├── favicon-192x192.png
└── favicon-512x512.png
```

Place these in the app's public/static asset directory unless the framework requires a different location.

## Integration

Next.js App Router:

```typescript
// app/layout.tsx
export const metadata = {
  icons: {
    icon: [
      { url: "/favicon.ico", sizes: "any" },
      { url: "/favicon.svg", type: "image/svg+xml" },
      { url: "/favicon-16x16.png", sizes: "16x16", type: "image/png" },
      { url: "/favicon-32x32.png", sizes: "32x32", type: "image/png" },
    ],
    apple: [{ url: "/apple-touch-icon.png", sizes: "180x180" }],
  },
};
```

HTML:

```html
<link rel="icon" href="/favicon.ico" sizes="any">
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<link rel="icon" type="image/png" sizes="32x32" href="/favicon-32x32.png">
<link rel="icon" type="image/png" sizes="16x16" href="/favicon-16x16.png">
<link rel="apple-touch-icon" sizes="180x180" href="/apple-touch-icon.png">
```

PWA manifest:

```json
{
  "icons": [
    { "src": "/favicon-192x192.png", "sizes": "192x192", "type": "image/png" },
    { "src": "/favicon-512x512.png", "sizes": "512x512", "type": "image/png" }
  ]
}
```

## Quality Check

Before finishing:

- Inspect `favicon-16x16.png` and `favicon-32x32.png`; simplify if the mark blurs together.
- Confirm generated files are in the framework's served asset directory.
- Confirm metadata or link tags point to the generated paths.
- Prefer brand colors over default template colors when the project exposes brand tokens.
- Keep noise and glow subtle; they should add polish, not visual clutter.

## Avoid

- Replacing a real brand icon with a generic monogram without a reason.
- Generating only a 512px icon and skipping browser-tab sizes.
- Assuming a large-preview icon will work at 16px.
- Using arbitrary blue/purple gradients when the project has defined colors.
- Updating unrelated branding or layout files while integrating favicons.
