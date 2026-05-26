# Usage Examples

Concrete invocation patterns for the unified `pixel-snapper` skill. Replace `<skill>` with the absolute path to the loaded skill folder, for example `/home/user/.codex/skills/pixel-snapper`.

## Native Grid Recovery

Use this when the source already has an implied low-resolution pixel grid hidden inside an upscaled or AI-generated PNG.

```bash
uv run "<skill>/scripts/pixel_snapper.py" \
  "input.png" \
  "output-native.png" \
  --k-colors 256
```

For strict retro palettes, sweep a few values:

```bash
for k in 16 32 64 128 256; do
  uv run "<skill>/scripts/pixel_snapper.py" \
    "input.png" "out-k${k}.png" --k-colors "$k"
done
```

Inspect at a useful size without changing recovered pixels:

```bash
ffmpeg -y -loglevel error -i "output-native.png" \
  -vf "scale=iw*8:ih*8:flags=neighbor" \
  "output-native-x8.png"
```

## Known-Layout Spritesheet

Use this when the sheet grid is known. The helper crops each frame first, snaps each frame independently, then reassembles the sheet.

```bash
uv run "<skill>/scripts/pixel_snapper_sheet.py" \
  "walk-sheet.png" \
  "walk-sheet-snapped.png" \
  --cols 6 --rows 1 --k-colors 256
```

Use one palette across all frames when consistency matters:

```bash
uv run "<skill>/scripts/pixel_snapper_sheet.py" \
  "sheet.png" "sheet-snapped.png" \
  --cols 4 --rows 4 --k-colors 128 --shared-palette
```

## Sprite Fusion Grid Snap

Use this for single images, tiles, maps, textures, or cleanup samples where output dimensions may be grid-derived.

```bash
python3 "<skill>/scripts/spritefusion_snapper.py" \
  --input "input.png" \
  --output "spritefusion-output.png" \
  --colors 16
```

Create comparison samples:

```bash
for k in 8 16 32; do
  python3 "<skill>/scripts/spritefusion_snapper.py" \
    --input "input.png" \
    --output "spritefusion-k${k}.png" \
    --colors "$k"
done
```

Override detected grid size only after inspecting a bad auto result:

```bash
python3 "<skill>/scripts/spritefusion_snapper.py" \
  --input "input.png" \
  --output "spritefusion-output.png" \
  --colors 16 \
  --pixel-size 8
```

## Fixed-Canvas Animation Frames

Use this for character actions, frame folders, or other game-ready animation assets that must keep one canvas size and stable character scale.

```bash
python3 "<skill>/scripts/fixed_canvas_pixelate.py" \
  --input-dir "frames-source" \
  --output-dir "frames-pixelated" \
  --size 512 \
  --colors 16
```

Use rectangular output when required:

```bash
python3 "<skill>/scripts/fixed_canvas_pixelate.py" \
  --input-dir "frames-source" \
  --output-dir "frames-pixelated" \
  --size 384x512 \
  --colors 16
```

## Batch Inspection

Verify fixed-frame outputs before shipping them:

```bash
python3 "<skill>/scripts/inspect_png_batch.py" \
  --root "frames-pixelated" \
  --source-root "frames-source" \
  --require-single-size \
  --max-visible-rgb 16
```

`--source-root` samples matching source files to detect whether soft alpha should have been preserved. Use `--source-check-limit 0` for an exhaustive source/output alpha comparison.

## Quick Sanity Checks

- If native-grid output is exactly `64x64`, fallback detection probably fired.
- If output is mostly one color, increase the color count.
- If output dimensions are close to the source dimensions, decrease the color count or reject the input as a poor snapping candidate.
- If fixed-frame outputs have more than one size, do not ship them as fixed-frame animation assets.
- If output has dark halos, inspect alpha levels and regenerate while preserving soft alpha.
