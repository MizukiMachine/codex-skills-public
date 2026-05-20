---
name: spritefusion-pixel-snapper
description: Use Sprite Fusion Pixel Snapper to convert or clean raster images into grid-snapped pixel art PNGs, and use the fixed-canvas workflow for animation frame batches that need consistent frame dimensions or sprite scale. Trigger this skill when the user asks to pixelate, dot-art, pixel-snap, clean AI-generated pixel art, quantize colors for pixel art, convert animation frames, preserve fixed frame dimensions, or run Hugo-Dz/spritefusion-pixel-snapper on an image.
---

# Sprite Fusion Pixel Snapper

## Purpose

Use Hugo-Dz/spritefusion-pixel-snapper as the processing engine for raster images. The tool snaps source pixels to a regular grid and quantizes colors into a strict palette, which is especially useful for AI-generated pixel art, tilemaps, isometric maps, 2D game assets, and textures.

## Operating Model

Sprite Fusion Pixel Snapper is a grid-snapper, not a fixed-resolution image resizer. Upstream output dimensions are derived from the detected grid cell count: one output pixel per detected cell. Different images can produce different output sizes even when their source canvases match. The wrapper's `--preserve-aspect` only pads the final PNG to keep the input aspect ratio; it does not guarantee a specific absolute size such as `512x512`, nor does it guarantee that animation frames keep a consistent character scale.

For animation frames, sprites, and game assets, treat frame dimensions as a contract. If the source frames share a fixed canvas and the user needs consistent in-game scale, preserve the whole source canvas at one uniform scale or use a fixed-canvas post-process. Do not accept raw upstream batch output as final until all frame dimensions and relative paths have been verified.

Transparency is also part of the visual contract. For PNG sprites, RGB palette size and alpha preservation are separate concerns: an output can be correctly reduced to `8` RGB colors while still retaining many alpha values for soft edges. Do not flatten, premultiply, or hard-mask alpha unless the user explicitly asks for that look. If a source has many nonzero alpha levels but the output has only `A=255` for visible pixels, treat that as a failed conversion because it can turn transparent dark edge pixels into opaque black halos.

## Intent Gate

Before generating final outputs, establish what the user wants the conversion to optimize. Do not infer this silently for batches, animation frames, character sprites, or other assets that may be used in a game runtime.

If the requested mode is not explicit, ask a short question before final processing:

```text
どちらを優先しますか？
1. Sprite Fusion grid-snap: グリッド補正の見た目優先。出力サイズは画像ごとに変わる可能性あり。
2. Fixed-canvas animation output: 全フレーム同じサイズ・同じキャラスケール優先。
3. まず代表フレームで比較サンプルを作る。
```

Ask only for missing parameters needed by the chosen mode:

- For Sprite Fusion grid-snap: color count and output path.
- For fixed-canvas animation output: color count, output path, and target frame size such as `512` or `512x512`.
- For comparison samples: representative source frame(s), color counts to compare, and sample output path.

Proceed without asking only when the user already specified the mode and all required parameters, or when the task is a single image where grid-derived output size is clearly acceptable.

## Workflow

1. Run the Intent Gate before final conversion. Ask the mode question when the desired tradeoff is unclear.
2. Use the provided input and output paths. Ask when either path is missing or ambiguous. Prefer PNG output.
3. Classify the asset before conversion:
   - Single images, textures, maps, and cleanup samples may use upstream's natural grid-derived output size.
   - Animation frames, character sprites, action folders, frame sequences, and spritesheet inputs require a dimension contract before batch conversion.
   - If fixed frame size or consistent character scale matters, ask for or infer the target output canvas size and make the output path explicit. Prefer writing to a new directory instead of overwriting source assets.
4. Choose `k_colors` before final processing:
   - If the user specified a color count, use that value.
   - If the color count is missing, ask before running final or batch conversion. Offer `8` for stronger retro styling, `16` for balanced pixel-art detail, and `32` when preserving shading matters.
   - If the user is unsure, create comparison samples from a representative image at `8`, `16`, and `32` colors, then ask which setting to use for the remaining images.
   - Use `16` only when the user explicitly accepts the default or asks you to proceed without choosing.
5. For single-image work, use auto-detected pixel size first. Add `--pixel-size N` only if the output grid is wrong.
6. For animation or frame-sequence work, run a calibration pass before final batch conversion:
   - Count source images and inspect source PNG dimensions.
   - Convert representative frames from different actions/views.
   - Inspect output dimensions and alpha behavior, not only visual quality.
   - If source PNGs have multiple nonzero alpha values, the representative outputs should also preserve multiple alpha values unless the user explicitly requested hard edges.
   - If representative outputs differ in size, raw upstream output is not acceptable for fixed-frame animation assets.
