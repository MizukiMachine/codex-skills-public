---
name: og-image-creator
description: "Webプロジェクト向けのOpen Graph画像とSNSプレビュー画像を作成・統合する。ブランド反映、メタデータ追加、共有画像の監査、ルート別OG画像生成で使う。"
---

# OG Image Creator

## 目的

共有される site に自然になじむ Open Graph images を作る。先に codebase を調べ、routes と brand signals を抽出し、review 可能な 1200x630 assets を生成し、framework-native style で metadata に統合する。

## 基本方針

OG image は standalone poster ではなく、page contract と brand system の一部。accurate previews、small social cards での readability、repeatable regeneration を最適化する。

優先順位:

1. 正しい route metadata、dimensions、URLs、accessibility
2. 既存 colors、fonts、logos、components、tone に基づく authentic brand fit
3. strong hierarchy と safe padding による thumbnail readability
4. one-off manual images ではなく maintainable generation path

作業前に確認すること:

- framework と routing model: Next.js App Router、Pages Router、Astro、Gatsby、React SPA、static HTML、custom
- current metadata owner: page exports、layout component、SEO component、HTML head、MD/MDX frontmatter、CMS data
- brand sources: logo files、CSS variables、Tailwind/theme config、fonts、components、screenshots、existing image style
- static vs dynamic need: fixed marketing pages、many content routes、user-generated routes、per-slug article cards
- absolute `og:image` / `twitter:image` 用の canonical site URL

## Capabilities

- web project を分析し、framework、routes、metadata、brand colors、fonts、logos を含む `og-analysis.json` を作る
- `public/og/` に route-specific images と `manifest.json`、`preview.html` を生成する
- pages が正しい Open Graph と Twitter card tags を expose するよう framework-native metadata を更新する
- generic design、stale metadata、missing absolute URLs、poor contrast、bad dimensions、over-large files を audit する

## 参照ファイル

| Topic | File | Use When |
|-------|------|----------|
| OG specs and validation | [og-specifications.md](references/og-specifications.md) | dimensions、metadata、URLs、image alt text、file size、platform preview behavior を確認 |
| Design and content principles | [design-principles.md](references/design-principles.md) | layouts、typography、hierarchy、brand usage、page-type variations を選ぶ |
| Framework workflows | [framework-workflows.md](references/framework-workflows.md) | Next.js、Astro、React SPA、Gatsby、static HTML に metadata を統合 |

## ワークフロー

### 1. 既存状態を調べる

analyzer を first pass として使い、gap は手動で code を確認する。

```bash
SKILL_ROOT="${CODEX_HOME:-$HOME/.codex}/skills/og-image-creator"
python3 "$SKILL_ROOT/scripts/analyze_codebase.py" /path/to/project
```

script は `/path/to/project/og-analysis.json` を書く。image 生成前に必ず review する。routes や brand signals が足りない場合は `rg` で framework files を直接調べ、JSON を patch するか analyzer result を改善する。dynamic routes は `dynamic: true` になる。`[slug]`、`:id`、`*` を final static pages として扱わず、real data から concrete per-slug entries を作る。

Discovery targets:

- `package.json`、framework config、route folders、route config、SEO components、layout components、MD/MDX frontmatter
- 既存 `<Head>`、`metadata`、`generateMetadata`、`Helmet`、HTML `<meta>` ownership
- `public/`、`src/assets/`、CSS files、Tailwind config、theme tokens、favicon/app icons、logo assets
- existing generated images と social preview references

### 2. strategy を選ぶ

stable routes と brand-critical pages は static generated images を使う。route count や user-generated content が static assets を不便にする場合のみ dynamic framework image generation を使う。

page-type-specific treatments:

- Landing: brand-forward、large value statement、minimal supporting copy
- Article/blog: category/date、title、excerpt、publisher mark
- Product/feature: product name、core benefit、actual visual or UI cue
- Documentation: topic label、structured feel、high clarity、restrained accents
- About/company: logo and identity-forward、professional and direct

### 3. reviewable images を生成する

rendering dependency がなければ target environment に入れる。

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

visual quality が重要なら `preview.html` を開くか screenshot する。`og-analysis.json`、routes、metadata、assets、generator を edit したら regenerate する。

generator は dynamic parameterized routes を既定で skip する。route pattern の fallback image を意図的に作る場合だけ `--include-dynamic` を使う。

### 4. metadata に統合する

detected framework について [framework-workflows.md](references/framework-workflows.md) を読む。既存 metadata abstraction があるなら優先する。なければ複数 page で long tag blocks を重複させず、小さな shared SEO helper を作る。

framework が自動展開しない場合、deployed social tags には absolute URLs を使う。可能なら `og:image:width`、`og:image:height`、`og:image:alt` を含める。

### 5. 検証する

- image dimensions が 1200x630
- text が safe area に収まり、小さな preview size でも読める
- file sizes が合理的。実用上は 200 KB 未満を優先
- deployed HTML の metadata が reachable absolute image URLs を指す
- social preview tools が cache refresh 後に意図した image を表示する
- metadata integration 中に無関係な user changes を上書きしていない

## Command Patterns

custom analysis path を指定して分析:

```bash
SKILL_ROOT="${CODEX_HOME:-$HOME/.codex}/skills/og-image-creator"
python3 "$SKILL_ROOT/scripts/analyze_codebase.py" . --output ./tmp/og-analysis.json
```

reviewed analysis file から生成:

```bash
SKILL_ROOT="${CODEX_HOME:-$HOME/.codex}/skills/og-image-creator"
python3 "$SKILL_ROOT/scripts/generate_og_images.py" . --analysis ./tmp/og-analysis.json --out-dir ./public/og
```

iteration 中に数 route だけ生成:

```bash
SKILL_ROOT="${CODEX_HOME:-$HOME/.codex}/skills/og-image-creator"
python3 "$SKILL_ROOT/scripts/generate_og_images.py" . --limit 3
```

dynamic route patterns の fallback images を意図的に生成:

```bash
SKILL_ROOT="${CODEX_HOME:-$HOME/.codex}/skills/og-image-creator"
python3 "$SKILL_ROOT/scripts/generate_og_images.py" . --include-dynamic
```

## 避けること

**discovery 前に生成する**

問題: routes、metadata owner、brand sources を外しやすい。
改善: analysis と確認後に生成する。

**全 route に同じ layout を使う**

問題: landing、docs、articles、products は伝える仕事が違う。
改善: page type ごとに hierarchy、emphasis、supporting copy を変える。

**generic gradient + title**

問題: どの site にも見え、brand recognition を弱める。
改善: actual brand tokens、logo assets、component shapes、spacing、typography を使う。

**final metadata に relative social image URLs を使う**

問題: crawler が local paths を resolve できない場合がある。
改善: canonical origin または framework metadata base を使う。

**overcrowded cards**

問題: social previews は thumbnails になりやすく、小さい text や複数 focal points は読めない。
改善: one dominant idea、short supporting copy、large type、safe padding を使う。

## Variation Guidance

- page type、content density、audience、share context で変える
- established design systems では exact tokens を再利用し、young projects では current UI に合う restrained generated style にする
- real product / UI visuals が役立つときは使い、decorative placeholders は避ける
- few static routes は hand-review、hundreds of routes は templating / dynamic generation を使う

避ける収束:

- 全 page で同じ title/logo placement
- site の palette が豊かなのに single dominant hue
- long titles を tiny type に押し込む
- project の established SEO pattern を無視した metadata edits
