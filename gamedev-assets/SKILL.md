---
name: gamedev-assets
description: "2Dゲーム向けPNGアセットを監査・整理する。スプライトシート、タイルセット、タイルマップ、マニフェスト、寸法、差分オーバーレイ、欠落素材の調査で使う。"
---

# Gamedev Assets

`scripts/` の同梱 script を使い、game art pipeline を一貫性があり debug 可能な状態に保つ。

## Asset Index の学び

asset-index convention を作るときは、自分の repo に短い worked example doc を残す。この repo では Love2D asset index 構築の実践メモが `docs/asset-index-learnings.md` にある。

manifest を作るときの要点:

- Love2D では Lua table のような **native** manifest format を使ってよいが、export しやすい **JSON-shaped** 構造にする
- size だけでなく、使い方で分類する: `backgrounds`、`tilesets`、`images`、`spritesheets`
- tileset では最初に tile size を決める。例: `16x16` なら `columns/rows` を導出する
- sprite sheets は sparse として扱い、full grid 前提ではなく alpha-based non-empty `{col,row}` frames を保存する
- key は stable / sanitized、`path` は case と spaces を含む on-disk truth として保持する
- asset 変更後は coverage check を必ず走らせる

## Animation Normalization の学び

AI-generated sprite strips や extracted video frames を game-sized animation frames に入れるとき:

- target size reference は1つの approved in-game frame にする
- placement は metadata 由来の shared runtime anchor を使う
- sequence 全体に one shared scale を使う。frame ごとに scale しない
- attack / hurt など tall poses が混ざる state では `median-lower`、crouch など first frame が idle-like standing なら `first-frame` を scaling reference にする
- video-frame imports は full frame set の union crop を計算し、全 frame に同じ crop box を使う
- fixed center + fixed bottom または known runtime anchor で align する。local silhouette ごとの recenter は drift を生む

理由:

- per-frame crop/alignment は sideways drift や "skating" を作りやすい
- per-frame scaling は raised weapons / hurt reactions など tall poses を縮める
- 多くの animation 問題は import 時の registration 問題
- source video の全 frame を残すと、usable game loop ではなく repeated cycles になりやすい

practical rule:

- sequence framing を先に保つ
- normalize はその後
- collision/body bounds は normalized export 後に導く

explicit scaling modes を持つ strip importer では次を優先する。

- upward pose variation がある attack、hurt などは `median-lower`
- frame `01` が idle-like standing で、後続 frame が短く見えるべき crouch / enter-and-lower state は `first-frame`

video-derived animation では特に次の順序にする。

1. motion を明確に確認したい場合は、まず dense extraction を使う
2. その dense sequence を one shared crop、one shared scale、one shared anchor で normalize する
3. その結果を analysis material として扱う
4. runtime asset には clean loop cycle を1つ curate する

この repo の run-animation 実験では、次の区別が重要だった。

- dense import は診断に向く
- curated single-cycle export は実際の game asset に向く

animation が "skating" している、または横に滑っているように見える場合は、この順序で確認する。

1. frames が independently cropped されていないか
2. frames が independently centered されていないか
3. tall poses が short poses と違う scale になっていないか
4. source motion 自体に true root-motion drift が含まれていないか

character が **shadow から浮いている**、または direction ごとに立ち位置の高さが違う場合は visible alpha bounds を確認する。

1. 各 frame の lowest non-transparent pixel を測る
2. directions / states 間で bottom baseline を比較する
3. PNG frames を normalize して feet が shared baseline に着くようにする。一般的には `bottomY = frameHeight - 1`
4. その後で engine-side sprite origin や shadow offsets を調整する

foot placement が悪い場合、asset manifest を最初の修正先にしない。manifest は frame size、atlas size、frame count、fps、pivot metadata を記述できるが、PNG 内の transparent padding は直せない。まず runtime spritesheet を直す。nearest-neighbor import 後も pose が soft に見える場合、その softness は source frames に既に含まれていることが多い。

