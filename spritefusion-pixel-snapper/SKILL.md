---
name: spritefusion-pixel-snapper
description: Use Sprite Fusion Pixel Snapper to convert or clean arbitrary raster images into grid-snapped pixel art PNGs. Trigger this skill when the user asks to pixelate, dot-art, pixel-snap, clean AI-generated pixel art, quantize colors for pixel art, or run Hugo-Dz/spritefusion-pixel-snapper on an image.
---

# Sprite Fusion Pixel Snapper

## Purpose

Use Hugo-Dz/spritefusion-pixel-snapper as the processing engine for raster images. The tool snaps source pixels to a regular grid and quantizes colors into a strict palette, which is especially useful for AI-generated pixel art, tilemaps, isometric maps, 2D game assets, and textures.

## Workflow

1. Use the provided input and output paths. Ask when either path is missing or ambiguous. Prefer PNG output.
2. Choose `k_colors` before final processing:
   - If the user specified a color count, use that value.
   - If the color count is missing, ask before running final or batch conversion. Offer `8` for stronger retro styling, `16` for balanced pixel-art detail, and `32` when preserving shading matters.
   - If the user is unsure, create comparison samples from a representative image at `8`, `16`, and `32` colors, then ask which setting to use for the remaining images.
   - Use `16` only when the user explicitly accepts the default or asks you to proceed without choosing.
3. Use auto-detected pixel size first. Add `--pixel-size N` only if the output grid is wrong.
4. Run the wrapper script in `scripts/pixel_snapper.py`.
5. Keep the wrapper's default aspect-ratio preservation enabled unless the user explicitly asks for raw upstream dimensions. The wrapper pads the PNG canvas with transparent pixels when the upstream grid would change the input aspect ratio.
6. Inspect the output. If the grid is too coarse or too fine, rerun with an explicit `--pixel-size`.

## Quick Commands

Run after the user chooses a 16-color palette:

```bash
python3 "<skill>/scripts/pixel_snapper.py" --input "input.png" --output "output.png" --colors 16
```

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

## Troubleshooting

- Bad grid detection: rerun with `--pixel-size N`. The upstream range is `1` through half of the smallest image dimension.
- Aspect ratio changed unexpectedly: keep the default `--preserve-aspect` behavior enabled. If a caller used `--no-preserve-aspect`, rerun without it.
- Aspect preservation fails on source dimension reading: convert the source to PNG, JPEG, GIF, or BMP, or pass `--no-preserve-aspect` when raw upstream dimensions are acceptable.
- Too few colors: increase `--colors`.
- Too many colors or blurry result: decrease `--colors`.
- Very large images: resize before processing; upstream rejects dimensions above `10000x10000`.
- Cargo cannot find a binary: verify the repository is up to date and run from the upstream project root or use the wrapper's `--repo` option.
- Broken cache: if the cache path exists but has no `Cargo.toml`, remove that partial directory or pass `--repo` with a valid checkout.
- Cargo may warn that `src/main.rs` is present in both `lib` and `bin` targets; this is expected in the upstream project and does not block output generation.

## References

Read `references/upstream.md` when exact upstream usage details are needed.
