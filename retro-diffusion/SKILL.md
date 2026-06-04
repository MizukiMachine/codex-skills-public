---
name: retro-diffusion
description: "Retro Diffusionでピクセルアート画像やスプライトシートを生成・編集する。参照画像から歩行サイクルやターンアラウンドなどのアニメーション素材を試すときに使う。"
metadata:
  short-description: "Retro Diffusionの画像・アニメーションワークフロー"
---

# Retro Diffusion

Retro Diffusion で pixel-art images や animation sheets を生成する場合に使う。特に side-view platformer walks、turnarounds、action cycles など reference-image-driven character work に向く。

## 考え方: Style を Asset Contract に合わせる

Retro Diffusion は fal のような provider-agnostic model marketplace ではない。重要な control は `prompt_style` で、style ごとに asset contract が違う。

- general image models
- spritesheet-oriented styles
- fixed-size animation generators
- input frame を必要とし、neutral poses から強い styles

正しい使い方:

- 欲しい asset shape に合う style を選ぶ
- style の size contract を守る
- `input_image` には clean RGB reference を渡す
- cost checks と output capture を workflow の first-class step として扱う

**生成前に確認すること:**

- single image、spritesheet、animation のどれか
- freeform prompt、reference-driven edit、starting-frame animation のどれか
- selected `prompt_style` に fixed frame size があるか
- GIF preview、PNG spritesheet、または両方が必要か

**基本原則**

1. **style first, prompt second**: `prompt_style` は flavor ではなく mode selector
2. **size contracts を守る**: `animation__four_angle_walking` は `48x48`、`animation__8_dir_rotation` は `80x80`、advanced animations は starting frame size に合わせる
3. **reference cleanliness matters**: `input_image` は transparency なしの RGB。prompt で reference を説明する
4. **preview だけでなく sheet を capture**: sprite work では `return_spritesheet: true`
5. **prompt は短く**: advanced animations は service が action text を内部展開する。長い prompt は server-side で失敗し得る
6. **completion は artifacts で判断**: wrapper が timeout しても run が成功している場合がある

## 提供するもの

- portable Retro Diffusion harness:
  - text-to-image
  - `input_image` による img2img-style runs
  - `reference_images` による multi-reference runs
  - fixed-style animation / spritesheet generation
- generic inference runner:
  - `POST https://api.retrodiffusion.ai/v1/inferences`
  - `check_cost: true` による cost-only checks
  - normalized run manifests と decoded outputs の書き出し
- repeatable experiment configs 用 batch runner
- useful presets:
  - `rd-pro-platformer`
  - `rd-pro-edit`
  - `rd-pro-spritesheet`
  - `rd-fast-character-turnaround`
  - `rd-plus-character-turnaround`
  - `animation-four-angle-walking`
  - `animation-8-dir-rotation`
  - `animation-walking-and-idle`
  - `rd-advanced-animation-walking`
  - `rd-advanced-animation-idle`
  - `rd-advanced-animation-attack`

## Working With Retro Diffusion

### API Shape

- Endpoint: `POST https://api.retrodiffusion.ai/v1/inferences`
- Auth header: `X-RD-Token: YOUR_API_KEY`

outputs:

- `base64_images`
- `output_urls`
- `balance_cost`
- `remaining_balance`

operational rule:

- terminal process に final success line がないだけで失敗と決めない
- local caller が indeterminate state を返しても、Retro Diffusion run は完了している場合がある
- retry 前に output folder を確認する
  - new image artifacts
  - run metadata JSON
  - run start より新しい file modification times
- missing stdout ではなく artifact verification 後に failed と判断する

animations は通常 transparent GIFs で返る。PNG sheet が必要なら `return_spritesheet: true` を付ける。

### Reference And Animation Guidance

`input_image`:

- 先に RGB へ変換する
- transparency を除去する
- `data:image/png;base64,` prefix は含めない
- prompt で reference が何かを書く
- silent RGBA-to-black conversion より explicit prepared RGB reference image を使う

side-view platformer walks:

- neutral starting frame があるなら `rd_advanced_animation__walking` を先に試す
- `width` と `height` は starting frame と合わせる
- `frames_duration` を意図して指定する
- extractable frames が必要なら in-place locomotion を求める
- large anchor が不安定なら compact square reference を準備して retry
- `return_spritesheet: true` では transparent spritesheet PNG が返った実績がある

multi-direction walking presets:

- `animation__four_angle_walking` と `animation__walking_and_idle` は `48x48` workflows
- broad exploration には有用だが、既存 `64x64` anchor との直接比較には向かない

eight-direction turnaround:

- one-shot directional sheet が欲しいときは `animation__8_dir_rotation` を first probe にする
- fixed `80x80` として扱う
- server errors や weak directions が出たら staged `rd_pro__edit` workflow へ切り替える
- dependable fallback:
  - isometric anchor から cardinals を先に作る
  - same anchor + cardinal sheet を `reference_images` として diagonals を作る

### Prompting Guidance

concept art copy ではなく animation direction として書く。

- character は誰か
- facing direction
- intended motion
- 何を stable に保つか
- 何を避けるか

良い components:

- identity: compact adventurer、same costume colors、same silhouette and proportions
- facing: side-facing、profile view、facing right
- motion: walk cycle in place、readable step rhythm、alternating arm swing
- stability: keep silhouette and costume consistent frame to frame
- exclusions: no camera movement、no perspective rotation、no extra props、no background

advanced animation prompts:

- 1-2 short sentences
- long descriptive prose を避ける
- identity details を過剰に繰り返さない
- 可能なら full prompt を `300` characters 未満に保つ

ただし guardrails は残す。`side-facing`、`same costume and silhouette`、action disambiguation、`no background clutter` などを削ると別 motion family へ drift し得る。

## Scripts

- `scripts/retro_inference_run.py`: one run、image/edit/animation/spritesheet、cost-only mode
- `scripts/retro_experiment_matrix.py`: JSON-defined experiment batch
- `scripts/prepare_reference_image.py`: local PNG から RGB reference を準備、matte flatten、nearest-neighbor square resize

## Portable Workflow

project-specific artifacts は skill directory ではなく user's working project に置く。

default layout:

- checked-in experiment contracts: `experiments/retro-diffusion/configs/`
- generated outputs: project-owned `outputs/`、`artifacts/`、asset-staging directory
- prompts、notes、learnings は project が使う experiment docs の隣に置く

skill は scripts、references、presets を提供し、prompts/configs/manifests/generated images の置き場所は user project が決める。

## Run Verification Workflow

run が stall、timeout、ambiguous result に見える場合:

1. start 前に intended output directory を記録する
2. run を1回だけ launch
3. wrapper が clean completion を出さない場合、まず output directory を inspect
4. expected filenames、non-empty PNG/GIF、run JSON / response JSON、new timestamps を確認
5. artifacts があれば completed と扱い、sheet quality を評価する
6. retry は no new artifacts、または returned artifact が明らかに corrupt / incomplete の場合だけ

practical rule: ambiguous transport state は model failure ではない。files first、retry second。

## 避けること

**incompatible animation styles を同一 task として比較する**

問題: fixed `48x48` walker と reference-driven advanced walking sheet は output contract が違う。
改善: style ごとの size、input、sheet / GIF contract を分けて評価する。

**transparent RGBA sprites を直接 `input_image` に渡す**

問題: alpha が黒や予期しない matte として扱われ、silhouette や色が崩れることがある。
改善: RGB へ変換し、clean flat background 付きの prepared reference を渡す。

**GIF か spritesheet かを指定せず walk animation を頼む**

問題: downstream extraction / frame comparison の契約が曖昧になる。
改善: sprite workflow では `return_spritesheet: true` を指定し、artifact を deterministic に扱う。

**advanced animation modes で verbose prompts**

問題: hidden validation limit や prompt expansion と衝突し、server-side failure になることがある。
改善: action prompt は非常に terse にし、identity / facing / background clauses だけを残す。

**良い run の後に prompt を単純化しすぎる**

問題: facing、silhouette、action type、background behavior が外れ、次 run で drift する。
改善: stability に効いた lock clauses は残す。

**wrapper の success message なしで即 retry**

問題: local wrapper が timeout や final response drop を起こしても、artifact は生成済みのことがある。
改善: retry 前に intended output folder の PNG / GIF / JSON を確認する。

**reference image だけで style が保たれると仮定する**

問題: image reference だけでは orientation、identity、action semantics が弱い場合がある。
改善: prompt でも facing、silhouette、costume、action を補強する。

**larger isometric anchor が常に良いと仮定する**

問題: larger / angled anchor は walk cycle や side-facing motion を不安定にすることがある。
改善: compact prepared anchor を試し、side-facing / neutral pose を優先する。

**`animation__8_dir_rotation` を canonical turnaround path とみなす**

問題: 8-dir rotation は first probe には有用でも、すべての turnaround に最適とは限らない。
改善: probe として扱い、必要なら staged `rd_pro__edit` などに切り替える。

**frame-size contracts を無視する**

問題: style によって size が clamp / ignore され、engine contract とずれる場合がある。
改善: style ごとの documented size / returned artifact を検証してから runtime asset 化する。

**general-purpose video model として扱う**

問題: Retro Diffusion は sprite-native outputs 用 API で、自由な video generation とは契約が違う。
改善: sprite / animation / spritesheet artifacts として扱い、motion reference 用 video model と混同しない。

## Variation Guidance

- asset contract に応じて `RD_PRO`、`RD_FAST`、advanced animation styles を使い分ける
- short attack と longer walk tests で `frames_duration` を変える
- downstream need に応じて GIF preview / spritesheet を選ぶ
- platformer walking の best prompt が turnarounds / idles にも最適とは仮定しない

## 参照

- API and style notes: `references/api-and-styles.md`
- Animation strategy notes: `references/animation-workflows.md`
- Presets: `assets/model-presets.json`
- Prompt starters: `assets/prompt-profiles/`

## 覚えておくこと

Retro Diffusion は built-in style を正しく選び、clean reference を渡し、必要な sprite artifact を明確に求め、advanced-animation prompts を短く保ち、結果を one-off prompt ではなく experiment として追跡したときに強い。
