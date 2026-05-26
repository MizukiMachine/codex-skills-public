---
name: og-image-ai
description: "OpenAI GPT ImageモデルによるAIイラストと、Pillowによる決定的なテキスト合成を組み合わせて、Open Graph画像やSNSプレビュー画像を生成する。創造的/テーマ性のあるOG画像、イラスト入りブログ/記事カード、製品/ランディングページのSNSカード、`og-analysis.json` からのバッチ生成、または決定的な `og-image-creator` パイプラインのAI生成版が必要なときに使う。"
metadata:
  short-description: "AIイラストのOG画像を生成"
---

# OG Image AI

## Purpose

Generate 1200x630 Open Graph images that combine AI-generated visual backgrounds with crisp, deterministic text overlays. Use this as the creative companion to `og-image-creator`, not as a replacement for route discovery, metadata integration, or preview verification.

## Operating Model

An AI OG image is still part of a page's metadata contract. The AI should supply theme, mood, and visual specificity; the script should own text, safe area, dimensions, filenames, manifests, and preview pages.

Prioritize:

1. Correct route metadata, public image paths, and framework-native integration.
2. Readable text at social-preview thumbnail sizes.
3. Brand and page-type fit based on the actual project.
4. Controlled cost and iteration with dry runs and small batches before full generation.

Before generating, establish:

- Framework, routing model, and current metadata owner.
- Canonical site URL and public/static asset directory.
- Brand colors, typography, logo usage, visual tone, and existing OG images.
- Stable routes versus dynamic route patterns that need concrete slug data.
- Whether AI imagery is desirable for this project, or whether deterministic `og-image-creator` cards better fit the brand.

## When To Use

| Scenario | Use og-image-ai | Use og-image-creator |
|----------|-----------------|----------------------|
| Illustrated or atmospheric social card background | Yes | No |
| Unique thematic visual per article or product page | Yes | Maybe |
| Strict design-system consistency at scale | No | Yes |
| No API spend or fully deterministic output required | No | Yes |
| Metadata audit or framework integration only | Maybe | Yes |
| First pass for a large route set | Only after a small calibration batch | Yes |

## Capabilities

- Reuse `og-analysis.json` from `og-image-creator` for route-aware batch generation.
- Generate GPT Image backgrounds with page-type and brand-color prompt guidance.
- Composite title, description, accent bar, and optional site name with Pillow.
- Skip dynamic route patterns by default so `[slug]` cards are not mistaken for final per-page images.
- Produce `manifest.json` and `preview.html` for visual review.

## Deliverables

- `public/og/*.png` or the project's equivalent public asset path.
- `public/og/manifest.json` with route, file, dimensions, and alt text records.
- `public/og/preview.html` for review at social-card proportions.
- Framework-native metadata updates when the user asks for integration.
- A short final summary of generated assets, metadata edits, and verification performed.

## Reference Files

| Topic | File | Use When |
|-------|------|----------|
| Prompt design | [references/prompt-design.md](references/prompt-design.md) | Choosing style presets, page-type hints, custom prompts, and anti-text instructions |
| Generator script | [scripts/generate_og_ai.py](scripts/generate_og_ai.py) | Generating single images, dry-run prompts, or batches from `og-analysis.json` |

For framework-specific metadata integration, also use `og-image-creator` and read its `references/framework-workflows.md` and `references/og-specifications.md`.

## Dependencies

Use the target project's environment when possible:

```bash
python3 -m pip install openai Pillow
```

Or run without installing into the project:

```bash
uv run --with openai --with Pillow python scripts/generate_og_ai.py --help
```

Generation requires `OPENAI_API_KEY`. The script defaults to `gpt-image-2`, `1536x1024`, and `medium` quality before cropping to 1200x630. Use `--model`, `--size`, and `--quality low|medium|high|auto` to adjust. Check current OpenAI pricing before quoting exact costs.

## Workflow

### 1. Discover Existing State

Start with the deterministic analyzer from `og-image-creator`:

```bash
OG_CREATOR_ROOT="${CODEX_HOME:-$HOME/.codex}/skills/og-image-creator"
python3 "$OG_CREATOR_ROOT/scripts/analyze_codebase.py" /path/to/project
```

Review `/path/to/project/og-analysis.json` before generation. If routes, metadata, colors, or site name are wrong, inspect the project and correct the analysis before using it.

Discovery targets:

- `package.json`, framework config, route files, SEO components, layouts, and MD/MDX frontmatter.
- Existing `metadata`, `generateMetadata`, `<Head>`, Helmet, static `<meta>`, or CMS ownership.
- CSS variables, Tailwind/theme config, fonts, favicons, app icons, logo files, and existing OG assets.
- Real data for dynamic routes; do not generate final cards for `[slug]`, `:id`, or `*` patterns without concrete content.

### 2. Decide The Visual Strategy

