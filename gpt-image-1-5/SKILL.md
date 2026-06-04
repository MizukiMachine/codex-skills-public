---
name: gpt-image-1-5
description: "OpenAI gpt-image-1.5で画像生成ワークフローを組む。透明背景、スタイル制御イラスト、コンセプトアート、アイコン、Images API利用の相談で使う。"
metadata:
  short-description: "OpenAI GPT Image 1.5の生成、プロンプト、APIラッパー"
---

# GPT Image 1.5

OpenAI `gpt-image-1.5` で実際に画像生成する場合、またはこの model に合わせた prompt と parameter selection が必要な場合に使う。

## 考え方: 意図を production request へ翻訳する

image generation は「きれいな prompt を書いて祈る」作業ではない。曖昧な art request を、subject、composition、style、constraints、output settings を持つ具体的な production request へ変換する。

**生成前に確認すること:**

- deliverable は concept art、icon、product render、marketing image、character sheet、UI element、transparent asset のどれか
- framing、palette、era、camera angle、background treatment、text、brand details など何を安定させるか
- file は review、iteration speed、print quality、web use、transparent cutout のどれに最適化するか
- single image か、related images の system か

**基本原則**

1. **adjective soup より intent**: 具体的な composition と constraints を優先する
2. **output settings も prompt の一部**: size、quality、format、background は有用性を変える
3. **生成事実を正直に扱う**: API 実行または output 受領後だけ generated と伝える

## GPT Image 1.5 の扱い

OpenAI は `gpt-image-1.5` を text/image input と image/text output を持つ GPT Image model としている。Images API は generation で `gpt-image-1.5`、`png` / `webp` / `jpeg` output、documented size/quality/background controls を support する。詳細は `references/openai-gpt-image-1-5.md` を読む。

## 使う場面

- user が OpenAI で image generation を求める
- `gpt-image-1.5` 用 prompt が必要
- transparent-background assets、icons、concept art、product shots、stylized illustrations が必要
- Images API の runnable example または wrapper script が必要

## Generation Workflow

1. target deliverable と output constraints を request から明確化する
2. 必要に応じて prompt に次を含める
   - subject
   - composition
   - style/material/era
   - lighting/camera
   - important exclusions
   - file intent
3. API settings を意図して選ぶ
   - `size`: `1024x1024`, `1024x1536`, `1536x1024`, `auto`
   - `quality`: `low`, `medium`, `high`, `auto`
   - `output_format`: `png`, `webp`, `jpeg`
   - `background`: `transparent` は `png` または `webp` のみ
4. generation requested で `OPENAI_API_KEY` がある場合は `scripts/gpt_image_generate.py` を使う
5. outputs を user-visible path に保存し、何を生成したか正確に報告する

## Prompt Construction

compact な production-oriented prompts を優先する。

```text
Create a side-view fantasy inn sign for a 2D platformer. Carved wood, brass brackets, hand-painted fox emblem, warm lantern glow, readable silhouette, transparent background, no mockup, no text, centered composition.
```

style-sensitive work では矛盾する style を積まない。

- good: `1990s SNES-era platformer prop with restrained palette and crisp pixel clusters`
- bad: `hyper realistic painterly low poly anime cinematic pixel art watercolor`

iteration では silhouette、palette、camera/framing、surface detail、mood/lighting のように1軸ずつ変える。

## Cookbook Prompting Pointers

OpenAI cookbook guidance に基づく補強:

- intended use を明確にする: concept art、screenshot、icon、edit、text-heavy graphic、product render、transparent asset
- prompt structure を ordered / explicit にする
  - subject
  - environment/background
  - composition / camera / framing
  - style / materials / era
  - lighting / color treatment
  - exact constraints and exclusions
- object の placement、foreground/background、overlap、visible constraints を具体化する
- edits では change list と preserve list を両方書く
- image 内 text は exact text を引用し、短くし、placement と typography expectations を書く
- multiple reference images は `image 1 = character silhouette` のように role を label する
- iteration は prompt 全体を書き換えず、小さな controlled deltas で行う
- layout fidelity が重要なら mood board ではなく design spec として書く

## Sprite Animation Consistency

low-resolution sprite animation edits では "same character" だけでは不足する。tiny pixel characters は frame-1 size、body orientation、outline thickness、face readability、costume silhouette が drift しやすい。

sprite-strip work の stricter pattern:

1. older concept export ではなく **currently shipped in-game frame** から始める
2. shipped frame を upscaled し、slot layout に配置した transparent **reference canvas** を作る
3. frame-by-frame edits より one full-strip edit を優先する
4. best current strip から small-delta retouch を優先し、full reinterpretation を避ける
5. multi-image edits では role を明示する
   - `Image 1 = identity anchor`
   - `Image 2 = pose/layout/motion anchor`
6. what must change / what must stay unchanged を両方書く
7. side view、head size、silhouette family、palette family、outline thickness、apparent scale を preserve list に繰り返す

idle から始まる state では2つの手段がある。

- **Hard-lock on import**: gameplay が exact shipped idle frame から始まる必要があるとき有効。ただし generated frame 2 と合わないと jump が目立つ
- **Protected frame-1 edit**: visual continuity が必要なとき強い。frame 1 を edit 内で immutable にし、後続 frame だけ変更させる

practical rule:

- 問題が「real idle sprite から始まらない」なら hard-lock が役立つ
- 問題が「frame 1 と frame 2 が別 character に見える」なら hard-lock だけでは不足。surgical edit または mask を使う

Example structure:

```text
Create a portrait 16-bit pixel-art gameplay screenshot.
Subject: a pirate hero climbing a rope.
Environment: sea cave opening with dock platforms and shallow surf below.
Composition: side-view, centered hero, upward route clearly readable, HUD at top only.
Style: authentic 16-bit pixel art, 256x384 internal resolution, 4x nearest-neighbor upscale.
Lighting/color: bright coastal blues with warm stone and wood tones.
Constraints: visible pixels, limited palette, stepped shading, no glossy rendering, no collage, no poster framing.
```

## 同梱 script

生成:

```bash
OPENAI_API_KEY=... \
python3 .codex/skills/gpt-image-1-5/scripts/gpt_image_generate.py \
  --prompt "Isometric potion shop icon, transparent background, polished game asset" \
  --out-dir tmp/potion_shop --quality high --size 1024x1024 --output-format png
```

Useful flags:

- `--background transparent`
- `--n 1`
- `--filename-prefix hero`
- `--user some-trace-id`

script は `POST /v1/images/generations` を呼び、`b64_json` を decode して files を書く。

## 避けること

**generation 前に成功したと言う**

問題: user は hypothetical prompt ではなく actual image を求めている。
改善: API を実行し output file を保存してから generated と伝える。未実行なら理由を明示する。

**contradictory prompt stacks**

問題: 複数の subject、composition、style direction が競合すると adherence が落ちる。
改善: one subject、one composition、one primary style direction に整理する。

**`jpeg` で transparent background**

問題: `jpeg` は alpha を持てない。
改善: transparent assets では `png` または `webp` を使う。

**sprite sheets が保証されるふりをする**

問題: model は deterministic sheet layouts より single assets / poses / states の方が得意。
改善: sheet が必要なら review / cleanup / normalization 前提で扱い、保証しない。

**常に highest quality にする**

問題: early ideation で high quality を使うと cost と latency が増える。
改善: early ideation は `low` / `medium`、final outputs で quality を上げる。

**tiny sprites で "same character" を十分とみなす**

問題: small sprites では identity が簡単に drift する。
改善: side view、head size、outline thickness、palette family、apparent scale などの invariants を明記する。

**sequence mismatch を frame 1 の後付け置換で直そうとする**

問題: frame 2 以降が別 character なら、frame 1 だけ差し替えても motion sequence は合わない。
改善: masked / protected frame-1 edit で continuity を保つか、sequence 全体を再生成する。

**同じ seed sprite を複数 slot に並べるだけで identity anchor が強くなると仮定する**

問題: duplicate slots は model focus を強めるとは限らず、layout や identity を歪めることがある。
改善: single seeded slot や surgical retouch を試し、比較する。

## Variation Guidance

すべてを1つの house style にしない。

- prop、character、icons、scene art で prompt structure を変える
- painterly illustration、flat iconography、3D render look、pixel-inspired concept、UI-ready cutout など brief に合わせて rendering direction を変える
- random variation より context-fit を優先する。consistent set を作る場合だけ style を再利用する

## 参照

- API/model notes: `references/openai-gpt-image-1-5.md`
- Runnable generator: `scripts/gpt_image_generate.py`
- OpenAI cookbook prompting guide: https://developers.openai.com/cookbook/examples/multimodal/image-gen-1.5-prompting_guide/

## 覚えておくこと

image generation を理論ではなく実務にする。request を precise prompt にし、settings を意図して選び、可能なら API を実行し、real output path を報告する。
