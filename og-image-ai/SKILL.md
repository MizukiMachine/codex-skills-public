---
name: og-image-ai
description: "AIイラストとPillowのテキスト合成でOpen Graph画像を生成する。記事カード、製品ページ、SNSプレビュー、og-analysis.jsonの一括処理で使う。"
metadata:
  short-description: "AIイラストのOG画像を生成"
---

# OG Image AI

## 目的

AI-generated visual backgrounds と、Pillow による crisp / deterministic text overlays を組み合わせて 1200x630 Open Graph images を生成する。`og-image-creator` の creative companion として使い、route discovery、metadata integration、preview verification の代替にはしない。

## 基本方針

AI OG image も page metadata contract の一部。AI は theme、mood、visual specificity を担当し、script は text、safe area、dimensions、filenames、manifests、preview pages を管理する。

優先順位:

1. 正しい route metadata、public image paths、framework-native integration
2. social-preview thumbnail size でも読める text
3. 実 project に基づく brand and page-type fit
4. dry runs と small batches による controlled cost and iteration

生成前に確認すること:

- framework、routing model、current metadata owner
- canonical site URL と public/static asset directory
- brand colors、typography、logo usage、visual tone、existing OG images
- stable routes と、concrete slug data が必要な dynamic route patterns
- AI imagery がこの project に望ましいか、deterministic `og-image-creator` cards の方が brand に合うか

## 使い分け

| Scenario | Use og-image-ai | Use og-image-creator |
|----------|-----------------|----------------------|
| illustrated / atmospheric social card background | Yes | No |
| article/product page ごとの unique thematic visual | Yes | Maybe |
| strict design-system consistency at scale | No | Yes |
| API spend なし、または fully deterministic output required | No | Yes |
| metadata audit or framework integration only | Maybe | Yes |
| large route set の first pass | small calibration batch 後のみ | Yes |

## Capabilities

- `og-image-creator` の `og-analysis.json` を再利用し、route-aware batch generation を行う
- page-type と brand-color prompt guidance 付きで GPT Image backgrounds を生成する
- title、description、accent bar、optional site name を Pillow で composite する
- `[slug]` cards を final per-page images と誤解しないよう、dynamic route patterns は既定で skip する
- visual review 用の `manifest.json` と `preview.html` を作る

## 成果物

- `public/og/*.png` または project equivalent public asset path
- route、file、dimensions、alt text records を含む `public/og/manifest.json`
- social-card proportions で確認する `public/og/preview.html`
- integration 依頼時の framework-native metadata updates
- generated assets、metadata edits、verification の短い最終要約

## 参照ファイル

| Topic | File | Use When |
|-------|------|----------|
| Prompt design | [references/prompt-design.md](references/prompt-design.md) | style presets、page-type hints、custom prompts、anti-text instructions を選ぶ |
| Generator script | [scripts/generate_og_ai.py](scripts/generate_og_ai.py) | single images、dry-run prompts、`og-analysis.json` からの batches |

framework-specific metadata integration では `og-image-creator` も使い、`references/framework-workflows.md` と `references/og-specifications.md` を読む。

## Dependencies

可能なら target project の environment を使う。

```bash
python3 -m pip install openai Pillow
```

project に install せず実行する場合:

```bash
uv run --with openai --with Pillow python scripts/generate_og_ai.py --help
```

generation には `OPENAI_API_KEY` が必要。script は既定で `gpt-image-2`、`1536x1024`、`medium` quality を使い、1200x630 へ crop する。`--model`、`--size`、`--quality low|medium|high|auto` で調整する。正確な cost を言う前には current OpenAI pricing を確認する。

## ワークフロー

### 1. 既存状態を調べる

`og-image-creator` の deterministic analyzer から始める。

```bash
OG_CREATOR_ROOT="${CODEX_HOME:-$HOME/.codex}/skills/og-image-creator"
python3 "$OG_CREATOR_ROOT/scripts/analyze_codebase.py" /path/to/project
```

generation 前に `/path/to/project/og-analysis.json` を review する。routes、metadata、colors、site name が違う場合は project を調べ、analysis を修正してから使う。

Discovery targets:

- `package.json`、framework config、route files、SEO components、layouts、MD/MDX frontmatter
- 既存 `metadata`、`generateMetadata`、`<Head>`、Helmet、static `<meta>`、CMS ownership
- CSS variables、Tailwind/theme config、fonts、favicons、app icons、logo files、existing OG assets
- dynamic routes の real data。concrete content なしに `[slug]`、`:id`、`*` の final cards を生成しない

