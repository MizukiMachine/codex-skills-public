---
name: "imagegen"
description: "AI生成のビットマップ画像を作成・編集する。写真、イラスト、テクスチャ、スプライト、モックアップ、透明背景切り抜きが必要なときに使う。SVGやHTML/CSSで直接作る用途は除く。"
---

# Image Generation Skill

現在の project 用に画像を生成または編集する。対象例は website assets、game assets、UI mockups、product mockups、wireframes、logo design、photorealistic images、infographics など。

## Top-Level Modes and Rules

このスキルには top-level mode が2つだけある。

- **Default built-in tool mode (preferred):** 通常の画像生成、編集、単純な transparent image request では built-in `image_gen` tool を使う。`OPENAI_API_KEY` は不要。
- **Fallback CLI mode:** `scripts/image_gen.py` CLI を使う。ユーザーが CLI/API/model path を明示的に求めた場合、または `gpt-image-1.5` による true model-native transparency fallback をユーザーが明示確認した後だけ使う。`OPENAI_API_KEY` が必要。

CLI fallback では CLI が次の subcommand を提供する。

- `generate`
- `edit`
- `generate-batch`

ルール:

- 通常の画像生成・編集依頼では built-in `image_gen` tool を既定で使う。
- ordinary quality、size、file-path control のためだけに CLI fallback へ切り替えない。
- ユーザーが transparent image/background を明示した場合も、まず built-in `image_gen` に留まる。flat removable chroma-key background で prompt し、installed helper `$CODEX_HOME/skills/.system/imagegen/scripts/remove_chroma_key.py` で local removal する。
- built-in `image_gen` や CLI `gpt-image-2` から CLI `gpt-image-1.5` へ黙って切り替えない。これは model/path downgrade として扱い、ユーザーが既に `gpt-image-1.5`、`scripts/image_gen.py`、CLI fallback を明示していない限り確認する。
- transparent request が chroma-key removal ではきれいに処理しにくい、true/native transparency を求めている、または local removal validation に失敗した場合は、`gpt-image-2` が `background=transparent` を support しないため true transparency には CLI `gpt-image-1.5 --background transparent --output-format png` が必要だと説明し、進めるか確認する。CLI fallback はユーザー確認後だけ実行する。
- `batch` という語だけでは CLI fallback を意味しない。大量 asset や batch-generate の依頼でも CLI/API/model control を明示していない場合は built-in path に留まり、asset や variant ごとに built-in call を1回ずつ行う。
- built-in tool が失敗または利用不可の場合、CLI fallback があり `OPENAI_API_KEY` が必要だと伝える。ユーザーがその fallback を明示的に求めた場合だけ進める。
- ユーザーが CLI mode を明示した場合は bundled `scripts/image_gen.py` workflow を使う。一回限りの SDK runner を作らない。
- `scripts/image_gen.py` は絶対に変更しない。足りないものがある場合は、他の作業をする前にユーザーへ確認する。

Built-in save-path policy:

- built-in tool mode では、Codex は既定で generated images を `$CODEX_HOME/*` 配下に保存する。
- built-in の既定保存先を OS temp として説明したり、それに依存したりしない。
- built-in `image_gen` tool に destination-path argument があるかのように説明・依存しない。特定 location が必要なら、生成後に `$CODEX_HOME/generated_images/...` から選択した output を移動または copy する。
- built-in mode の save-path precedence:
  1. ユーザーが destination を指定した場合、選択 output をそこへ移動または copy する。
  2. 画像が current project 用の場合、完了前に最終選択 image を workspace へ移動または copy する。
  3. preview や brainstorming だけなら inline に render する。underlying file は既定の `$CODEX_HOME/*` path に残っていてよい。
- project から参照する asset を既定の `$CODEX_HOME/*` path のみに残さない。
- ユーザーが replacement を明示していない限り existing asset を上書きしない。`hero-v2.png` や `item-icon-edited.png` のような sibling versioned filename を作る。

両 mode 共通の prompt guidance は `references/prompting.md` と `references/sample-prompts.md` にある。

CLI mode 専用 docs/resources:

- `references/cli.md`
- `references/image-api.md`
- `references/codex-network.md`
- `scripts/image_gen.py`

Local post-processing helper:

- `$CODEX_HOME/skills/.system/imagegen/scripts/remove_chroma_key.py`: generated image の flat chroma-key background を除去し、alpha 付き PNG/WebP を書き出す。antialiased edges には auto-key sampling、soft matte、despill を優先する。

## When to Use