## Asset Index Theory

asset index / manifest は game art の single source of truth。centralized loading、frame metadata、disk/code validation を可能にする。

### Output Formats

- **JSON**: engine 依存が少なく推奨
- **Lua table**: Love2D など Lua projects

### Asset Categories

| Category | Purpose | Key metadata |
|----------|---------|--------------|
| `backgrounds` | parallax/scrolling layers、static backdrops | `path`, `width`, `height` |
| `tilesets` | grid-based level tiles | `path`, `tileWidth`, `tileHeight`, `columns`, `rows`, `margin`, `spacing` |
| `images` | static sprites | `path`, `width`, `height` |
| `spritesheets` | animated sprites | `path`, `frameWidth`, `frameHeight`, `fps`, `frames` or `animations` |

### Manifest Structure

```json
{
  "meta": {
    "version": 1,
    "root": "assets/game",
    "defaultFps": 10
  },
  "backgrounds": {
    "clouds": { "path": "Backgrounds/clouds.png", "width": 256, "height": 128 }
  },
  "tilesets": {
    "desert": {
      "path": "Tilesets/desert.png",
      "width": 192,
      "height": 96,
      "tileWidth": 16,
      "tileHeight": 16,
      "columns": 12,
      "rows": 6
    }
  },
  "images": {
    "deco": {
      "bush": { "path": "Deco/bush.png", "width": 32, "height": 16 }
    }
  },
  "spritesheets": {
    "enemies": {
      "chicken": {
        "path": "Enemies/chicken.png",
        "width": 224,
        "height": 64,
        "frameWidth": 32,
        "frameHeight": 32,
        "columns": 7,
        "rows": 2,
        "animations": {
          "idle": { "fps": 6, "frames": [[0, 0], [1, 0]] },
          "run": { "fps": 10, "frames": [[0, 1], [1, 1], [2, 1], [3, 1]] }
        }
      }
    }
  }
}
```

### Frame Coordinates

frame は sprite sheet grid 内の `[column, row]` pair として参照する。

- **zero-based indexing**: 最初の cell は `[0, 0]`
- **grid defined by frame dimensions**: `frameWidth x frameHeight` で image を分割する
- **sparse sheets**: すべての cell に content がない場合は explicit `frames` array を使う
- **named animations**: frame sequence と timing は `animations` object にまとめる

### Workflow: Building an Asset Index

1. **Inventory**: `asset_sizes.py` で PNG dimensions を取得
2. **Probe sheets**: `asset_sheet_probe.py --frame WxH --list` で non-empty cells を調べる
3. **Categorize**: background、tileset、static image、spritesheet を分類
4. **Define animations**: frame sequences と fps を決める
5. **Write manifest**: JSON または Love2D 向け Lua
6. **Validate**: `asset_manifest_check.py` で manifest と disk を照合

## Quick Start (`uv` 推奨)

repo root から実行する。

```bash
# 1) Check manifest coverage (manifest ↔ disk)
uv run .codex/skills/gamedev-assets/scripts/asset_manifest_check.py --manifest path/to/assets_index.lua --root assets

# 1b) Export Lua manifest to portable JSON (recommended for non-Lua engines/tools)
uv run .codex/skills/gamedev-assets/scripts/asset_manifest_export_json.py --manifest path/to/assets_index.lua --out path/to/assets_index.json

# 2) List PNG sizes
uv run .codex/skills/gamedev-assets/scripts/asset_sizes.py --root assets --json tmp/asset_sizes.json

# 3) Probe sprite sheet for non-empty frames
uv run .codex/skills/gamedev-assets/scripts/asset_sheet_probe.py path/to/sheet.png --frame 32x32 --list --json tmp/probe.json

# 3b) Audit/fix visible foot baselines inside sprite frames
uv run .codex/skills/gamedev-assets/scripts/asset_sprite_baseline.py assets/characters --frame 256x256 --json tmp/baselines.json
uv run .codex/skills/gamedev-assets/scripts/asset_sprite_baseline.py assets/characters --frame 256x256 --target-bottom 255 --out-dir tmp/baseline-fixed

# 4) Debug tilesets / tilemaps with a manifest-driven GUI editor
uv run .codex/skills/gamedev-assets/scripts/asset_tilemap_editor.py --manifest path/to/assets_index.json
```

