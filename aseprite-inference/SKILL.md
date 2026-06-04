---
name: aseprite-inference
description: "Asepriteファイルからレイヤー、セル、タグ、パレットなどの構造を解析する。フレーム範囲や再生時間を推定し、エンジン向けJSONを作るときに使う。"
metadata:
  short-description: "Asepriteファイルからmetadataを推定"
---

# Aseprite Inference

`.ase` / `.aseprite` を、layered pixel または tilemap cel の構造化 timeline として読む。animation timing、per-frame bounds、layer hierarchy、tags、slices、tilesets、palettes などの有用な metadata を推定し、engine-ready JSON を作る。

## 考え方: 仮定より推定

Aseprite file を「真実」、実装コードを「仮説」として扱う。hard-code せず、読み取りと検証を優先する。

**推定前に確認すること:**

- 欲しいのは **authoring intent** (tags/slices/user data) か、**render intent** (visible pixels/bounds/ordering) か
- **pixels** の decode が必要か、**structure-only** (layers/timing/tags) で足りるか
- sprite は **RGBA / Grayscale / Indexed / Tilemap** のどれで、それが transparency/bounds logic に影響するか

**基本原則**

1. **chunk-driven にする**: unknown chunks は `chunk_size` で skip し、crash しない
2. **timing は per-frame として扱う**: `header.speed` は deprecated。各 frame duration を使い、必要なら fallback する
3. **decode mode を分ける**: まず fast metadata pass。pixel/tile decode は必要なときだけ
4. **推定を明示する**: わかっていることと仮定したことを両方 output する。例: indexed transparency

## Quick Start

同梱 inspector で JSON に変換する。

```bash
python3 .codex/skills/aseprite-inference/scripts/aseprite_inspect.py path/to/sprite.aseprite --json
```

tight bounds など pixel-derived inference が必要な場合だけ decode を有効にする。

```bash
python3 .codex/skills/aseprite-inference/scripts/aseprite_inspect.py path/to/sprite.aseprite --json --decode-cels
```

## 信頼して推定できること

- **Animation structure**: frame count、per-frame durations、total timeline
- **Layer model**: hierarchy、blend modes、opacities、background/reference flags、optional UUIDs
- **Cel placement**: per-frame per-layer cels、linked cels、z-index adjustments、opacity
- **Tags**: named animation ranges、playback direction、repeat behavior
- **Slices**: frame-keyed rectangles、optional 9-slice centers/pivots。hitbox/anchor に有用
- **Tilesets/tilemaps**: tile dimensions、tile count、tilemap masks (ID + flips)
- **Palettes**: indexed-color palette changes、main header の transparency index
- **User data**: layer/cel/tag/tileset に付く text/color/properties

cel pixels を decode した場合はさらに次を推定できる。

- cel/frame ごとの **tight bounds** (non-transparent extents)
- **sparsity/empty frames** の検出
- frame bounds size/variability からの sprite-sheet packing hints

## よく使うワークフロー

### 1. engine metadata (JSON) を作る

- まず structure-only で inspect し、tight bounds が必要なときだけ decode を足す
- `frames[]`, `layers[]`, `tags[]`, `slices[]`, normalized `frameMs[]` を出す
- deterministic render ordering が必要なら cel header の **z-index rules** と layer ordering を取り込む
- character grounding では slice/pivot/user-data を出しつつ、runtime offsets 固定前に exported PNG の alpha bounds を `gamedev-assets` などで確認する

### 2. "なぜ見えないか" を debug する

- layer visibility flags と opacity を確認する
- cel が別 frame に **linked** されていないか確認する
- indexed sprites では transparent index と background layer semantics を確認する

### 3. slices を hitboxes/anchors に変換する

- frame ごとの slice key から runtime hitbox を作る
- pivot があれば使い、なければ slice center などを fallback として推定する

## 避けること

**`speed` を authority とみなす**

問題: `header.speed` は deprecated で、各 frame duration が本来の timeline を表す。
改善: frame duration が zero の場合だけ compatibility fallback を適用する。

**palette が常に存在する、または常に256 entries と仮定する**

問題: palette chunks の有無や entry count は file によって違い、indexed sprites では transparency index も意味を持つ。
改善: palette chunks を parse し、indexed sprites では transparency index と background layer semantics を確認する。

**unknown chunks で hard-fail する**

問題: unknown chunk を即 failure にすると、新しい Aseprite features や custom chunks に弱い parser になる。
改善: chunk size で skip し、unknown chunk summary を debugging 用に残す。

**すべてを既定で decompress する**

問題: 不要な pixel decode は遅く、大きな sprites で memory risk を増やす。
改善: structure-only pass を先に行い、必要な cel/tile だけ decode し、大きな sprite には safety limits を置く。

**indexed pixels を RGBA とみなす**

問題: indexed cel pixels は palette indices であり、直接 RGBA と解釈すると色と transparency が壊れる。
改善: palette を parse した後だけ RGBA に変換する。

**linked cels を無視する**

問題: linked cel は別 frame の cel data を参照するため、bounds inference や duration analysis がずれる。
改善: post-pass で link を解決してから bounds や emitted metadata を確定する。

**layer UI grouping を render grouping と同一視する**

問題: group compositing は header flags、blend mode、opacity rules に依存し、UI tree だけでは render order を決められない。
改善: layer hierarchy と render flags / opacity / blend rules を分けて出力する。

**authoring intent と render intent を混同する**

問題: tags、slices、user data は authoring intent、pixels / bounds は render intent で、別の事実を表す。
改善: 両方を出し、runtime offset などは final exported PNG alpha bounds で検証する。

## Variation Guidance

- game engine では、最小 timing+tags から full per-layer/per-cel metadata まで schema を用途で変える
- debugging では chunk dump style、runtime では compact normalized JSON を優先する
- tilemaps では target に応じて tile usage summaries と full per-cell tile streams を使い分ける

## References & Scripts

- Script: `scripts/aseprite_inspect.py` (binary parser + JSON。optional cel/tile decode)
- Reference: `references/aseprite-format-cheatsheet.md` (chunk map + gotchas)
- Reference: `references/inference-recipes.md` (bounds/timing/order を安全に計算する方法)

## 覚えておくこと

この領域では精度が重要。

- indexed transparency handling、bounds derived from pixels vs dimensions など、仮定を明示する output を優先する
- chunk-driven parsing、strict bounds checks、optional decode passes で production-grade Aseprite tooling を作る

## 期待値

- 新しい chunk types に強く、malformed input に対して安全な parser を目指す
- 根拠を file data から説明できない賢すぎる推定より、事実を正直に表す JSON を優先する