- 新しい image を生成する。例: concept art、product shot、cover、website hero。
- style、composition、mood の参照として1枚以上の reference image を使い、新しい image を生成する。
- 既存 image を編集する。例: inpainting、lighting/weather transformation、background replacement、object removal、compositing、transparent background。
- 1つの task で多数の assets や variants を作る。

## When Not to Use

- repo 内の既存 SVG/vector icon set、logo system、illustration library を拡張・一致させる場合。
- simple shapes、diagrams、wireframes、icons など、SVG、HTML/CSS、canvas で直接作る方が適切な場合。
- source file が editable native format で既に存在する小さな project-local asset edit。
- ユーザーが generated bitmap ではなく deterministic code-native output を明確に求めている task。

## Decision Tree

次の2点を分けて考える。

1. **Intent:** 新規画像か、既存画像の編集か。
2. **Execution strategy:** 1 asset か、多数の assets/variants か。

Intent:

- ユーザーが既存 image の一部を保ったまま変更したい場合は **edit** として扱う。
- ユーザーが image を style、composition、mood、subject guidance の参照としてだけ提供した場合は **generate** として扱う。
- image が提供されていない場合は **generate** として扱う。

Built-in edit semantics:

- built-in edit mode は、attached image や thread 内で以前に生成された image のように、conversation context 上で既に見えている image のためのもの。
- ユーザーが local image file を built-in tool で編集したい場合、まず built-in `view_image` tool で読み込み、conversation context に image が見える状態にしてから built-in edit flow を進める。
- built-in tool で任意 filesystem-path editing ができると約束しない。
- local file に direct file-path control、masks、その他 CLI-only parameter が必要な場合は、ユーザーが明示的に求めた場合だけ CLI fallback を使う。
- edit では invariants を強く保持し、既定では non-destructive に保存する。

Execution strategy:

- built-in default path では、asset または variant ごとに `image_gen` call を1回ずつ出して多数 outputs を作る。
- CLI fallback path では、ユーザーが CLI mode を明示的に選び、多数 prompts/assets が必要な場合だけ CLI `generate-batch` subcommand を使う。
- 多数の distinct assets では、separate prompt の代わりに `n` を使わない。`n` は1 prompt の variants 用である。distinct assets には distinct built-in calls または distinct CLI `generate-batch` jobs が必要。

ユーザーが既存画像の変更を明確に求めていない限り、新規画像を求めていると仮定する。

## Workflow

1. top-level mode を決める。既定は built-in。単純な transparent-output request も built-in。fallback CLI は明示要求または transparent-output fallback の明示確認後だけ使う。
2. intent を `generate` または `edit` に決める。
3. output が preview-only か current project で消費されるものかを決める。
4. execution strategy を single asset、repeated built-in calls、CLI `generate-batch` から決める。
5. inputs を先に集める。prompt(s)、exact text (verbatim)、constraints/avoid list、input images。
6. すべての input image について role を明示する。
   - reference image
   - edit target
   - supporting insert/style/compositing input
7. edit target が local filesystem 上だけにあり built-in path に留まる場合は、conversation context に image を出すため `view_image` で先に inspect する。
8. ユーザーが photo、illustration、sprite、product image、banner など raster-style asset を明示した場合、SVG/HTML/CSS placeholder で代替せず `image_gen` を使う。icon、logo、UI graphic が既存 repo-native SVG/vector/code assets に合わせるべき場合は、直接それらを編集する方を優先する。
9. specificity に応じて prompt を補強する。
   - ユーザー prompt が具体的で詳細なら、creative requirement を足さず clear spec に normalize する。
   - ユーザー prompt が generic なら、output quality を実質的に改善する tasteful augmentation だけ足す。
10. built-in `image_gen` tool を既定で使う。
11. transparent-output request では下の transparent image guidance に従う。built-in `image_gen` で flat chroma-key background 付きに生成し、選択 output を workspace または `tmp/imagegen/` へ copy し、installed `$CODEX_HOME/skills/.system/imagegen/scripts/remove_chroma_key.py` helper を実行し、alpha result を検証してから使う。この path が不適切に見える、または失敗した場合は CLI `gpt-image-1.5` へ切り替える前に確認する。
12. output を inspect し、subject、style、composition、text accuracy、invariants/avoid items を検証する。
13. targeted change を1つだけ加えて iterate し、再確認する。
14. preview-only work では image を inline render する。underlying file は既定の `$CODEX_HOME/generated_images/...` path のままでよい。
15. project-bound work では選択 artifact を workspace へ移動または copy し、必要なら consuming code や references を更新する。project-referenced asset を既定の `$CODEX_HOME/generated_images/...` path のみに残さない。
16. batches または multi-asset request では、ユーザーが preview-only を明示していない限り、要求された deliverable はすべて workspace に final として保存する。discarded variant は要求されていない限り保持不要。
17. ユーザーが CLI fallback を明示的に選択または確認した場合のみ、model、quality、size、`input_fidelity`、masks、output format、output paths、network setup について fallback-only docs を使う。
18. workspace-bound asset の final saved path(s)、final prompt または prompt set、built-in tool と fallback CLI mode のどちらを使ったかを必ず報告する。

