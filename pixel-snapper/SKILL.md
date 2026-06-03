---
name: pixel-snapper
description: "ピクセルアートPNGのクリーンアップと変換を行う。アップスケール画像やAI生成の擬似ピクセルアートから隠れたネイティブピクセルグリッドを復元し、Sprite Fusionのグリッドスナップ、固定キャンバスでのフレーム一括ピクセル化、パレット量子化、寸法・パス対応・RGB色数・アルファ保持の検証を扱う。pixelate、dot-art、pixel-snap、擬似ピクセルアート整理、AIピクセルアート整理、既知レイアウトのスプライトシート、アニメーションフレーム一括処理、固定フレームサイズ、ゲーム用ピクセル素材が必要なときに使う。"
---

# Pixel Snapper

## Purpose

Turn raster images that look like pixel art into usable pixel-art assets. Use the right path for the asset: recover a hidden low-resolution grid, run Sprite Fusion's grid snapper, or preserve a fixed animation canvas while pixelating and quantizing frames.

## Operating Model

Pixel-art cleanup is not one operation. Choose the workflow by the output contract:

| Need | Use | Output Size |
|------|-----|-------------|
| Recover the native grid from upscaled or AI-faked pixel art | `scripts/pixel_snapper.py` | Discovered from the source |
| Recover frames from a sheet with known rows/columns | `scripts/pixel_snapper_sheet.py` | Discovered per frame, then reassembled |
| Use Hugo-Dz/Sprite Fusion grid snapping on a single image, tile, map, texture, or sample | `scripts/spritefusion_snapper.py` | Derived by upstream; padded to source aspect by default |
| Convert animation frames while keeping one canvas size and stable character scale | `scripts/fixed_canvas_pixelate.py` | Explicit `--size N` or `--size WxH` |
| Validate batch dimensions, visible RGB palette, and alpha behavior | `scripts/inspect_png_batch.py` | Report/fail based on invariants |

Prioritize:

1. Correct asset contract: native-grid discovery for exploratory cleanup, fixed canvas for game animation.
2. Visual readability: smallest palette that preserves the design.
3. Alpha integrity: preserve soft alpha unless the user explicitly asks for hard-edged cutouts.
4. Reproducibility: keep originals and write experiments to new output paths before promoting assets.

## Reference Files

| Topic | File | Use When |
|-------|------|----------|
| Native grid recovery algorithm | [algorithm.md](references/algorithm.md) | Debugging hidden-grid recovery or changing internal tunables |
| Native grid examples | [usage-examples.md](references/usage-examples.md) | Running sweeps, upscales, and known-layout sheet recovery |
| Sprite Fusion upstream | [spritefusion-upstream.md](references/spritefusion-upstream.md) | Needing exact upstream CLI, verified commit, or WASM details |

## Before Starting

Answer these before final conversion:

- Is the input fake/upscaled pixel art, already-native pixel art, a continuous-tone image, or a game animation batch?
- Is output size allowed to be discovered, or must every frame have a fixed size and stable in-game scale?
- Is this a single image, a folder of PNG frames, or a spritesheet with known rows/columns?
- What color count is desired? For AI native-grid recovery, start near `256`; for strict retro cleanup compare `8`, `16`, and `32`.
- Does the source use soft alpha? If yes, preserve alpha levels by default.

Ask a short tradeoff question before a final batch conversion when the mode is unclear:

```text
Which tradeoff should I optimize?
1. Native/Sprite Fusion grid-snap: prioritize visual grid cleanup; output dimensions may vary by image.
2. Fixed-canvas animation output: keep every frame the same size with stable character scale.
3. Build comparison samples from representative frames first.
```

Proceed without asking when the user supplied the mode, output path, size/color requirements, or when the task is a single image where discovered output dimensions are clearly acceptable.

## Workflow

1. Classify the asset and output contract. Do not run grid-derived batch output as final animation frames unless varying dimensions and offsets are acceptable.
2. Record source facts: file count, PNG dimensions, rows/columns for known sheets, visible alpha behavior, and intended output path.
3. Choose the script:
   - Hidden grid from fake/upscaled pixel art: `pixel_snapper.py`.
   - Known-layout sheet: `pixel_snapper_sheet.py`.
   - Sprite Fusion grid cleanup where grid-derived output is acceptable: `spritefusion_snapper.py`.
   - Fixed-size frame batch: `fixed_canvas_pixelate.py`.
4. Choose palette size. For unknown style, create representative samples rather than guessing.
5. Calibrate on one or a few representative frames before a full batch.
6. Run final conversion into a new output path. Avoid overwriting source assets.
7. Verify with checks matched to the chosen workflow, then compare visually against the source.