Use AI backgrounds when the content benefits from atmosphere, metaphor, or illustration. Prefer `og-image-creator` when the project needs exact brand tokens, repeated corporate cards, very low cost, or deterministic regeneration.

Choose style and content inputs from project context:

- Landing: product category, offer, audience, and brand colors.
- Article: topic, category, date or series when available, and a visual metaphor.
- Product: actual product surface, feature domain, or workflow cue.
- Documentation: restrained technical texture and high text clarity.
- About/company: identity, mission, team, or location cues without fake logos or text.

### 3. Dry-Run Prompts

Single image:

```bash
SKILL_ROOT="${CODEX_HOME:-$HOME/.codex}/skills/og-image-ai"
python3 "$SKILL_ROOT/scripts/generate_og_ai.py" \
  --title "Building Scalable APIs" \
  --description "A guide to API design patterns" \
  --style tech \
  --page-type article \
  --brand-colors "#2563eb,#14b8a6" \
  --dry-run
```

Batch prompt review:

```bash
SKILL_ROOT="${CODEX_HOME:-$HOME/.codex}/skills/og-image-ai"
python3 "$SKILL_ROOT/scripts/generate_og_ai.py" \
  --analysis ./og-analysis.json \
  --output ./public/og \
  --limit 3 \
  --dry-run
```

Inspect dry-run output for generic imagery, missing brand cues, forbidden text requests, or page-type mismatch before spending API calls.

### 4. Generate A Calibration Set

Generate one to three images first:

```bash
SKILL_ROOT="${CODEX_HOME:-$HOME/.codex}/skills/og-image-ai"
python3 "$SKILL_ROOT/scripts/generate_og_ai.py" \
  --analysis ./og-analysis.json \
  --output ./public/og \
  --style tech \
  --quality low \
  --limit 3
```

Use `--theme-hint` for extra project-specific context. Use `--custom-prompt` only when the preset cannot express the desired visual direction; keep the no-text and clear-zone constraints.
When `--brand-colors` is supplied with `--custom-prompt`, the script still appends brand palette guidance after the custom prompt.

### 5. Review And Iterate

Open `public/og/preview.html` or inspect the generated PNGs. Regenerate the calibration set if backgrounds fight the text, feel generic, ignore the brand, include unwanted text, or hide important visual details behind the overlay.

Only after the style works, generate the full stable route set:

```bash
SKILL_ROOT="${CODEX_HOME:-$HOME/.codex}/skills/og-image-ai"
python3 "$SKILL_ROOT/scripts/generate_og_ai.py" \
  --analysis ./og-analysis.json \
  --output ./public/og \
  --style corporate \
  --quality medium
```

Dynamic routes are skipped by default. Use `--include-dynamic` only to create an intentional fallback image for a route pattern; for final per-slug previews, add concrete route records from CMS or content data.
If one or more routes fail during batch generation, the script still writes the manifest and preview for successful routes, then exits nonzero with the failed route list.

### 6. Integrate Metadata

If the user wants integration, use the existing framework metadata pattern. Prefer existing SEO helpers and shared layouts over one-off tag blocks.

Keep these invariants:

- Final images are 1200x630 PNGs in a public asset directory.
- `og:image` and `twitter:image` resolve to deployed public URLs or framework-resolved public paths.
- Include width, height, and useful alt text when the framework supports them.
- Do not edit generated `dist/` or build output when a source template or layout owns metadata.

## Anti-Patterns

**Generating before discovery**

Why bad: The image may use the wrong routes, metadata owner, colors, or asset path.

Better: Run or reuse `og-analysis.json`, inspect gaps, then generate.

**Prompting the model to draw the title**

Why bad: Image models can still render text incorrectly, and social-card text must stay exact.

Better: Ask for no text in the background and let Pillow composite all typography.

**Full-site batch generation on the first pass**

Why bad: Cost and inconsistent style compound quickly.

Better: Dry-run prompts, generate a small calibration set, then scale.

**Treating dynamic route patterns as final pages**

Why bad: A card for `/blog/[slug]` is not a finished preview for real content.

Better: Skip dynamic routes unless creating a deliberate fallback; generate concrete per-slug cards from real data.

**Replacing a precise brand system with generic AI art**

Why bad: It can weaken recognition and look detached from the product.

Better: Use deterministic `og-image-creator` cards or constrain AI imagery to subtle, brand-aligned backgrounds.

## Verification

Before finishing:

- Confirm generated files are 1200x630.
- Review `preview.html` at 600x315 or smaller and confirm title and description remain readable.
- For non-Latin titles, confirm the selected system font renders real glyphs rather than fallback boxes.
- Check that no AI-generated text, fake logos, or important hidden details appear in the background.
- Inspect `manifest.json` for correct routes, filenames, dimensions, and alt text.
- Verify metadata in rendered or deployed HTML when integration was performed.
- Confirm file sizes are reasonable for social sharing; optimize or switch strategy if assets are too large.