### 2. visual strategy を決める

content が atmosphere、metaphor、illustration から利益を得る場合は AI backgrounds を使う。exact brand tokens、repeated corporate cards、very low cost、deterministic regeneration が重要なら `og-image-creator` を優先する。

project context から style と content input を選ぶ。

- Landing: product category、offer、audience、brand colors
- Article: topic、category、date/series、visual metaphor
- Product: actual product surface、feature domain、workflow cue
- Documentation: restrained technical texture と high text clarity
- About/company: identity、mission、team、location cues。fake logos/text は避ける

### 3. dry-run prompts

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

API call 前に generic imagery、missing brand cues、forbidden text requests、page-type mismatch を dry-run output で確認する。

### 4. calibration set を生成する

最初は1-3枚だけ生成する。

```bash
SKILL_ROOT="${CODEX_HOME:-$HOME/.codex}/skills/og-image-ai"
python3 "$SKILL_ROOT/scripts/generate_og_ai.py" \
  --analysis ./og-analysis.json \
  --output ./public/og \
  --style tech \
  --quality low \
  --limit 3
```

project-specific context は `--theme-hint` で足す。`--custom-prompt` は preset では表現できない visual direction のときだけ使い、no-text と clear-zone constraints を保つ。`--brand-colors` と `--custom-prompt` を併用すると、script は custom prompt の後に brand palette guidance を追加する。

### 5. review and iterate

`public/og/preview.html` を開くか generated PNGs を確認する。背景が text と競合する、generic、brand 無視、unwanted text を含む、overlay に重要な detail が隠れる場合は calibration set を再生成する。

style が固まった後だけ stable route set 全体を生成する。

```bash
SKILL_ROOT="${CODEX_HOME:-$HOME/.codex}/skills/og-image-ai"
python3 "$SKILL_ROOT/scripts/generate_og_ai.py" \
  --analysis ./og-analysis.json \
  --output ./public/og \
  --style corporate \
  --quality medium
```

dynamic routes は既定で skip される。route pattern の fallback image を意図的に作る場合だけ `--include-dynamic` を使う。final per-slug previews では CMS や content data から concrete route records を追加する。batch generation 中に route failure があっても、成功分の manifest と preview は書かれ、failed route list 付きで nonzero exit する。

### 6. metadata に統合する

ユーザーが integration を求めた場合、既存 framework metadata pattern を使う。one-off tag blocks より既存 SEO helpers や shared layouts を優先する。

invariants:

- final images は public asset directory 内の 1200x630 PNG
- `og:image` と `twitter:image` は deployed public URLs、または framework-resolved public paths に resolve する
- framework が support するなら width、height、useful alt text を含める
- metadata owner が source template / layout にある場合、generated `dist/` や build output を編集しない

## 避けること

**discovery 前に生成する**

問題: routes、metadata owner、colors、asset path を外しやすい。
改善: `og-analysis.json` を確認し、route contract と brand sources を把握してから生成する。

**model に title を描かせる**

問題: image model の text は不正確になり得る。
改善: background には text なしを求め、typography は Pillow が composite する。

**初回から full-site batch generation**

問題: cost が膨らみ、style inconsistency も見つけにくくなる。
改善: dry-run と calibration set で prompt、layout、brand treatment を固定してから batch する。

**dynamic route patterns を final pages として扱う**

問題: `/blog/[slug]` は real content の preview ではなく、title や image facts が存在しない。
改善: actual content route / slug data から OG inputs を作る。

**precise brand system を generic AI art に置き換える**

問題: brand recognition を弱め、既存 site と乖離する。
改善: brand precision が重要なら deterministic `og-image-creator` cards を使う。

## 検証

- generated files が 1200x630 か確認する
- `preview.html` を 600x315 以下で確認し、title/description が読めるか見る
- non-Latin titles では font が fallback boxes ではなく glyphs を描くか確認する
- AI-generated text、fake logos、重要 detail の隠れがないか確認する
- `manifest.json` の routes、filenames、dimensions、alt text を確認する
- integration した場合は rendered/deployed HTML の metadata を確認する
- social sharing に対して file sizes が合理的か確認し、大きすぎる場合は optimize または strategy を変える
