# Phaser 4 iOS Rendering Notes

Use this when a Capacitor iOS Phaser project is confirmed Phaser 4.x, the user asks for Phaser 4, or the task touches Phaser 3 to 4 migration, renderer internals, filters, lighting, shaders, `DynamicTexture`, `RenderTexture`, `SpriteGPULayer`, `TilemapGPULayer`, texture orientation, or renderer performance.

This reference supplements `phaser4-gamedev`; use that skill for the broader Phaser 4 workflow.

## Version And Renderer Contract

- Inspect the installed Phaser 4 minor version before using version-sensitive APIs.
- Prefer local typings and official docs for exact API names when renderer details matter.
- Start new Phaser 4 iOS work with WebGL-focused assumptions unless the project has a concrete Canvas compatibility requirement.
- Do not port Phaser 3 renderer internals, pipelines, masks, FX, tint, camera internals, or texture assumptions without a focused audit.
- Treat filters, lighting, render targets, and GPU layers as architectural choices; they affect batching, fill-rate, memory, and WKWebView compatibility.

Useful searches before renderer-sensitive edits:

```bash
rg -n "\"phaser\"|Phaser\\.VERSION|phaser\\.min\\.js|phaser\\.js|from ['\"]phaser['\"]" . -g 'package.json' -g '*lock*' -g '*.html' -g 'src/**' -g 'public/**'
rg -n "setTintFill|tintFill|BitmapMask|GeometryMask|preFX|postFX|ColorMatrix|Phaser\\.Geom\\.Point|Point\\.|Math\\.TAU|Math\\.PI2|setPipeline\\(['\"]Light2D['\"]\\)|DynamicTexture|RenderTexture|TileSprite|Shader|Pipeline|WebGLRenderer|gl\\.|Phaser\\.Struct\\.(Set|Map)" .
```

Classify findings:
- Mechanical: local API replacement, low risk after compile and visual checks.
- Behavioral: code compiles but meaning, timing, orientation, or visual output may differ.
- Architectural: old renderer/filter/shader/pipeline model needs redesign.

## Rendering Path Selection

| Path | Best Fit | Avoid When |
| --- | --- | --- |
| Standard game objects | Interactive gameplay, physics sprites, UI, ordinary animation | Only huge simple visual counts are the measured bottleneck |
| `SpriteGPULayer` | Dense simple quads such as starfields or decorative swarms | Members need rich gameplay logic, collisions, multiple textures, or frequent structural edits |
| `TilemapGPULayer` | Very large orthographic tile layers with high visible tile count | Small maps, isometric/staggered maps, many tilesets, or constantly changing maps |
| `DynamicTexture` / `RenderTexture` | Runtime compositing, capture, stamping, generated textures, shader inputs | A plain sprite, atlas frame, tint, or animation frame is enough |
| Filters / lighting | Image-space effects, masks, color grading, glow, blur, normal-map lighting | The look can be solved by art, tint, animation, or an object-local effect |
| Custom shader / raw WebGL | The effect cannot be expressed with Phaser APIs | The code mutates renderer state unpredictably or depends on v3 internals |

Use standard objects first unless the requirement or measured bottleneck justifies a specialized renderer path.

## iOS-Specific Performance Model

Ask which cost dominates before rewriting architecture:
- CPU churn: objects, timers, tweens, sounds, or particles created/destroyed every frame.
- Physics churn: too many collision pairs or active bodies.
- Batch breaks: filters, lighting, blend modes, render target switches, shader changes, or mixed texture state.
- Fill-rate: large translucent, filtered, lit, or full-screen surfaces.
- Asset pressure: oversized textures, unpadded atlas frames, excessive atlases, or tile data too large for mobile GPUs.
- Device limits: high DPR, low-power mode, memory pressure, thermal throttling, and WKWebView context loss.

Fix pooling, culling, atlas layout, texture sizes, and collision scope before introducing GPU layers or custom shaders.

## Migration Hotspots

Review these before moving a Phaser 3 project to Phaser 4:

| Phaser 3 Pattern | Phaser 4 Direction |
| --- | --- |
| `sprite.setTintFill(color)` | `sprite.setTint(color).setTintMode(Phaser.TintModes.FILL)` |
| `Math.PI2` | `Math.TAU` |
| older `Math.TAU` as PI / 2 | `Math.PI_OVER_2` |
| `sprite.setPipeline('Light2D')` | `sprite.setLighting(true)` |
| `preFX` / `postFX` | Phaser 4 filters |
| `BitmapMask` / `GeometryMask` patterns | Current mask/filter APIs for the installed version |
| `Phaser.Geom.Point` helpers | `Phaser.Math.Vector2` or current math helpers |
| custom pipelines or direct `gl` calls | Render nodes, `Extern`, filters, shaders, or a redesign |

Do not apply these mechanically without checking the installed Phaser minor version and visual behavior.

## Render Targets, Filters, And Texture Orientation

Rules:
- `DynamicTexture` and `RenderTexture` drawing can be buffered; call `render()` when output must become visible.
- Minimize per-frame render target switches on iOS.
- Avoid large full-screen render targets unless they are clearly needed.
- Enable filters before accessing filter lists, and guard availability because filters are WebGL-only.
- Prefer object-local filters unless a camera-wide effect is deliberate.
- Treat blur, bloom, shadows, lighting, and large masks as fill-rate risks on iPhone and iPad GPUs.
- Re-check shaders that sample framebuffer outputs, compressed textures, render textures, or dynamic textures; orientation and alpha may differ from ordinary images.

Minimal render-target pattern:

```ts
const texture = this.textures.addDynamicTexture('stamp-output', 256, 256);

texture.drawFrame('sheet', 'spark', 64, 64);
texture.render();
```

Filter pattern:

```ts
sprite.enableFilters();

if (sprite.filters) {
  sprite.filters.internal.addGlow(0xffffff, 2, 0);
}
```

## iOS Verification

For Phaser 4 renderer changes, verify on browser and iOS:
- Game boots to the first playable scene without console, loader, or texture key errors.
- Sprites, atlases, tilemaps, bitmap fonts, UI panels, and pixel-art rounding render correctly.
- Camera follow, bounds, zoom, fades, filters, masks, lighting, and render textures match intent.
- Custom shaders sample textures with the correct orientation.
- `DynamicTexture` or `RenderTexture` output is nonblank after `render()`.
- GPU layers do not introduce update spikes when data changes.
- FPS and memory remain acceptable on the target simulator or device.