## Transparent Image Requests

transparent-image request でも最初は built-in `image_gen` を使う。built-in tool は true transparent-background control を公開していないため、removable chroma-key source image を作り、key color を local で alpha に変換する。

既定手順:

1. built-in `image_gen` で、要求 subject を perfectly flat solid chroma-key background 上に生成する。
2. subject に出にくい key color を選ぶ。既定は `#00ff00`。green subject には `#ff00ff` を使う。blue subject には `#0000ff` を避ける。
3. 生成後、選択 source image を `$CODEX_HOME/generated_images/...` から workspace または `tmp/imagegen/` に移動または copy する。
4. project-relative script path ではなく installed helper path を実行する。

```bash
python "${CODEX_HOME:-$HOME/.codex}/skills/.system/imagegen/scripts/remove_chroma_key.py" \
  --input <source> \
  --out <final.png> \
  --auto-key border \
  --soft-matte \
  --transparent-threshold 12 \
  --opaque-threshold 220 \
  --despill
```

5. output に alpha channel がある、corner が transparent、subject coverage が妥当、key-color fringe が目立たないことを検証する。薄い fringe が残る場合は `--edge-contract 1` で1回 retry する。edge が visibly stair-stepped で、subject が shiny/reflective でない場合だけ `--edge-feather 0.25` を使う。
6. asset が project-bound なら final alpha PNG/WebP を project に保存する。project-referenced transparent asset を `$CODEX_HOME/*` のみに残さない。

transparent request は次のように prompt する。

```text
Create the requested subject on a perfectly flat solid #00ff00 chroma-key background for background removal.
The background must be one uniform color with no shadows, gradients, texture, reflections, floor plane, or lighting variation.
Keep the subject fully separated from the background with crisp edges and generous padding.
Do not use #00ff00 anywhere in the subject.
No cast shadow, no contact shadow, no reflection, no watermark, and no text unless explicitly requested.
```

chroma keying の代わりに CLI `gpt-image-1.5 --background transparent --output-format png` を自動使用しない。ユーザーが true/native transparency を求める場合、local removal validation が失敗した場合、または hair、fur、feathers、smoke、glass、liquids、translucent materials、reflective objects、soft shadows、realistic product grounding、実用的な key color と衝突する subject colors など複雑な request の場合は、切り替え前に確認する。

確認は簡潔に行う。

```text
This likely needs true native transparency. The default built-in path uses a chroma-key background plus local removal, but true transparency requires the CLI fallback with gpt-image-1.5 because gpt-image-2 does not support background=transparent. It also requires OPENAI_API_KEY. Should I proceed with that CLI fallback?
```

## Prompt Augmentation

ユーザー prompt を structured, production-oriented spec に整える。ユーザーの goal を明確かつ actionable にするが、機械的に detail を追加しない。

closed schema ではなく prompt-shaping guidance として扱う。役に立つ line だけ使い、必要なら clarity を上げる short labeled line を追加する。

### Specificity Policy

ユーザー prompt の具体性で augmentation 量を決める。

- prompt が既に具体的で詳細なら、その具体性を保持し、normalize/structure だけ行う。
- prompt が generic なら、result を実質的に改善する tasteful augmentation を足してよい。

Allowed augmentations:

- composition/framing hints
- polish level または intended-use hints
- practical layout guidance
- stated request を支える reasonable scene concreteness

Not allowed augmentations:

- request から implied されない extra characters/objects
- implied されない brand names、slogans、palettes、narrative beats
- surrounding layout が支えない arbitrary side-specific placement

## Use-Case Taxonomy

各 request を次の bucket のいずれかに分類し、prompt や reference で slug を一貫して使う。

生成:

- `photorealistic-natural`: candid/editorial lifestyle scenes、real texture、natural lighting。
- `product-mockup`: product/packaging shots、catalog imagery、merch concepts。
- `ui-mockup`: app/web interface mockups、wireframes。desired fidelity を指定する。
- `infographic-diagram`: structured layout と text を持つ diagrams/infographics。
- `scientific-educational`: labels と accuracy constraints が必要な classroom explainers、scientific diagrams、learning visuals。
- `ads-marketing`: audience、brand position、scene、exact tagline/copy を持つ campaign concepts と ad creatives。
- `productivity-visual`: slides、charts、workflow、data-heavy business visuals。
- `logo-brand`: logo/mark exploration、vector-friendly。
- `illustration-story`: comics、children's book art、narrative scenes。
- `stylized-concept`: style-driven concept art、3D/stylized renders。
- `historical-scene`: period-accurate/world-knowledge scenes。

編集:

- `text-localization`: in-image text を翻訳・置換し、layout を保持する。
- `identity-preserve`: try-on、person-in-scene。face/body/pose を lock する。
- `precise-object-edit`: 特定 element の remove/replace。interior swaps を含む。
- `lighting-weather`: time-of-day、season、atmosphere のみを変える。
- `background-extraction`: transparent background / clean cutout。simple opaque subjects では built-in `image_gen` with chroma-key removal を先に使い、complex subjects で true CLI transparency を使う前に確認する。
- `style-transfer`: reference style を適用しつつ subject/scene を変える。
- `compositing`: multi-image insert/merge。lighting/perspective を合わせる。
- `sketch-to-render`: drawing/line art から photoreal render。

## Shared Prompt Schema

両 top-level mode で共通の prompt scaffolding として、次の labeled spec を使う。

```text
Use case: <taxonomy slug>
Asset type: <where the asset will be used>
Primary request: <user's main prompt>
Input images: <Image 1: role; Image 2: role> (optional)
Scene/backdrop: <environment>
Subject: <main subject>
Style/medium: <photo/illustration/3D/etc>
Composition/framing: <wide/close/top-down; placement>
Lighting/mood: <lighting + mood>
Color palette: <palette notes>
Materials/textures: <surface details>
Text (verbatim): "<exact text>"
Constraints: <must keep/must avoid>
Avoid: <negative constraints>
```

Notes:

- `Asset type` と `Input images` は prompt scaffolding であり、dedicated CLI flags ではない。
- `Scene/backdrop` は visual setting を指す。fallback CLI の `background` parameter とは別物で、そちらは output transparency behavior を制御する。
- `Quality:`、`Input fidelity:`、masks、output format、output paths など fallback-only execution notes は CLI path だけに属する。built-in `image_gen` tool arguments として扱わない。

Augmentation rules:

- 短く保つ。
- prompt を実質的に改善する detail だけ追加する。
- edit では invariants (`change only X; keep Y unchanged`) を明示する。
- 成功を妨げる critical detail が欠けている場合だけ質問する。それ以外は進める。

## Examples

### Generation Example

```text
Use case: product-mockup
Asset type: landing page hero
Primary request: a minimal hero image of a ceramic coffee mug
Style/medium: clean product photography
Composition/framing: wide composition with usable negative space for page copy if needed
Lighting/mood: soft studio lighting
Constraints: no logos, no text, no watermark
```

### Edit Example

```text
Use case: precise-object-edit
Asset type: product photo background replacement
Primary request: replace only the background with a warm sunset gradient
Constraints: change only the background; keep the product and its edges unchanged; no text; no watermark
```

## Prompting Best Practices

- prompt は scene/backdrop -> subject -> details -> constraints の順に構造化する。
- intended use (ad、UI mock、infographic など) を含め、mode と polish level を伝える。
- photorealism では camera/composition language を使う。
- ユーザーが vector output または non-image placeholder を明示した場合だけ SVG/vector stand-ins を使う。
- exact text は quote し、typography と placement を指定する。
- tricky words は letter-by-letter で綴り、verbatim rendering を要求する。
- multi-image inputs では image index で参照し、どう使うかを説明する。
- edit では drift を減らすため、iteration ごとに invariants を繰り返す。
- single-change follow-up で iterate する。
- prompt が generic なら material に役立つ extra detail だけ加える。
- prompt が詳細なら expand せず normalize する。
- CLI fallback 専用の model、`quality`、`input_fidelity`、masks、output format、output-path guidance は `references/cli.md` と `references/image-api.md` を参照する。
- transparent images では request が complex で true CLI transparency を必要とする場合を除き、built-in-first chroma-key workflow を使う。CLI `gpt-image-1.5` へ切り替える前に確認する。

