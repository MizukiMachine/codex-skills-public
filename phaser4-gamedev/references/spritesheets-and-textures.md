# Phaser 4 Spritesheets And Textures

Use this reference before loading spritesheets, atlases, compressed textures, TileSprites, render textures, shader inputs, or GPU layer textures.

Most apparent animation and rendering bugs start as asset metadata bugs. Measure first.

## Asset Contract

Confirm these values from the actual source asset before writing loader config:

- file path and loader key
- full image width and height
- frame width and height
- spacing and margin
- atlas format and frame names
- trimmed vs untrimmed frame bounds
- origin or pivot assumptions
- whether the asset is pixel art or smooth art
- whether the texture is compressed
- whether the texture will be sampled by custom shaders, filters, render targets, or GPU layers

Do not infer dimensions from visual appearance.

## Fast Measurement

Use whichever local tool is available:

```bash
file path/to/asset.png
identify path/to/asset.png
magick identify path/to/asset.png
```

If no image tool is installed, inspect the asset through the project editor, browser devtools, atlas JSON, or a tiny runtime probe that logs `texture.get(frame)` data after preload.

## Spritesheets

For spritesheets:

- compute the frame grid from exact image dimensions
- verify spacing and margin numerically
- confirm square vs rectangular frames
- check whether the final row is full or partial
- test the first frame, last frame, and one frame near each row boundary
- verify animation frame ranges against the measured grid

Example checks:

```text
image: 1024 x 512
frame: 64 x 64
spacing: 0
margin: 0
columns: 16
rows: 8
frame count: 128
last index: 127
```

Do not create animation frame ranges until this math is explicit.

## Atlases

For texture atlases:

- trust atlas data over visual intuition
- confirm every code-referenced frame name exists
- inspect trimmed frames before using tight collision, hit areas, origins, or melee ranges
- verify padding/extrusion if smooth filtering or camera zoom can expose seams
- avoid manual frame-coordinate duplication when the atlas parser already owns the data

When collisions or origins depend on art bounds, compare atlas frame bounds with the intended gameplay box. Trimmed art often needs explicit body sizes or offsets.

## `SpriteGPULayer` Texture Requirements

`SpriteGPULayer` gains speed by being constrained. Before using it, confirm:

- members can share one texture source
- a multi-atlas is not required
- frame padding or power-of-two texture size is acceptable for seam-sensitive visuals
- the layer can be populated mostly up front
- gameplay does not require normal per-object behavior

If the layer will mutate constantly, standard game objects may be simpler and faster in practice.

## Tilemaps And Tile Textures

For tilemap work:

- confirm map format, tileset image path, tile width, tile height, spacing, margin, and firstgid
- confirm collision layer names and custom properties from Tiled or the map source
- test tile index 0 handling and empty tile assumptions
- verify camera bounds against map pixel dimensions
- when using `TilemapGPULayer`, regenerate the layer data texture after runtime tile edits

For very large maps, read [rendering-and-performance.md](rendering-and-performance.md) before switching tile renderers.

## `TileSprite`

Phaser 4 `TileSprite` can repeat atlas or spritesheet frames, but old crop-based repetition patterns need redesign.

Check:

- frame key and frame bounds
- tile position and tile scale
- `tileRotation` usage
- whether the old code depended on cropping behavior that no longer exists

## Texture Orientation

Phaser 4 uses GL-style texture orientation internally. This matters most when working with:

- custom shaders
- framebuffer output
- `DynamicTexture`
- `RenderTexture`
- compressed textures
- external WebGL tools

For ordinary PNG or JPG game-object rendering, Phaser handles common cases. For shaders and compressed textures, verify orientation deliberately.

Debug order for upside-down, mirrored, or vertically offset effects:

1. Identify the texture source: image, atlas, framebuffer, compressed texture, dynamic texture, or render texture.
2. Verify shader UV assumptions.
3. Verify whether the source asset pipeline targeted Phaser 3 or Phaser 4.
4. Test one simple known texture before editing complex shader math.

## Compressed Textures

For compressed texture workflows:

- confirm the format supported by target browsers and devices
- verify asset generation settings, including Y-axis orientation
- keep source PNGs or source art available for debugging
- compare against an uncompressed texture when diagnosing shader or orientation issues

Do not treat compressed textures like ordinary PNGs during migration.

## Pixel Art

For pixel art:

- measure frames exactly
- use nearest-neighbor texture filtering where appropriate
- avoid unwanted atlas bleeding by padding or extruding frames
- test camera movement at intended zoom and DPR
- use rounding deliberately, not as a global reflex

Bad pixel-art output is often a combination of frame metadata, filtering, CSS scaling, DPR, and camera movement. Check all of them.

## Runtime Probes

When asset metadata is unclear, add a temporary debug probe after preload:

```ts
const texture = this.textures.get('hero');
const frame = texture.get('idle-0');

console.table({
  key: texture.key,
  frame: frame.name,
  x: frame.x,
  y: frame.y,
  width: frame.width,
  height: frame.height,
  cutWidth: frame.cutWidth,
  cutHeight: frame.cutHeight
});
```

Remove or guard probes after diagnosis.

## Anti-Patterns

- Eyeballing frame dimensions.
- Debugging animation timing before proving frame metadata.
- Assuming all texture sources share the same orientation rules.
- Using multi-atlas textures for `SpriteGPULayer`.
- Ignoring trimmed atlas frames when physics or hit areas depend on visible bounds.
- Treating compressed textures like ordinary PNGs during migration.
