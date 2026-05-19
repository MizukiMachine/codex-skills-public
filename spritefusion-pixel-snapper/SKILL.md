---
name: spritefusion-pixel-snapper
description: Use Sprite Fusion Pixel Snapper to convert or clean arbitrary raster images into grid-snapped pixel art PNGs. Trigger this skill when the user asks to pixelate, dot-art, pixel-snap, clean AI-generated pixel art, quantize colors for pixel art, or run Hugo-Dz/spritefusion-pixel-snapper on an image.
---

# Sprite Fusion Pixel Snapper

## Purpose

Use Hugo-Dz/spritefusion-pixel-snapper as the processing engine for raster images. The tool snaps source pixels to a regular grid and quantizes colors into a strict palette, which is especially useful for AI-generated pixel art, tilemaps, isometric maps, 2D game assets, and textures.

## Workflow

1. Use the provided input and output paths. Ask only when either path is missing or ambiguous. Prefer PNG output.
2. Choose `k_colors`:
   - Default: `16`.
   - Use smaller values such as `4` or `8` for retro sprites.
   - Use larger values such as `24` or `32` when preserving shading matters.
3. Use auto-detected pixel size first. Add `--pixel-size N` only if the output grid is wrong.
4. Run the wrapper script in `scripts/pixel_snapper.py`.
5. Inspect the output. If the grid is too coarse or too fine, rerun with an explicit `--pixel-size`.

## Quick Commands

Run with defaults:

```bash
python3 "<skill>/scripts/pixel_snapper.py" --input "input.png" --output "output.png"
```

Run with a 16-color palette:

```bash
python3 "<skill>/scripts/pixel_snapper.py" --input "input.png" --output "output.png" --colors 16
```

Override pixel grid size:

```bash
python3 "<skill>/scripts/pixel_snapper.py" --input "input.png" --output "output.png" --colors 16 --pixel-size 8
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

The script calls Cargo as:

```text
cargo run --release --manifest-path <repo>/Cargo.toml -- <input> <output> [k-colors] [--pixel-size N]
```

Use `--dry-run` to print the command without executing it. Use `--ref none` to skip Git checkout for a manually managed repository.

## Troubleshooting

- Bad grid detection: rerun with `--pixel-size N`. The upstream range is `1` through half of the smallest image dimension.
- Too few colors: increase `--colors`.
- Too many colors or blurry result: decrease `--colors`.
- Very large images: resize before processing; upstream rejects dimensions above `10000x10000`.
- Cargo cannot find a binary: verify the repository is up to date and run from the upstream project root or use the wrapper's `--repo` option.
- Broken cache: if the cache path exists but has no `Cargo.toml`, remove that partial directory or pass `--repo` with a valid checkout.
- Cargo may warn that `src/main.rs` is present in both `lib` and `bin` targets; this is expected in the upstream project and does not block output generation.

## References

Read `references/upstream.md` when exact upstream usage details are needed.
