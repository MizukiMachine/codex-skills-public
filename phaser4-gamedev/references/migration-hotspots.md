# Phaser 3 To 4 Migration Hotspots

Use this reference before touching a Phaser 3 codebase or reviewing a port that already compiles. The first pass is search, classification, and risk control, not blind replacement.

## Migration Model

Phaser 4 migration is selective redesign:

1. Mechanical API updates.
2. Behavioral review for code that compiles but changes meaning.
3. Architectural rewrite for renderer, filter, shader, texture, mask, and custom pipeline code.

Do the cheap searches first so renderer-level risks are visible before the code is half-migrated.

## Version Check

Inspect the installed package, vendored bundle, script tag, or runtime `Phaser.VERSION`. Phaser 4.0 and 4.1 docs are both available, and future minor versions may change API details.

```bash
rg -n "\"phaser\"|Phaser\\.VERSION|phaser\\.min\\.js|phaser\\.js|from ['\"]phaser['\"]" . -g 'package.json' -g '*lock*' -g '*.html' -g 'src/**' -g 'public/**'
```

Use official sources for exact replacements:

- `https://docs.phaser.io/api-documentation`
- `https://github.com/phaserjs/phaser/blob/v4.0.0/changelog/v4/4.0/CHANGELOG-v4.0.0.md`
- `https://phaser.io/tutorials/phaser-4-rendering-concepts`

## First Search Pass

Run this before editing:

```bash
rg -n "setTintFill|tintFill|BitmapMask|GeometryMask|preFX|postFX|ColorMatrix|Phaser\\.Geom\\.Point|Point\\.|Math\\.TAU|Math\\.PI2|setPipeline\\(['\"]Light2D['\"]\\)|DynamicTexture|RenderTexture|TileSprite|Shader|Pipeline|WebGLRenderer|gl\\.|Phaser\\.Struct\\.(Set|Map)" .
```

Classify every finding into:

- **Mechanical**: replacement is local and low risk.
- **Behavioral**: code compiles but meaning, orientation, timing, or visual output may differ.
- **Architectural**: the v3 concept no longer maps cleanly to v4.

## Mechanical Replacements

| Phaser 3 | Phaser 4 Direction | Review Needed |
|----------|--------------------|---------------|
| `setTintFill(color)` | `setTint(color).setTintMode(Phaser.TintModes.FILL)` | Confirm original code wanted fill tint, not multiply tint |
| `Math.PI2` | `Math.TAU` | Confirm the expression expected a full turn |
| `setPipeline('Light2D')` | `setLighting(true)` | Confirm lighting setup and normal maps |
| `Phaser.Struct.Set` | native `Set` | Rewrite helper methods such as `iterateLocal` |
| `Phaser.Struct.Map` | native `Map` | Rewrite helper methods such as `contains` or `setAll` |

These are good codemod candidates only after tests or visual checks exist.

## Behavioral Review Required

### Math Constants

In Phaser 3, `Math.TAU` represented PI / 2 in older codepaths, while `Math.PI2` represented PI * 2. In Phaser 4, `Math.TAU` is PI * 2 and `Math.PI_OVER_2` is PI / 2.

Rules:

- Replace old `Math.PI2` usage with `Math.TAU`.
- Replace old `Math.TAU` quarter-turn usage with `Math.PI_OVER_2`.
- Review any custom trig helper or angle table.

### Color Matrix And Filters

Phaser 4 replaced the old FX model with filters. `preFX` and `postFX` assumptions do not transfer directly.

Check:

- filter ownership: game object vs camera
- internal vs external filters
- filter order
- padding needs for blur, glow, and shadow
- WebGL-only behavior

### `DynamicTexture` And `RenderTexture`

Drawing commands are buffered. Blank or stale output usually means queued commands were never flushed.

Check every migrated render target for:

- `render()` after queued drawing commands
- clear/preserve semantics
- orientation when used by shaders or framebuffers
- per-frame render target switches

### `TileSprite`

Phaser 4 `TileSprite` is not the old object internally.

Key changes:

- Texture cropping support from old patterns is gone.
- Repeating atlas or spritesheet frames is now viable.
- `tileRotation` exists in Phaser 4.

If old code relied on crop-based repetition tricks, redesign the effect.

### Camera Internals

Normal camera position, scroll, zoom, bounds, follow, and fade patterns may port cleanly. Direct matrix work is risky.

Review any code that:

- reads or mutates camera matrices
- depends on pre-render rounding
- implements custom culling
- syncs shader uniforms from camera internals

## Architectural Rewrite Areas

### Masks And FX

Phaser 4 uses filters for many effects and masks. A direct `BitmapMask` or `preFX`/`postFX` port usually needs redesign.

Migration approach:

1. Identify the visual result the old mask or FX produced.
2. Decide whether the result belongs on the object, camera, or render texture.
3. Use current filter APIs for the installed Phaser version.
4. Verify visual order, padding, performance, and WebGL availability.

### Custom Pipelines And Renderer Internals

Phaser 4 replaced the Phaser 3 pipeline model with a modern renderer and render nodes. Treat custom pipelines, direct WebGL state, and renderer buffer access as redesign work.

Search for:

- `Pipeline`
- `WebGLRenderer`
- direct `gl.` calls
- custom shader setup
- framebuffer assumptions
- texture coordinate flips

Use Phaser 4 filters, shaders, render nodes, or `Extern` only after reading the current docs and source for the exact version.

### Shaders And Texture Orientation

Phaser 4 uses GL-style texture orientation through the renderer pipeline. Re-check shaders that sample:

- ordinary textures
- framebuffer outputs
- compressed textures
- render textures or dynamic textures

If an effect is upside down or vertically offset, verify asset orientation and source type before changing shader math.

### Geometry And Points

Phaser 4 moved many point-like workflows toward `Vector2` and newer math helpers.

Review:

- `Phaser.Geom.Point`
- `Point.*` static helpers
- geometry methods that return or accept point-like objects
- custom collision or path code using point shape assumptions

Use `Phaser.Math.Vector2`, `Phaser.Types.Math.Vector2Like`, or current math helpers as appropriate.

## Recommended Migration Order

1. Confirm source and target Phaser versions.
2. Run the hotspot search and classify results.
3. Update the package and TypeScript surfaces.
4. Fix mechanical compile errors.
5. Redesign renderer, filter, shader, mask, texture, and pipeline code.
6. Verify boot, scenes, input, physics, animations, tilemaps, and visual output.
7. Optimize only after behavior matches the original.

## Review Checklist

- Does the port boot without loader or texture key errors?
- Do all scenes still transition and restart correctly?
- Are animations using the same frames and timing?
- Are masks, filters, lighting, and render textures visually equivalent or intentionally changed?
- Are custom shaders sampling with the correct orientation?
- Are angle constants semantically correct?
- Are tilemaps, TileSprites, and camera bounds behaving as before?
- Are FPS and memory acceptable after renderer changes?

## What Not To Do

- Do not rewrite the whole game before classifying hotspots.
- Do not assume TypeScript success means rendering success.
- Do not port custom pipelines as string replacements.
- Do not debug shader math before checking texture orientation and render-target source.
- Do not upgrade to GPU layers during migration unless the original behavior is already stable.
