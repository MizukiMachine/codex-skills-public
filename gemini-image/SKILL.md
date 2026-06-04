---
name: gemini-image
description: "Gemini画像モデルで画像生成・編集ワークフローを組む。複数参照画像、キャラクター一貫性、Google検索でのグラウンディング、Gemini API利用の相談で使う。"
metadata:
  short-description: "Gemini画像生成・編集、generateContent、プロンプト、APIラッパー"
---

# Gemini Image

Google の Gemini image models で画像生成・編集を行うとき、または model selection、multi-image references、multi-turn refinement、grounded image generation が必要なときに使う。

## 考え方: 1 API、3 model、意図して選ぶ

Gemini は他の Gemini と同じ `generateContent` endpoint で画像生成する。最初の判断は prompt ではなく、model、`imageConfig`、references、thinking の必要性。

**生成前に確認すること:**

- deliverable は concept art、marketing visual、product render、edit pass、infographic、screenshot、character-consistent set のどれか
- model は Pro、3.1 Flash、2.5 Flash / Nano Banana のどれが合うか
- calls 間で character identity、palette、layout、brand text、aspect ratio の何を安定させるか
- multi-step layout、infographic、world building など reasoning が必要か、direct render で足りるか
- 1枚が goal か、iterative editing の multi-turn chat が必要か

**基本原則**

1. **model selection は parameter**: 3 Pro、3.1 Flash、2.5 Flash は resolution ceiling、reference capacity、aspect ratios、thinking の有無が違う
2. **`imageConfig` も prompt の一部**: `aspectRatio` と `imageSize` は framing、token cost、asset usefulness を変える
3. **references には role を付ける**: multiple input images はそれぞれの役割を prompt で label する
4. **thinking は有料 compute**: layout-heavy / reasoning-heavy brief では有効、direct render では省く
5. **生成事実を正直に扱う**: API を実行し bytes を file に書いた後だけ generated と伝える

## Gemini Image Models

Gemini API は `POST /v1beta/models/{model}:generateContent` で image generation を expose する。image output は `generationConfig.responseModalities = ["TEXT", "IMAGE"]` で opt-in。image bytes は `candidates[0].content.parts[].inlineData` に base64 で返る。

利用可能な image models:

- `gemini-3-pro-image-preview`: Pro tier。thinking on by default。最大 4K、最大 6 object + 5 character refs
- `gemini-3.1-flash-image-preview`: balanced default。最大 4K、14 aspect ratios、最大 10 object + 4 character refs、web + image search grounding
- `gemini-2.5-flash-image`: Nano Banana。speed / cost optimized、1K cap、最大 3 reference images、thinking なし

すべて SynthID watermark 付き。transparent backgrounds は非対応。audio / video inputs は受け付けない。

読む references:

- `references/gemini-image-models.md`: model variants、`imageConfig`、reference limits、pricing-shaped token costs
- `references/gemini-prompting-guide.md`: prompt structure、multi-image references、multi-turn editing、thinking、grounding

## 使う場面

- Gemini image generation または Nano Banana を求められた
- Gemini で conversational image editing が必要
- reference images を使って character / product consistency を保ちたい
- Google Search による grounded image が必要
- image output 用 `generateContent` wrapper が必要
- Gemini と `gpt-image-2`、`gpt-image-1.5`、fal-hosted models を比較する

Next.js / web app をこれら model で作る場合は、full-stack patterns 用に `nano-banana-builder` を優先する。この skill は API/CLI layer に留める。

## Model Selection

| Need | Recommended model |
|---|---|
| highest fidelity、complex layout、infographics、multi-step reasoning | `gemini-3-pro-image-preview` |
| most aspect ratios、most references、image-search grounding、balanced cost | `gemini-3.1-flash-image-preview` |
| cheap iteration、quick drafts、simple prompts at 1K | `gemini-2.5-flash-image` |
| transparent cutouts | なし。`gpt-image-1.5` などを使う |
| native sprite art / pixel art | なし。`retro-diffusion` または `gpt-image-2` を使う |

## API Choice

- one-shot generation、edits、reference-driven composition には `generateContent`
- multi-turn iterative editing には chat session pattern (Python `client.chats.create`, JS `ai.chats.create`)
- many images かつ 24h turnaround を許容する場合は Batch API
- direct local wrapper が必要なら同梱 scripts

## Generation Workflow