7. Run the appropriate script only after the expected output contract is clear:
   - Use `scripts/pixel_snapper.py` for single images or batches where grid-derived output dimensions are acceptable.
   - Use `scripts/fixed_canvas_pixelate.py` for animation frames that need fixed frame dimensions and consistent sprite scale. This fixed-canvas script preserves the source canvas at one uniform scale and quantizes colors; it does not run the upstream grid walker.
8. Keep the wrapper's default aspect-ratio preservation enabled unless the user explicitly asks for raw upstream dimensions. The wrapper pads the PNG canvas with transparent pixels when the upstream grid would change the input aspect ratio.
9. Inspect the output:
   - For single images, verify the grid is neither too coarse nor too fine; rerun with `--pixel-size N` if needed.
   - For frame batches, verify file count, relative path parity, unique frame dimensions, RGB color count among visible pixels, and alpha preservation. If `unique frame dimensions != 1` when fixed frames are required, treat the batch as failed and regenerate with a fixed-canvas workflow.

## Failure-Proof Batch Flow

Use this flow before producing or replacing a full animation asset set:

```text
classify asset
  -> record source count, dimensions, RGB count, alpha count
  -> choose fixed canvas size and color count
  -> generate one action/view sample in a new output directory
  -> verify sample:
       file count matches
       all dimensions match target
       visible RGB colors <= requested color count
       alpha is preserved when source has soft alpha
       preview source/output on the same background
  -> only then run full batch
  -> verify the full batch with the same checks
```

Do not proceed from sample to full batch if any invariant fails. Do not overwrite a known-good output until the new output passes validation.

## Animation Frame Contract

Use this contract whenever the input is a character animation, frame sequence, or spritesheet source:

- Source frame count must match output frame count.
- Relative paths should match unless the user explicitly asks for a new structure.
- Source frame dimensions should be recorded before conversion.
- Required output frame dimensions must be known before final batch conversion.
- All final frame PNGs must have the same dimensions.
- Character scale must come from the original source canvas, not from per-image content bounds.
- Do not crop to the visible character unless the user explicitly asks for trimmed frames and accepts anchor/offset handling.
- Alpha channel behavior must be intentional. Preserve soft alpha by default; use a hard alpha threshold only when the user explicitly wants crisp cutout edges.
- Validate RGB colors among pixels with `alpha > 0` separately from RGBA colors. Many RGBA values can be correct when one RGB palette color appears at many alpha levels.

If the user asks for "low-resolution pixel art" but also needs game-ready animation frames, a fixed-canvas downscale plus palette quantization may be more appropriate than raw upstream grid snapping. In that case, state that Sprite Fusion's grid-derived output is unsafe for fixed-frame animation and use a fixed-canvas pipeline while preserving the source directory structure.

## Quick Commands

Run a fixed-canvas animation batch after the user chooses the target size and color count:

```bash
python3 "<skill>/scripts/fixed_canvas_pixelate.py" --input-dir "input_dir" --output-dir "output_dir" --size 512 --colors 16
```

Run after the user chooses a 16-color palette:

```bash
python3 "<skill>/scripts/pixel_snapper.py" --input "input.png" --output "output.png" --colors 16
```

Inspect PNG dimensions in a batch:

```bash
python3 - <<'PY'
from pathlib import Path
import struct
root = Path("output_dir")
counts = {}
for p in root.rglob("*.png"):
    if "spritesheets" in p.parts:
        continue
    data = p.read_bytes()
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        size = struct.unpack(">II", data[16:24])
        counts[size] = counts.get(size, 0) + 1
print("unique sizes", len(counts))
for size, count in sorted(counts.items()):
    print(size, count)
PY
```

Check source/output path parity:

```bash
out="output_dir"
comm -3 \
  <(find "input_dir" -type f -iname '*.png' -printf '%P\n' | sort) \
  <(find "$out" -path "$out/spritesheets" -prune -o -type f -iname '*.png' -printf '%P\n' | sort)
```

Inspect RGB palette count and alpha preservation in a PNG batch:

```bash
python3 "<skill>/scripts/inspect_png_batch.py" \
  --root "output_dir" \
  --source-root "input_dir" \
  --require-single-size \
  --max-visible-rgb "<requested_color_count>"
```

With `--source-root`, the inspector reads the first matching source files by default (`--source-check-limit 8`) to detect whether the source set uses soft alpha, then fails outputs that collapse visible pixels to one alpha level. Use `--source-check-limit 0` for exhaustive source/output alpha comparison, especially when an asset set intentionally mixes soft-alpha frames and hard-edged or fully opaque frames. Add `--min-alpha-levels 2` only when every non-empty output frame is expected to contain soft alpha; do not use it for fully opaque or intentionally hard-edged sprites.

Run comparison samples:

```bash
python3 "<skill>/scripts/pixel_snapper.py" --input "input.png" --output "sample-8.png" --colors 8
python3 "<skill>/scripts/pixel_snapper.py" --input "input.png" --output "sample-16.png" --colors 16
python3 "<skill>/scripts/pixel_snapper.py" --input "input.png" --output "sample-32.png" --colors 32
```

