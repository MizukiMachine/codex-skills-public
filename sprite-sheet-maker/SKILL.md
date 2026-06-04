---
name: sprite-sheet-maker
description: "複数のフレームPNGをゲーム用スプライトシートにまとめる。番号付きフレーム、ピクセルアート、キャラクターアクション列、4x4配置などで使う。"
---

# Sprite Sheet Maker

## Purpose

Use the bundled `scripts/make_spritesheet.py` script to combine PNG animation frames into a single sprite sheet. The script is pure Python and does not require Pillow, ImageMagick, or npm packages.

## Workflow

1. Use the provided input directory and output path. Ask only when either is missing or ambiguous.
2. Sort frames with natural filename order by default, so `frame_2.png` comes before `frame_10.png`.
3. Use the default square-ish grid unless the user specifies a layout. A 16-frame directory becomes `4x4`.
4. Preserve transparency and use transparent background by default.
5. For variable-sized character frames, keep the default `--align bottom-center` to reduce animation foot/baseline jitter. Use `--align center` for generic icons or effects.
6. Generate JSON metadata when engine integration needs frame rectangles or source offsets.

## Quick Commands

Default sprite sheet:

```bash
python3 "<skill>/scripts/make_spritesheet.py" --input-dir "frames" --output "spritesheet.png"
```

Force 4 columns and write metadata next to the PNG:

```bash
python3 "<skill>/scripts/make_spritesheet.py" --input-dir "frames" --output "spritesheet.png" --columns 4 --metadata
```

Use fixed cells, center alignment, and spacing:

```bash
python3 "<skill>/scripts/make_spritesheet.py" --input-dir "frames" --output "spritesheet.png" --columns 4 --cell-width 256 --cell-height 256 --align center --spacing 2
```

Preview the planned output without writing files:

```bash
python3 "<skill>/scripts/make_spritesheet.py" --input-dir "frames" --output "spritesheet.png" --dry-run
```

## Script Behavior

- Inputs: non-interlaced 8-bit PNG files, including RGBA, RGB, grayscale, grayscale-alpha, and indexed-color PNGs.
- Output: 8-bit RGBA PNG.
- Default cell size: maximum width and height found across all input frames.
- Default grid: `ceil(sqrt(frame_count))` columns and enough rows. For 16 frames this is `4x4`.
- Default order: natural filename order.
- Default alignment: `bottom-center`.
- Default margin and spacing: `0`.
- Default background: transparent.

## Options

- `--pattern "*.png"`: choose input files inside `--input-dir`.
- `--columns N` / `--rows N`: control grid layout.
- `--cell-width N` / `--cell-height N`: force cell dimensions; the script rejects cells smaller than the largest frame.
- `--align VALUE`: one of `top-left`, `top-center`, `top-right`, `center-left`, `center`, `center-right`, `bottom-left`, `bottom-center`, `bottom-right`.
- `--margin N`: outer margin in pixels.
- `--spacing N`: spacing between cells in pixels.
- `--background transparent|#RRGGBB|#RRGGBBAA`: background fill.
- `--metadata [path]`: write JSON metadata. Without a path, writes `<output>.json`.
- `--order natural|lex`: choose filename sort behavior.

## Troubleshooting

- Unexpected animation jitter: rerun with `--align bottom-center` for characters or `--align center` for effects.
- Output cells too large: inspect source frame dimensions; variable-sized frames use the maximum frame size as cell size.
- Engine expects a single row: use `--columns <frame-count>` or `--rows 1`.
- Engine expects exact cells: pass `--cell-width` and `--cell-height`.
- Unsupported PNG error: convert the source frames to non-interlaced 8-bit PNGs first.