1. deliverable、invariants、target aspect ratio / size を特定する
2. model を選ぶ。premium reasoning は 3 Pro、balanced default は 3.1 Flash、cheap drafts は 2.5 Flash
3. prompt を brief に合わせた順序で書く
   - intended use / asset type
   - subject
   - scene / backdrop
   - composition / camera framing
   - style / material / era
   - lighting / color treatment
   - text requirements。verbatim は quotes
   - exact constraints and exclusions
4. `imageConfig` を意図して選ぶ
   - `aspectRatio`: model の supported list から選ぶ
   - `imageSize`: `"1K"`、3.x の `"2K"` / `"4K"`、3.1 Flash の `"512"` / `"0.5K"`
5. thinking の必要性を決める
   - 3 Pro: default on。direct render では `thinkingConfig.thinkingLevel: "minimal"`
   - 3.1 Flash: opt-in。layout-heavy work では `"High"`
   - 2.5 Flash: thinking なし
6. grounding が必要なら `tools: [{"google_search": {}}]` を追加する
7. `GEMINI_API_KEY` または `GOOGLE_API_KEY` があれば `scripts/gemini_image_generate.py` を実行する
8. outputs を user-visible path に保存し、file path と model を報告する

### Prompt Scaffold

brief が構造化で良くなる場合は、次の compact spec を使う。

```text
Intended use:
Subject:
Scene/backdrop:
Composition/framing:
Style/medium:
Lighting/mood:
Text (verbatim):
Aspect ratio:
Constraints:
Avoid:
```

actual API request では、これは `contents[0].parts[0].text` の string と `imageConfig` block へ map する。

### Prompt Construction

production-oriented prompts を優先する。

```text
Editorial overhead shot of a single matcha latte on a pale linen runner, ceramic cup with a thin gold rim, faint steam, scattered loose-leaf tea, warm afternoon window light from the left, magazine-style negative space on the right for headline text, no people, no logos.
```

text-heavy / layout-sensitive work では mood description ではなく design spec として書き、literal copy は必ず引用する。

iteration は1軸ずつ変える。

- subject pose / framing
- material / palette
- lighting direction
- background treatment
- density of detail

## Edit Workflow

Gemini の edit は2種類。

- **Single-call edit**: source image(s) と edit instruction を1回の `generateContent` に送る
- **Chat-based edit**: chat session を開き source image を送り、text turns で refinement する。各 turn は新 image を返し、model が visual context を保持する

edits / reference-image workflows:

1. 必要最小限の images を送る
2. prompt で role を明示する
   - `image 1 = identity anchor`
   - `image 2 = layout/pose reference`
   - `image 3 = palette/material reference`
3. change list と preserve list を両方書く
4. continuity が重要なら wholesale reinterpretation より small deltas
5. consistency set では同じ identity anchor を毎回送り、anchor language も verbatim で保つ
6. local edit requests は `scripts/gemini_image_edit.py` を使う

edit prompt example:

```text
Use image 1 as the identity anchor and image 2 as the composition guide. Keep the same character face, hair color, jacket pattern, and proportions from image 1. Change only the background to a rainy night street with neon signage, and match the three-quarter framing from image 2. Keep aspect ratio 16:9. Do not redesign the jacket, do not add new characters, do not add text.
```

### Multi-Turn Chat Editing

iterative refinement では repeated one-shot calls ではなく chat session を使う。model が prior images と prompts を context として保持するため、"now make it..."、"and add..."、"go back to the previous version but..." のような workflows に強い。

practical rule: ユーザーが複数 revision を求めそうなら chat を開く。そうでなければ one-shot。

## 重要な `imageConfig`

### Aspect Ratio

- `gemini-3.1-flash-image-preview`: 1:1, 1:4, 1:8, 2:3, 3:2, 3:4, 4:1, 4:3, 4:5, 5:4, 8:1, 9:16, 16:9, 21:9
- `gemini-3-pro-image-preview` / `gemini-2.5-flash-image`: 1:1, 2:3, 3:2, 3:4, 4:3, 4:5, 5:4, 9:16, 16:9, 21:9

usage に合わせて選ぶ。icons は 1:1、heroes は 16:9、mobile/story は 9:16、cinematic は 21:9、editorial portraits は 4:5。3.1 Flash の 1:4 / 1:8 / 4:1 / 8:1 は ribbons や strips に使える。

### Image Size

- `"512"` / `"0.5K"`: drafts and thumbnails。3.1 Flash only
- `"1K"`: standard。全 models
- `"2K"`: detailed work。3.x only
- `"4K"`: final assets。3.x only

token cost は size に比例する。探索中は `1K`、detail が重要になってから `2K` / `4K`。

### Thinking