`uv` なしなら Python 3.11+ と Pillow が必要。同梱 Python scripts は PEP 723 metadata を含むため、`uv run <script.py>` で dependencies が自動 install される。

## Asset Index Export (Lua -> JSON)

```bash
uv run .codex/skills/gamedev-assets/scripts/asset_manifest_export_json.py \
  --manifest path/to/assets_index.lua \
  --out path/to/assets_index.json
```

exporter は既定で `path` を output manifest folder からの相対 path に書き換え、`meta.root` を `"."` にする。copy/zip 後も動く manifest になる。

## Tilemap Debugging (Python tileset/tilemap editor)

manifest-driven editor で次を確認する。

- `tileWidth` / `tileHeight`、`columns` / `rows`
- cursor movement が keypress ごとに exactly 1 cell
- JSON tilemap の save/load が同じ layout を保つ

```bash
uv run .codex/skills/gamedev-assets/scripts/asset_tilemap_editor.py --manifest path/to/assets_index.json
```

注意: この GUI は `tkinter` を使う。`tkinter` は Python distribution / OS が提供するもので、`uv` / pip で install されるものではない。

headless exports:

```bash
# tileset の grid-overlay PNG を export
uv run .codex/skills/gamedev-assets/scripts/asset_tilemap_editor.py \
  --manifest path/to/assets_index.json --tileset <tileset_name> \
  --export-tileset-grid tmp/tileset_grid.png --label-ids --scale 6 --trim

# all non-empty tiles を in-place にした self-test tilemap を生成して render
uv run .codex/skills/gamedev-assets/scripts/asset_tilemap_editor.py \
  --manifest path/to/assets_index.json --tileset <tileset_name> \
  --make-selftest-map tmp/selftest.json

uv run .codex/skills/gamedev-assets/scripts/asset_tilemap_editor.py \
  --manifest path/to/assets_index.json --map tmp/selftest.json \
  --export-map-render tmp/selftest.png --scale 6 --trim

# 任意: concept mockup 用に背景色と tile 背面の fill rectangles を設定
uv run .codex/skills/gamedev-assets/scripts/asset_tilemap_editor.py \
  --manifest path/to/assets_index.json --map tmp/selftest.json \
  --export-map-render tmp/selftest_bg.png --scale 6 --bg '#77cfd8' --fill-rect '0,40,24,6,#12a7d5'
```

controls:

- arrows: cursor
- `WASD`: palette selection
- `Space/Enter`: paint、`X/Backspace`: erase
- `[` / `]`: tileset、`+/-`: zoom
- `F5`: quick-save、`F9`: quick-load
- `G`: grid、`H`: help

## Scene Reconstruction

reference PNG が tiles/backdrops から組まれており、tileset + tilemap で再構築したいときに使う。row-by-row で iterate し、deterministic renders と diff overlays で確認する。

詳細 heuristics は `references/tilemap_to_reference.md`、autofill tuning は `references/autofill_notes.md`。

**Workflow (manifest-driven, engine-agnostic)**

1. Lua から始める場合は `assets_index.json` を export / prepare する。

```bash
uv run .codex/skills/gamedev-assets/scripts/asset_manifest_export_json.py \
  --manifest path/to/assets_index.lua \
  --out tmp/assets_index.json
```

2. reference image に tiles ではない background layers が含まれる場合は、任意で backdrop を compose する。

```bash
uv run .codex/skills/gamedev-assets/scripts/tile_backdrop_compose.py \
  --layers path/to/layer0.png path/to/layer1.png path/to/layer2.png \
  --out tmp/backdrop.png --scale 6 --out-scaled tmp/backdrop_x6.png
```