両 mode 共通の追加原則: `references/prompting.md`。
両 mode 共通の copy/paste specs: `references/sample-prompts.md`。

## Guidance by Asset Type

website assets、game assets、wireframes、logo などの asset-type template は `references/sample-prompts.md` に集約されている。

## gpt-image-2 Guidance for CLI Fallback

fallback CLI は既定で `gpt-image-2` を使う。

- true model-native transparent output が必要な場合を除き、新規 CLI/API workflow では `gpt-image-2` を使う。
- transparent request が CLI fallback を必要としそうな場合、ユーザーが `gpt-image-1.5`、`scripts/image_gen.py`、CLI fallback を既に明示していない限り、`gpt-image-1.5` を使う前に確認する。built-in chroma-key path が既定だが、true transparency は `gpt-image-2` が `background=transparent` を support しないため `gpt-image-1.5` が必要だと説明する。
- `gpt-image-2` は image inputs で常に high fidelity を使う。この model では `input_fidelity` を設定しない。
- `gpt-image-2` は `quality` values `low`、`medium`、`high`、`auto` を support する。
- fast drafts、thumbnails、quick iterations では `quality low` を使う。final assets、dense text、diagrams、identity-sensitive edits、high-resolution outputs では `medium`、`high`、または `auto` を使う。
- square images は一般に生成が最速。fast square draft では `1024x1024` を使う。
- 4K-style output を求められた場合、landscape は `3840x2160`、portrait は `2160x3840` を使う。
- `gpt-image-2` size は `auto` または `WIDTHxHEIGHT`。ただし max edge `<= 3840px`、both edges multiples of `16px`、long-to-short ratio `<= 3:1`、total pixels が `655,360` から `8,294,400` の間という constraint をすべて満たす必要がある。

Popular `gpt-image-2` sizes:

- `1024x1024` square
- `1536x1024` landscape
- `1024x1536` portrait
- `2048x2048` 2K square
- `2048x1152` 2K landscape
- `3840x2160` 4K landscape
- `2160x3840` 4K portrait
- `auto`

## Fallback CLI Mode Only

### Temp and Output Conventions

この convention は CLI fallback のみに適用される。built-in `image_gen` の output behavior ではない。

- intermediate files (例: JSONL batches) には `tmp/imagegen/` を使い、完了後に削除する。
- final artifacts は `output/imagegen/` 配下に書く。
- output path control には `--out` または `--out-dir` を使い、filename は stable かつ descriptive に保つ。

### Dependencies

この repo では dependency management に `uv` を優先する。

Required Python package:

```bash
uv pip install openai
```

local chroma-key removal と optional downscaling に必要:

```bash
uv pip install pillow
```

Portability note:

- installed skill をこの repo の外で使う場合、その environment の package manager で dependencies を install する。
- uv-managed environment では `uv pip install ...` を優先する。

### Environment

- live API calls には `OPENAI_API_KEY` が必要。
- built-in `image_gen` tool を使う場合は、ユーザーに `OPENAI_API_KEY` を求めない。
- ユーザーに full key を chat に貼らせない。local に設定して準備できたら確認してもらう。

key がない場合は次を伝える。

1. OpenAI platform UI で API key を作成する: https://platform.openai.com/api-keys
2. system の environment variable として `OPENAI_API_KEY` を設定する。
3. 必要なら OS/shell ごとの environment variable 設定を案内すると提案する。

この environment で installation ができない場合は、欠けている dependency と active environment への install 方法を伝える。

### Script-Mode Notes

- CLI commands と examples: `references/cli.md`
- API parameter quick reference: `references/image-api.md`
- CLI mode の network approvals / sandbox settings: `references/codex-network.md`

## Reference Map

- `references/prompting.md`: 両 mode 共通の prompting principles。
- `references/sample-prompts.md`: 両 mode 共通の copy/paste prompt recipes。
- `references/cli.md`: `scripts/image_gen.py` による fallback-only CLI usage。
- `references/image-api.md`: fallback-only API/CLI parameter reference。
- `references/codex-network.md`: CLI mode の fallback-only network/sandbox troubleshooting。
- `scripts/image_gen.py`: fallback-only CLI implementation。ユーザーが CLI mode を明示的に選ぶ、または transparent request の true CLI transparency fallback を明示確認した場合以外は load/use しない。
- `$CODEX_HOME/skills/.system/imagegen/scripts/remove_chroma_key.py`: built-in transparent-image request 用の local post-processing helper。