## Commands

Recover a hidden native grid from an AI or upscaled pixel-art PNG:

```bash
uv run "<skill>/scripts/pixel_snapper.py" "input.png" "output.png" --k-colors 256
```

Recover a known-layout spritesheet:

```bash
uv run "<skill>/scripts/pixel_snapper_sheet.py" \
  "sheet.png" "sheet-snapped.png" --cols 4 --rows 4 --k-colors 256
```

Run Sprite Fusion grid snapping on one image:

```bash
python3 "<skill>/scripts/spritefusion_snapper.py" \
  --input "input.png" --output "output.png" --colors 16
```

Override Sprite Fusion grid size only after auto-detection fails:

```bash
python3 "<skill>/scripts/spritefusion_snapper.py" \
  --input "input.png" --output "output.png" --colors 16 --pixel-size 8
```

Generate fixed-canvas animation frames:

```bash
python3 "<skill>/scripts/fixed_canvas_pixelate.py" \
  --input-dir "input_frames" --output-dir "output_frames" --size 512 --colors 16
```

Verify a fixed-frame output batch:

```bash
python3 "<skill>/scripts/inspect_png_batch.py" \
  --root "output_frames" \
  --source-root "input_frames" \
  --require-single-size \
  --max-visible-rgb 16
```

## Animation Frame Contract

For character animations, frame sequences, action folders, or spritesheet-derived frames:

- Source frame count must match output frame count.
- Relative paths should match unless the user requested a new structure.
- Required output frame dimensions must be known before final batch conversion.
- All final frame PNGs must have the same dimensions when used as fixed-frame animation assets.
- Character scale must come from the original source canvas, not per-image visible bounds.
- Do not crop to visible pixels unless the user accepts anchor/offset handling.
- Preserve soft alpha by default; use hard alpha only when requested.
- Validate visible RGB colors separately from RGBA values because one RGB color can appear at many alpha levels.

If the user asks for "low-resolution pixel art" and game-ready animation frames, prefer fixed-canvas pixelation over raw grid snapping unless the engine has deliberate per-frame offsets and anchors.

## Verification

For single-image native or Sprite Fusion output:

- Check that the output dimensions are plausible, not just nonzero.
- Inspect a nearest-neighbor upscale at `x8` or `x16`.
- Compare source and output side by side.
- Re-run from the original source when changing color count or grid parameters.

For frame batches:

- Run `inspect_png_batch.py` with `--require-single-size` when fixed frames are required.
- Confirm source/output file count and relative path parity.
- Confirm visible RGB count is at or below the requested palette size.
- Confirm soft alpha was not collapsed to one opaque alpha value unless requested.

## Anti-Patterns

**Treating pixel snapping as a generic downscaler**

Bad: Run a hidden-grid snapper on a photograph, painting, or smooth illustration.

Better: Use pixel snapping only when a grid-like pixel-art structure exists. Use normal resizing for continuous-tone images.

**Trying to set native-grid output resolution**

Bad: Ask `pixel_snapper.py` for a specific width/height.

Better: Snap first to recover the native grid, then nearest-neighbor upscale to the needed multiple.

**Shipping raw grid-derived output as animation frames**

Bad: Batch Sprite Fusion outputs and assume equal frame dimensions.

Better: Calibrate, inspect dimensions, and use fixed-canvas pixelation when frame size and character scale must remain stable.

**Flattening alpha during palette cleanup**

Bad: Convert soft transparent edges into opaque black or hard halos.

Better: Preserve alpha, and inspect visible RGB counts separately from alpha levels.

**Re-snapping derivative outputs**

Bad: Run snapper output through another snapper pass.

Better: Keep the original source and re-run one workflow from that source with adjusted settings.

## Troubleshooting

| Symptom | Likely Cause | First Fix |
|---------|--------------|-----------|
| Native output is exactly `64x64` | Hidden-grid detection fell back | Try different `--k-colors`; reject if no real grid exists |
| Output is tiny or missing detail | Palette collapsed too much signal | Increase color count |
| Output is too noisy or close to source size | Too many colors preserved edge noise | Decrease color count |
| Sprite Fusion output aspect changed | Upstream generated unequal grid counts | Keep default aspect padding; avoid `--no-preserve-aspect` |
| Animation frames vary in size | Grid-derived output was used for fixed-frame assets | Regenerate with `fixed_canvas_pixelate.py` |
| Output has dark halos | Alpha was flattened or palette used near-transparent RGB | Regenerate while preserving alpha; inspect alpha levels |