3. tile-aligned reference を prepare する。downscale と grid overlay を作る。

```bash
uv run .codex/skills/gamedev-assets/scripts/tile_reference_prepare.py \
  --reference path/to/reference.png --downscale 6 \
  --tile 16 --grid-cols 18 --grid-rows 11 --grid-origin-y 0 \
  --out-small tmp/ref_small.png --out-grid tmp/ref_grid.png --out-grid-scaled tmp/ref_grid_x6.png
```

4. manual fixes 用の quick tile picker として tileset ID sheet を生成する。

```bash
uv run .codex/skills/gamedev-assets/scripts/tile_tileset_ids.py \
  --tileset path/to/tileset.png --tile 16 --scale 6 --out tmp/tileset_ids.png
```

5. base layered map JSON を作る。この file と step files を継続的に編集する。

```json
{
  "meta": {
    "gridWidth": 18,
    "gridHeight": 11,
    "tileOriginX": 0,
    "tileOriginY": 0,
    "canvasWidth": 288,
    "canvasHeight": 180,
    "layerOrder": ["background", "ground", "foreground"]
  },
  "layers": {
    "background": [[0,0],[0,0]],
    "ground": [[0,0],[0,0]],
    "foreground": [[0,0],[0,0]]
  }
}
```

6. debug overlay、diff、mismatched-tile highlighting 付きで step を render する。

```bash
uv run .codex/skills/gamedev-assets/scripts/tilemap_render_step.py \
  --manifest tmp/assets_index.json --root assets --tileset your_tileset_key \
  --map path/to/recreation_map.json --steps path/to/steps --step 11 \
  --backdrop tmp/backdrop.png --reference path/to/reference.png --scale 6 \
  --out-prefix tmp/recon_step11 --write-diff --write-diff-tiles-debug \
  --diff-threshold 6 --diff-tile-threshold 6
```

outputs:

- `*_render.png`: clean render
- `*_debug.png`: map coords + tile IDs + tileset coords（狙った修正用）
- `*_diff.png`: 不一致 pixel を示す reference 色の overlay
- `*_diff_tiles_debug.png` + `*_diff_tiles.json`: 不一致 tile cell の outlines と `{x,y}` リスト

resolved indices を `asset_tilemap_editor.py` で読み込める `tilemap.json` として書きたい場合は、次を追加する。

```bash
  --out-tilemap tmp/tilemap.json
```

optional row autofill:

```bash
uv run .codex/skills/gamedev-assets/scripts/tilemap_autofill_row.py \
  --manifest tmp/assets_index.json --root assets --tileset your_tileset_key \
  --map path/to/recreation_map.json --steps path/to/steps --base-step 3 \
  --reference-small tmp/ref_small.png --backdrop tmp/backdrop.png \
  --row 10 --layer ground --min-improve 1.0 --out-step path/to/steps/step_04.json
```

review GIFs:

```bash
uv run .codex/skills/gamedev-assets/scripts/make_gifs.py \
  --frames 'tmp/*step*_debug.png' --out tmp/steps_debug.gif \
  --diff-frames 'tmp/*step*_diff.png' --out-diff tmp/steps_diff.gif
```

## No tilemap? Generate `tilemap.json` from a reference (best-effort)

tilemap がまだない場合は、次から first-pass `tilemap.json` を直接生成できる。

- tileset (`assets_index.json` 経由)
- reference image
- できれば backdrop

これは naive brute-force matching なので、reference に non-tile pixels がある場合は完全でない、または解けない場合がある。debug/diff tools で mismatch を直すための bootstrap として扱う。

```bash
uv run .codex/skills/gamedev-assets/scripts/tilemap_from_reference.py \
  --manifest tmp/assets_index.json --root assets --tileset your_tileset_key \
  --reference path/to/reference.png \
  --backdrop-layers path/to/bg0.png path/to/bg1.png path/to/bg2.png \
  --out-dir tmp/recon_out --min-improve 1.0
```

outputs:

- `tmp/recon_out/tilemap.json`: indices
- `tmp/recon_out/steps/step_*.json`: refine できる placements

## Tilemap Debugging (Love2D test scenes)

engine 内で tile sizes / tileset grids が合わない場合は、この repo の built-in Love2D scenes で検証する:

- tileset grid math（tileW/tileH、columns/rows、margin/spacing）
- cursor が keypress ごとに正確に 1 cell 動くこと
- 保存した `.lua` map が同一に load し直せること

repo root から実行:

```bash
love .
```

Controls:

- `1` Tileset Inspector: arrows で selection cell を1つずつ移動、`[`/`]` で tileset 切替、`g` で grid、`+/-` で zoom
- `2` Tilemap Editor:
  - arrows で map cursor を1 cell ずつ移動
  - `WASD` で tileset sheet 上の palette（選択 tile）を移動
  - `Space/Enter` で paint、`X/Backspace` で erase
  - `Ctrl+S` quick-save、`Ctrl+L` quick-load（`F5`/`F9` も可）
  - 保存した map は Love の save directory 内の `maps/` に出力される（保存後に表示）

## Tools

### `asset_manifest_check.py`

manifest と disk の PNG が相互に揃っているか検証する。

```bash
uv run .codex/skills/gamedev-assets/scripts/asset_manifest_check.py
uv run .codex/skills/gamedev-assets/scripts/asset_manifest_check.py --json tmp/coverage.json
```

### `asset_manifest_export_json.py`

`assets_index.lua` を `assets_index.json` に export する（engine/tooling 間で portable）。

```bash
uv run .codex/skills/gamedev-assets/scripts/asset_manifest_export_json.py --manifest path/to/assets_index.lua --out path/to/assets_index.json
```

### `asset_sheet_probe.py`

sprite sheet grid の non-empty cells を探す。

```bash
uv run .codex/skills/gamedev-assets/scripts/asset_sheet_probe.py image.png --frame 32x32
uv run .codex/skills/gamedev-assets/scripts/asset_sheet_probe.py folder/ --frame 16x16 --list --json tmp/probe.json
```

### `asset_sprite_baseline.py`

spritesheet grid 内の visible alpha bounds を audit し、baseline-corrected copies を書ける。

使う場面:

- direction ごとに shadow から浮く
- directional idle が attack frame 由来
- AI sheets の feet 下 transparent padding が不統一
- engine origins は正しいが visual foot placement が違う

```bash
# frame ごとの alpha bounds、visible bottom pixel、必要な shift を報告する。
uv run .codex/skills/gamedev-assets/scripts/asset_sprite_baseline.py public/assets/kaede --frame 256x256 --json tmp/kaede-baselines.json

# visible な feet が y=255 に来る修正コピーを書き出す。
uv run .codex/skills/gamedev-assets/scripts/asset_sprite_baseline.py public/assets/kaede --frame 256x256 --target-bottom 255 --out-dir tmp/kaede-baseline-fixed

# source が idle/standing 想定のときは、任意で horizontal center も正規化する。
uv run .codex/skills/gamedev-assets/scripts/asset_sprite_baseline.py public/assets/kaede/idle-n.png --frame 256x256 --target-bottom 255 --target-center-x 128 --out tmp/idle-n-fixed.png
```

この script は animation quality を判断するものではなく、final PNG frames が engine の sprite-origin / shadow assumptions と一致するかを検証する runtime export guardrail。

### `asset_sizes.py`

folder 配下のすべての PNG の dimensions を取得する。

```bash
uv run .codex/skills/gamedev-assets/scripts/asset_sizes.py
uv run .codex/skills/gamedev-assets/scripts/asset_sizes.py --root assets/ --json tmp/sizes.json
```

### `asset_tilemap_editor.py`

tiles を選択して grid を描き、tileset の前提を検証する GUI tool。

```bash
uv run .codex/skills/gamedev-assets/scripts/asset_tilemap_editor.py --manifest path/to/assets_index.json
```