- `thinkingLevel: "minimal"`: fastest, weakest reasoning
- `thinkingLevel: "High"`: stronger layout planning, more tokens
- 3 Pro は default on、3.1 Flash は opt-in、2.5 Flash は knob なし
- thinking tokens は `includeThoughts` 表示有無に関係なく billed

### Grounding

`tools: [{"google_search": {}}]` を追加すると Google Search で grounding できる。real products、recent events、real places、public figures likenesses で有用。ただし 3.1 Flash は web + image search、3 Pro / 2.5 Flash は web search only。image search path は people images を取得できない。

## 同梱 scripts

生成:

```bash
GEMINI_API_KEY=... \
python3 .agents/skills/gemini-image/scripts/gemini_image_generate.py \
  --prompt "Editorial overhead shot of a single matcha latte on linen, magazine negative space on the right, warm window light" \
  --model gemini-3.1-flash-image-preview \
  --aspect-ratio 16:9 \
  --image-size 2K \
  --out-dir tmp/matcha
```

reference images から edit:

```bash
GEMINI_API_KEY=... \
python3 .agents/skills/gemini-image/scripts/gemini_image_edit.py \
  --image refs/identity.png \
  --image refs/layout.png \
  --prompt "Use image 1 for identity and image 2 for composition. Keep the same face and jacket. Change background to a rainy night street with neon signage." \
  --model gemini-3-pro-image-preview \
  --aspect-ratio 16:9 \
  --image-size 4K \
  --out-dir tmp/identity-edit
```

Useful flags:

- `--thinking-level minimal|High`
- `--google-search`
- `--filename-prefix hero`
- `--print-json`
- `--n 1`

scripts は `POST /v1beta/models/{model}:generateContent` を `responseModalities=["TEXT","IMAGE"]` 付きで呼び、inline base64 を decode して files を書く。

## 避けること

**every request を 3 Pro にする**

問題: Pro thinking は simple drafts や quick iterations では token cost を増やすだけになりやすい。
改善: まず 3.1 Flash を使い、layout、infographics、multi-step reasoning が必要なときだけ 3 Pro に上げる。

**transparent backgrounds を求める**

問題: Gemini image models は transparent backgrounds を生成しない。
改善: flat color で render して downstream で key out するか、native transparency が必要なら `gpt-image-1.5` などに切り替える。

**reference images を積みすぎる**

問題: input tokens が増え、model focus が薄まり、2.5 Flash では上限にも当たりやすい。
改善: identity / layout / palette anchors など必要最小限にし、各 image の role を prompt で label する。

**six-revision request を one-shot で処理する**

問題: repeated one-shot calls は prior visual context を失い、small deltas が drift する。
改善: iterative refinement では chat session を使い、model に prior image context を保持させる。

**direct render で thinking default のままにする**

問題: literal product shot などは reasoning を必要とせず、thinking token cost だけ増える。
改善: direct brief では `thinkingLevel: "minimal"` を設定する。

**初期から 4K**

問題: 4K は token cost と latency を増やし、ideation には過剰。
改善: exploration は 1K、prompt lock 後に 2K / 4K へ上げる。

**Gemini image を fact evidence として扱う**

問題: Google Search grounding があっても rendered image は stylized reconstruction であり citation ではない。
改善: real subject を反映する必要があるときだけ grounding し、事実の根拠は別に cite する。

**API 実行前に成功したと言う**

問題: prompt proposal と generated asset は別物。
改善: credentials があれば script を実行し、なければ generation 未実行と理由を明示する。

**SynthID watermark を無視する**

問題: Gemini images には invisible SynthID watermark が付くため、provenance や redistribution 判断に影響する。
改善: provenance、attribution、AI-generated 여부が話題なら明示する。

## Variation Guidance

- deliverable で model choice を変える。drafts は 2.5 Flash、balanced は 3.1 Flash、premium/complex は 3 Pro
- usage で aspect ratio を変える
- stage で image size を変える。explore は 1K、lock-in 後に 2K/4K
- literal product shot、stylized illustration、infographic で prompt structure を変える
- consistent set を意図する場合だけ identity anchors を再利用する

## 参照

- Model variants and parameters: `references/gemini-image-models.md`
- Prompting patterns: `references/gemini-prompting-guide.md`
- Runnable generator: `scripts/gemini_image_generate.py`
- Runnable editor: `scripts/gemini_image_edit.py`
- Official guide: https://ai.google.dev/gemini-api/docs/image-generation

## 覚えておくこと

Gemini image generation を儀式ではなく実務にする。model、`imageConfig`、thinking を意図して選び、credentials があるなら API を実行し、real output path と model を報告する。