Override pixel grid size:

```bash
python3 "<skill>/scripts/pixel_snapper.py" --input "input.png" --output "output.png" --colors 16 --pixel-size 8
```

Keep raw upstream output dimensions, even if the aspect ratio changes:

```bash
python3 "<skill>/scripts/pixel_snapper.py" --input "input.png" --output "output.png" --colors 16 --no-preserve-aspect
```

Use an already cloned upstream repository:

```bash
python3 "<skill>/scripts/pixel_snapper.py" --repo "/path/to/spritefusion-pixel-snapper" --input "input.png" --output "output.png"
```

Run against the latest upstream checkout instead of the verified commit:

```bash
python3 "<skill>/scripts/pixel_snapper.py" --input "input.png" --output "output.png" --ref main
```

## Requirements

- Rust/Cargo must be installed.
- Git is required if the upstream repository is not already present locally.
- Use `python` or `py -3` instead of `python3` on systems where that is the configured Python command.
- The wrapper clones `https://github.com/Hugo-Dz/spritefusion-pixel-snapper.git` into a local cache unless `--repo` or `SPRITEFUSION_PIXEL_SNAPPER_REPO` is provided.
- The wrapper checks out the verified upstream commit by default. Use `--ref main`, `--ref <commit-or-tag>`, or `--ref none` when a different checkout policy is needed.
- If network access, cache writes, or Cargo builds are blocked by sandboxing, ask the user for approval and rerun the same command with the required permission.

## Script Interface

The bundled script delegates to the upstream Rust CLI:

```text
input output [k-colors] [--pixel-size N]
```

The upstream CLI defaults to `16` colors when `k-colors` is omitted, but this skill should still confirm the intended color count with the user before final or batch conversion.

The script calls Cargo as:

```text
cargo run --release --manifest-path <repo>/Cargo.toml -- <input> <output> [k-colors] [--pixel-size N]
```

Use `--dry-run` to print the command without executing it. Use `--ref none` to skip Git checkout for a manually managed repository.

By default, the wrapper post-processes the upstream PNG output with `--preserve-aspect`: if the detected grid makes a square source become rectangular, or otherwise changes the source aspect ratio, the wrapper pads the output canvas with transparent pixels instead of stretching pixels. Use `--no-preserve-aspect` only when exact upstream dimensions are required.

Important: `--preserve-aspect` does not preserve the source dimensions and does not normalize all batch outputs to one frame size. It only preserves the source aspect ratio by padding the upstream result.

The fixed-canvas script accepts PNG frame directories:

```text
--input-dir <dir> --output-dir <dir> --size <N|WIDTHxHEIGHT> --colors <k>
```

It preserves relative paths, resizes the whole source canvas to the requested output canvas, and quantizes each frame to the requested color count. It supports non-interlaced 8-bit grayscale, RGB, grayscale-alpha, and RGBA PNG inputs. Use it when animation scale consistency is more important than upstream's content-sensitive grid snapping.

## Troubleshooting

- Bad grid detection: rerun with `--pixel-size N`. The upstream range is `1` through half of the smallest image dimension.
- Aspect ratio changed unexpectedly: keep the default `--preserve-aspect` behavior enabled. If a caller used `--no-preserve-aspect`, rerun without it.
- Animation character size changes between frames: raw upstream grid-derived output dimensions differ. Treat the batch as failed; regenerate with a fixed output canvas and uniform scale from the original source canvas.
- Frame batch has many output dimensions: auto-detected pixel size or content-sensitive grid walking changed per image. Do not ship as animation frames unless the engine also receives per-frame offsets/anchors.
- Output looks darker or has black halos: alpha was probably flattened, premultiplied, or hard-masked. Compare source/output alpha-level counts. Regenerate with the fixed-canvas workflow and preserve soft alpha.
- Output appears to exceed the requested color count: check visible RGB colors separately from RGBA colors. Many RGBA colors can be expected when soft alpha is preserved.
- Aspect preservation fails on source dimension reading: convert the source to PNG, JPEG, GIF, or BMP, or pass `--no-preserve-aspect` when raw upstream dimensions are acceptable.
- Too few colors: increase `--colors`.
- Too many colors or blurry result: decrease `--colors`.
- Very large images: resize before processing; upstream rejects dimensions above `10000x10000`.
- Cargo cannot find a binary: verify the repository is up to date and run from the upstream project root or use the wrapper's `--repo` option.
- Broken cache: if the cache path exists but has no `Cargo.toml`, remove that partial directory or pass `--repo` with a valid checkout.
- Cargo may warn that `src/main.rs` is present in both `lib` and `bin` targets; this is expected in the upstream project and does not block output generation.

## References

Read `references/upstream.md` when exact upstream usage details are needed.
