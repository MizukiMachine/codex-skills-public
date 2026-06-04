---
name: gpt-image-2-0
description: "OpenAI gpt-image-2で画像生成・編集ワークフローを組む。任意サイズ、複数参照画像、透明背景、商品レンダー、コンセプトアート、API利用の相談で使う。"
metadata:
  short-description: "OpenAI GPT Image 2の生成、編集、プロンプト、APIラッパー"
---

# GPT Image 2.0

OpenAI `gpt-image-2` で実際に画像生成や画像編集を行うとき、またはこの model に合わせた強い prompt と output controls が必要なときに使う。

## 考え方: 雰囲気ではなく仕様として扱う

`gpt-image-2` は production brief のように request を整理したときに強い。subject、framing、materials、constraints、output size、edit boundaries を含む、model が実行しやすい spec に変換する。

**生成前に確認すること:**

- deliverable は concept art、icon、product render、scene plate、marketing image、reference-driven edit のどれか
- identity、camera angle、silhouette、text、palette、proportions、brand cues など何を安定させるべきか
- output は fast iteration、final review、web delivery、specific pixel size のどれに最適化するか
- 1枚の image か、関連する image system か

**基本原則**

1. **形容詞の羅列より仕様**: 明確な subject/composition/output constraints が強い
2. **parameters も creative brief の一部**: `size`、`quality`、`output_format`、`output_compression`、`background` は結果を大きく変える
3. **edit では preserve-language を書く**: 何を変え、何を変えないかを明示する
4. **生成事実を正直に扱う**: API を実行して files を書いた後だけ、生成済みと伝える

## GPT Image 2 の扱い

OpenAI は `gpt-image-2` を generation / editing 用の current state-of-the-art GPT Image model としている。2026-04-21 時点の model page では alias `gpt-image-2`、snapshot `gpt-image-2-2026-04-21`。older workflows との差分:

- model constraints 内で arbitrary image sizes を support
- image inputs は常に high fidelity で処理
- JPEG / WebP は explicit compression control を support
- `gpt-image-2` は transparent backgrounds 非対応

意図して読む references:

- `references/openai-gpt-image-2.md`: model / API constraints
- `references/openai-prompting-guide.md`: prompt structure、text-heavy workflows、multi-image prompting、iteration patterns

## 使う場面

- user が OpenAI image generation / edits を求める
- `gpt-image-2` 用 prompt が必要
- Images API の runnable script が必要
- `2048x2048` や `3840x2160` など large custom dimensions が役立つ
- identity と composition を複数 source images に分ける multi-image reference edits が必要

## API Choice

- one prompt in, one image result out なら Images API
- conversational、tool-driven、longer multimodal exchange なら Responses API
- local wrapper で `POST /v1/images/generations` または `POST /v1/images/edits` を直接叩くなら同梱 scripts

## Generation Workflow

1. deliverable、invariants、output target を特定する
2. maintain しやすい prompt format を選ぶ。production work では labeled spec が長文より扱いやすい
3. prompt scaffolding は必要に応じて次の順にする
   - intended use / asset type
   - scene / backdrop
   - subject
   - composition / camera framing
   - style / material / era
   - lighting / color treatment
   - text requirements
   - exact constraints and exclusions
4. text-heavy、layout-sensitive、reference-driven の場合は final prompt 前に `references/openai-prompting-guide.md` を読む
5. 詳細 prompt は膨らませず normalize する。ユーザー指定が薄く、改善に意味がある場合だけ上品に補う
6. output controls を意図して選ぶ
   - `size`: `auto` または documented `gpt-image-2` limits を満たす `WIDTHxHEIGHT`
   - `quality`: `low`, `medium`, `high`, `auto`
   - `output_format`: `png`, `webp`, `jpeg`
   - `output_compression`: `jpeg` / `webp` 用 `0-100`
   - `background`: `opaque` または `auto`
7. generation requested で `OPENAI_API_KEY` がある場合は `scripts/gpt_image_generate.py` を使う
8. outputs は user-visible path に保存し、何を生成したか正確に報告する

### Prompt Scaffold

```text
Intended use:
Primary request:
Input images:
Scene/backdrop:
Subject:
Style/medium:
Composition/framing:
Lighting/mood:
Text (verbatim):
Constraints:
Avoid:
```

task type ごとの詳細 pattern は `references/openai-prompting-guide.md` を読む。

### Prompt Construction

production-oriented prompts を優先する。

```text
Create a polished isometric apothecary counter prop for a fantasy management game. Brass scale, labeled glass jars, dark walnut wood, neatly arranged herbs, centered composition, soft studio lighting, readable silhouette, no text, no frame, no watermark.
```

layout-sensitive work では design spec のように構造化する。iteration は silhouette、framing、material treatment、lighting、palette、detail density のように1軸ずつ変える。

## Edit Workflow

`gpt-image-2` は image inputs を常に high fidelity で処理する。edit は強くなるが、reference-image edits は older low-fidelity flows より cost が上がる場合がある。

edits / reference-image workflows:

1. task に必要な最小 image set だけ送る
2. prompt で role を明示する
   - `image 1 = identity anchor`
   - `image 2 = pose/layout reference`
   - `image 3 = texture/material reference`
3. 何を変えるか、何を変えないかを両方書く
4. controlled retouch では reinterpretation より small delta を優先する
5. text replacement、localization、layout preservation では `references/openai-prompting-guide.md` を読み、preservation spec として書く
6. local edit requests は `scripts/gpt_image_edit.py` を使う

Example:

```text
Use image 1 as the identity anchor and image 2 as the composition guide. Keep the same bottle shape, label placement, and cork silhouette from image 1. Change only the glass color to smoky teal, add faint condensation, and match the three-quarter tabletop framing from image 2. Do not add extra props, text, or background clutter.
```

## 重要な Output Controls

### Size

explicit `WIDTHxHEIGHT` は次を満たす。

- maximum edge length `<= 3840`
- both edges must be multiples of `16`
- aspect ratio must not exceed `3:1`
- total pixels must be between `655,360` and `8,294,400`

popular documented sizes:

- `1024x1024`
- `1536x1024`
- `1024x1536`
- `2048x2048`
- `2048x1152`
- `3840x2160`
- `2160x3840`
- `auto`

### Quality

- `low`: drafts、thumbnails、cheap iteration
- `medium`: normal design iteration
- `high`: detail が重要な final assets
- `auto`: quality を固定する理由がない brief

### Format / Compression

- `png`: lossless default、最大 fidelity
- `jpeg`: smaller and faster。OpenAI notes JPEG is faster than PNG
- `webp`: modern web delivery 向け compression
- `output_compression`: `jpeg` / `webp` のみ

### Background

`gpt-image-2` では `opaque` または `auto`。transparent backgrounds は非対応。

## 同梱 scripts

生成:

```bash
OPENAI_API_KEY=... \
python3 .codex/skills/gpt-image-2-0/scripts/gpt_image_generate.py \
  --prompt "Premium olive oil bottle product shot on a clean stone surface, soft shadows, editorial lighting" \
  --out-dir tmp/olive-oil \
  --size 2048x2048 \
  --quality medium \
  --output-format webp \
  --output-compression 80
```

複数 reference images から edit:

```bash
OPENAI_API_KEY=... \
python3 .codex/skills/gpt-image-2-0/scripts/gpt_image_edit.py \
  --image refs/identity.png \
  --image refs/layout.png \
  --prompt "Use image 1 for identity and image 2 for composition. Keep the same bottle silhouette and label placement. Change the liquid to deep amber and add subtle highlights." \
  --out-dir tmp/bottle-edit \
  --size 1536x1024 \
  --output-format jpeg \
  --output-compression 70
```

Useful flags:

- `--filename-prefix hero`
- `--user trace-id-123`
- `--print-json`

## 避けること

**transparent-cutout model のように扱う**

問題: この model は transparent background 非対応。
改善: hard requirement が native transparency なら別 model を使う。通常は flat background + post-processing を検討する。

**huge images を既定にする**

問題: large size / high quality は cost と latency を上げ、exploration を遅くする。
改善: 探索では `1024x1024`、`1536x1024`、`1024x1536`、`low` から始める。

**`png` に `output_compression` を使う**

問題: compression control は `jpeg` / `webp` 専用。
改善: `png` では `output_compression` を使わず、圧縮が必要なら `jpeg` / `webp` を選ぶ。

**reference images を送りすぎる**

問題: complexity と cost が増え、model focus が薄まる。
改善: 必要最小限の references にし、identity、layout、palette など role を明示する。

**prompt salad**

問題: 矛盾する style / composition cues は adherence を弱める。
改善: one composition と one dominant rendering direction に整理する。

**毎回 prompt をゼロから書く**

問題: iteration が比較不能になり、production prompt を保守しにくい。
改善: compact scaffold と references を使い、変更軸だけを調整する。

**API 実行前に成功したと言う**

問題: prompt proposal と generated asset は別物。
改善: API を実行し output path を確認してから成功を報告する。

## Variation Guidance

すべてを同じ polished style にしない。

- product render、icon、character art、scene art、edit requests で prompt emphasis を変える
- web delivery、review images、marketing crops、large art boards で size/format を変える
- literal product shot は tight control、concept exploration は loose control
- consistent set を意図している場合だけ visual direction を再利用する

## 参照

- API/model notes: `references/openai-gpt-image-2.md`
- Prompting patterns: `references/openai-prompting-guide.md`
- Runnable generator: `scripts/gpt_image_generate.py`
- Runnable editor: `scripts/gpt_image_edit.py`
- Official model page: https://developers.openai.com/api/docs/models/gpt-image-2
- Official guide: https://developers.openai.com/api/docs/guides/image-generation
- Official Images API reference: https://developers.openai.com/api/reference/resources/images
- Official prompting guide: https://developers.openai.com/cookbook/examples/multimodal/image-gen-models-prompting-guide

## 覚えておくこと

`gpt-image-2` を儀式ではなく実務にする。request を concrete spec にし、parameters を意図して選び、可能なら API を実行し、real output path を報告する。
