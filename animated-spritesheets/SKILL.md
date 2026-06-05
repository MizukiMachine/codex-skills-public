---
name: animated-spritesheets
description: "1枚のキャラクター参照画像からAI生成向けのアニメーションスプライトシートを作る。プロンプト、フレーム復元、背景除去、正規化、プレビュー生成で使う。"
metadata:
  short-description: "参照画像からアニメーションスプライトシートを作る"
---

# Animated Spritesheets

1枚の character reference image、多くは `1024x1024` の high-resolution sprite-like image から、usable animated spritesheet と review artifacts (contact sheets / GIFs) を作る。

使う場面:

- approved reference sprite から directional anchors / action sheets を作る
- poses が implied frame cells から drift した AI-generated sheets を salvage する
- game team が実際に inspect できる review artifacts を作る

使わない場面:

- final pixel art を frame-by-frame で手描きする
- tilemaps、environment sheets、UI icon sets
- source pixel が厳密に正しい strict tiny-pixel workflows

典型的な inputs:

- approved reference image 1枚
- optional sheet guide。例: `512x1280` alternating-pixel contact sheet
- direction、action、frame ordering を書いた prompt file

典型的な outputs:

- generated sheet / directional anchor
- recovered component crops
- optional no-background crops
- normalized runtime frames
- labeled contact sheet
- selected-sequence GIF

## 考え方: Spritesheet は2つの問題

AI sprite workflow は「frames を生成する」だけとして扱うと失敗しやすい。実際には2つの別問題。

1. **Generation**: 正しい character、direction、action を出す
2. **Registration**: それを stable engine-style frames に変換する

多くの場合、2つ目の方が難しい。

作業前に確認すること:

- strict tiny-pixel art か high-resolution pixelated art か
- reference は approved in-game identity か concept art か
- deliverable は single anchor、full spritesheet、finished GIF preview のどれか
- model が invisible cell boundaries をまたいだ場合、source of truth は cells か full sheet か

基本原則:

1. approved in-game sprite を identity anchor にする
2. polishing 前に recovery。missing silhouette / framing を先に直す
3. sequence につき one shared anchor。shared center/bottom rule で normalize する
4. contact sheets と GIFs は pipeline の一部

## ワークフロー

### 1. input reference を選ぶ

approved sprite-like reference 1枚を優先する。conflicting art sources を複数混ぜない。gameplay-facing sprite がない場合だけ concept art を使う。

### 2. sheet guide を作る

multi-frame generation では sheet-sized guide を先に作る。

`scripts/make_alternating_sheet.py` は次に使う。

- neutral alternating-pixel background
- `512x1280` など arbitrary sizes
- visible grid lines なしで pixel texture を促す guide

これは style/composition hint であり、strict frame cells を model が守る保証ではない。

### 2b. video-derived walk cycles では neutral plates

image-to-video models で walk-cycle source motion を作る場合、checkerboard、alternating-pixel sheet、visible grid を start background にしない。video model が floor、room、horizon、perspective grid と解釈し、camera drift や scene motion を作るため。

direction-specific neutral plate:

- `1280x720` canvas
- flat neutral gray background
- approved direction anchor を中央に置き、feet visible
- checker/grid/floor/horizon/arrows/labels なし
- bobbing / cloth sway 用 padding

prompt は facing direction、camera/framing、flat background、in-place walk、no scene/props/effects を lock する。template は `references/prompt-patterns.md`。

video は motion reference としてだけ使う。raw frames を extract し、contact sheets / GIFs を作り、team が curate した frame だけ background removal / normalization する。

### 3. whole sheet 用 prompt

production brief のように構造化する。

- intended use
- image roles
- subject and direction
- ordered frame sequence
- look/rendering constraints
- composition constraints
- explicit avoid list

frame list は具体的にする。例:

- `Frame 1: ready idle`
- `Frame 5: first shot muzzle flash`
- `Frame 10: return to idle`

patterns は `references/prompt-patterns.md`。

### 4. naive cell crops を信用しない

output size が正しくても hats、coats、feet、muzzle flashes が implied cell boundaries をまたぐ場合がある。

まず full sheet に `scripts/recover_component_frames.py` を使う。

- dominant foreground components を detect
- intended grid へ bucket back
- tight recovered frame crops を保存

これが実際の source of truth になることが多い。

### 5. silhouette recovery 後に background removal

cleaner edges が必要な場合、original rigid cell crops ではなく recovered component crops に background removal をかける。

remove.bg batch は `scripts/remove_bg_batch.py`。

理由:

- raw cell crops は既に間違っている可能性がある
- whole-sheet background removal は元の geometry を壊すことが多い
- per-component removal は recover した silhouette を保持する

### 6. one shared anchor に normalize

`scripts/normalize_frames.py` で recovered/cleaned crops を fixed runtime frame に置く。例:

- canvas `256x256`
- center `x = 128`
- bottom `y = 255`

これで sideways drift と fake skating を防ぐ。

生成された cell が transparent crops ではなく **opaque flat-background crops** の場合は、それらの cell から直接 GIF を作ってはいけない。まず `scripts/normalize_flat_bg_frames.py` を使い、connected corner background を flood-fill し、実際の foreground を crop し、すべての frame を same center/bottom anchor へ normalize する。これは、model が各 nominal `256x256` cell 内でキャラクターを異なる x/y offset に置いてしまう、よくある idle-sheet failure を修正する。

### 6b. visible foot baseline を audit

normalization 後、final engine frames 内の **visible** alpha bounds を確認する。

これは image canvas size とは別の話である。`256x256` frame でも feet が `y = 215` で終わり下に 40px transparent padding があると、frame は依然として間違っている。Phaser のような engine では sprite origin と shadow は通常、visible pixels ではなく full frame rectangle に対して適用されるため、bottom padding が frame ごとに不揃いだとキャラクターが shadow の上に浮いて見える。

runtime sheet export 前:

- 各 frame の alpha bounding box を inspect
- lowest non-transparent pixel が intended baseline、例 `bottomY = 255`、にあるか確認
- 同じ character の全 directions / states を比較
- runtime より大きな review canvas を downscale/crop/pad した後は再 baseline

`gamedev-assets` skill の `asset_sprite_baseline.py` で audit / correction できる。

### 7. review artifacts を作る

- `scripts/build_contact_sheet.py`: labeled review sheets
- `scripts/build_sequence_gif.py`: loops / curated sequences

少なくとも generated sheet、recovered crops、normalized contact sheet、selected-sequence GIF を review する。

## 避けること

**invisible grid を信用する**

問題: canvas size が正しくても、model は cells をまたいで compose することがある。
改善: frame boundaries を確定する前に full sheet から components を recover する。

**whole sheet に background removal**

問題: remove.bg などは全体 foreground bounds へ crop し、sheet geometry を壊しやすい。
改善: recovered component crop ごとに background removal する。

**per-frame recentering**

問題: frame ごとの独立 recentering は drift と fake motion を生む。
改善: sequence 全体を one shared center/bottom anchor に normalize する。

**frame size を foot alignment の証明とみなす**

問題: `256x256` frame でも feet の下に transparent padding があると、engine 上で shadow/origin bugs が出る。
改善: runtime export 前に alpha bounds を audit し、visible foot baseline を揃える。

**walk-cycle video に checker/grid backgrounds**

問題: video models は grid を physical scene と解釈し、perspective、horizon、camera drift、character turns を足すことがある。
改善: neutral `1280x720` flat-background direction plate を使い、extraction 後に selected frames を curate / normalize する。

**recovery 前に polish**

問題: edge cleanup では missing feet や sliced coats は復元できない。
改善: full silhouette を recover してから edge cleanup する。

**pixel-perfect tools を常に有効とみなす**

問題: 一部の pixel-snapping tools は high-resolution pixelated sprites を過剰 quantize したり縮めたりする。
改善: recovery / normalization 後に試し、readability が上がる場合だけ採用する。

## Variation Guidance

pipeline は target look、direction set、action type、sheet layout に応じて変える。

sequence 内で stable にするもの:

- identity source
- shared anchor rule
- frame canvas size
- final runtime frame 内の visible foot baseline
- final GIF の selection logic

変えてよいもの:

- action / direction ごとの prompt wording
- selected frame order
- palette cleanup strategy
- background removal の有無

## Adaptation Rules

- model が clean isolated frames を返すなら recovery を skip して normalization
- sheet geometry が unreliable なら nominal cell math より full-sheet recovery
- background removal が edges を壊すなら opaque crop を normalize
- single directional anchor なら generation + review で止める
- one-shot runner が大げさなら individual scripts を直接使う
- normalized review frames から runtime sheets に downscale/convert したら final PNGs を再 audit

## Resources

- Workflow reference: `references/pipeline.md`
- Prompt scaffolds: `references/prompt-patterns.md`
- Guide sheet generator: `scripts/make_alternating_sheet.py`
- One-shot pipeline runner: `scripts/run_pipeline.py`
- Full-sheet component recovery: `scripts/recover_component_frames.py`
- remove.bg batching: `scripts/remove_bg_batch.py`
- Frame normalization: `scripts/normalize_frames.py`
- Contact sheet builder: `scripts/build_contact_sheet.py`
- GIF builder: `scripts/build_sequence_gif.py`

## Quick Start

whole pipeline が必要な場合は runner を使う。

```bash
uv run scripts/run_pipeline.py \
  --work-dir runs/my-character-attack \
  --reference refs/character-anchor-1024.png \
  --guide refs/alternating-sheet-512x1280.png \
  --prompt-file prompts/attack-sheet.txt \
  --sheet-size 512x1280 \
  --sheet-prefix attack-sheet \
  --rows 5 \
  --cols 2 \
  --frame-canvas 256x256 \
  --center-x 128 \
  --bottom-y 255 \
  --remove-bg \
  --selected-order 01,03,02,04,05,07,09 \
  --durations-ms 140,110,110,110,120,120,160 \
  --flat-bg '#f0f0f0'
```

runner は既定で sibling `gpt-image-2-0` skill を generation に使う。layout が違う場合は `--gpt-image-edit-script` または `ANIMATED_SPRITESHEETS_GPT_IMAGE_EDIT` で上書きする。

## 覚えておくこと

AI spritesheets の難所は character を描かせることではなく、有望な sheet から stable、readable、engine-style frames へ持っていくこと。silhouette recovery、edge cleanup、normalization、motion curation の順で進める。
