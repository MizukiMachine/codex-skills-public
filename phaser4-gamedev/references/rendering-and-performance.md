# Phaser 4 Rendering and Performance

Use this reference when the task involves GPU layers, filters, lighting, render targets, custom shaders, batching, fill-rate, or FPS problems.

## Performance Model

Ask what is actually expensive before changing architecture:

- CPU object churn: many objects created, destroyed, or updated every frame.
- Batch breaks: filters, lighting, blend changes, shader changes, render target switches, or mixed texture/state paths.
- Fill-rate: large translucent, filtered, lit, or full-screen surfaces.
- Asset shape: oversized textures, multi-atlas use where a single image is required, unpadded frames, or bad tile data.
- Browser/device limits: mobile GPUs, high DPR, low-power mode, and memory pressure.

Do not replace a clear implementation with a specialized renderer until you know which cost dominates.

## Official API Checks

When exact API names matter, verify against the installed Phaser minor version:

- Phaser API: `https://docs.phaser.io/api-documentation`
- Rendering concepts: `https://phaser.io/tutorials/phaser-4-rendering-concepts`
- Phaser 4 changelog: `https://github.com/phaserjs/phaser/blob/v4.0.0/changelog/v4/4.0/CHANGELOG-v4.0.0.md`

## Rendering Path Selection

| Path | Best Fit | Main Cost Or Constraint |
|------|----------|-------------------------|
| Standard game objects | Interactive gameplay, physics sprites, UI, ordinary animation | More CPU work at huge counts |
| `SpriteGPULayer` | Huge counts of simple quads or shader-animated background members | Inflexible members, one texture source, expensive buffer rebuilds |
| `TilemapGPULayer` | Very large orthographic tile layers and smooth filtered tile edges | Constrained tilemap shape, one tileset focus, explicit regeneration after edits |
| `DynamicTexture` | Generated textures, masks, capture, compositing, stamping, shader inputs | Buffered command execution and render target complexity |
| `RenderTexture` | A visible game object backed by a dynamic texture | Same buffered update issues as `DynamicTexture` |
| Filters | Image-space effects, masks, color grading, glow, blur, camera effects | Extra render passes and possible large framebuffer cost |
| Lighting | Normal-map or light-driven visuals | Shader changes break batches and add fill-rate cost |
| Custom shader / `Extern` | A feature cannot be expressed with Phaser objects or filters | Renderer-state risk and version-specific APIs |

## `SpriteGPULayer`

Use `SpriteGPULayer` for dense visual members that are simple enough to live in a GPU buffer:

- starfields
- large decorative swarms
- particle-like background motion
- repeated animated environmental details

Key constraints:

- Populate the layer in batches where possible.
- Avoid frequent add/remove churn; buffer updates are the tradeoff for speed.
- Prefer one source texture. Multi-atlas textures are not a good fit.
- Use power-of-two textures or padded/extruded frames when exact seams matter.
- Keep complex enemies, pickups, bullets with collision logic, and UI as standard game objects unless measured data proves otherwise.

If member data must change, prefer targeted member updates over rebuilding the whole layer, and profile on the target device.

## `TilemapGPULayer`

Use `TilemapGPULayer` when the visible tile count is large enough to justify a specialized renderer.

Good fit:

- orthographic tilemaps
- huge tile layers
- one primary tileset
- camera zoom-out showing many tiles
- smooth filtered tile boundaries

Risky fit:

- isometric or staggered maps
- many tilesets or unusual tile transforms
- small maps where normal `TilemapLayer` is already cheap
- constantly changing maps

If tile data changes at runtime, regenerate the layer data texture with the current Phaser API, such as `generateLayerDataTexture`, so the GPU representation matches the map.

## Filters And Lighting

Filters and lighting are powerful but visible costs:

- Enable game-object filters before accessing filter lists.
- Guard `gameObject.filters` after `enableFilters()` because filter setup can return early when WebGL filters are unavailable.
- Prefer internal filters on the specific object when a camera-wide effect is not required.
- Use camera external filters for deliberate full-screen effects only.
- Do not share one filter controller across owners unless the docs for that controller explicitly allow it.
- Treat blur, bloom, shadow, and large masked areas as fill-rate risks.
- Apply lighting only where it materially improves the scene, because lighting changes shaders and can break batches.

Common pattern:

```ts
sprite.enableFilters();

if (sprite.filters) {
  sprite.filters.internal.addGlow(0xffffff, 2, 0);
}
```

## `DynamicTexture` And `RenderTexture`

Use render targets when you need capture, compositing, generated textures, or reusable rendered output.

Rules:

- Queueing draw calls is not the same as updating the texture.
- Call `render()` when the drawn output must become visible.
- Minimize per-frame render target switches.
- Avoid large full-screen render targets on mobile unless they are clearly needed.
- If a shader or mask uses the generated texture, verify orientation and alpha behavior in browser.

Minimal pattern:

```ts
const texture = this.textures.addDynamicTexture('stamp-output', 256, 256);

texture.drawFrame('sheet', 'spark', 64, 64);
texture.render();
```

## Pixel Art And Rounding

Phaser 4 defaults `roundPixels` to `false`. Use rounding deliberately:

- For crisp pixel art, test camera movement, scaling, rotation, and DPR before committing.
- Prefer per-object or camera-specific rounding where possible.
- Avoid global rounding for scenes with rotation or scale-heavy motion unless the wobble tradeoff is acceptable.
- Verify CSS image-rendering, texture filtering, and atlas padding alongside Phaser config.

## Profiling Order

1. Reproduce the slowdown in the browser with devtools open.
2. Count active game objects, physics bodies, tweens, timers, particles, and tile layers.
3. Check creation/destruction inside `update`.
4. Identify filters, lighting, blend modes, render targets, and shader changes.
5. Check texture size, atlas layout, tilemap dimensions, and whether GPU layer constraints fit.
6. Try the smallest targeted fix.
7. Re-test on the intended browser and device class.

## Debug Signals

| Symptom | Likely Cause | First Check |
|---------|--------------|-------------|
| FPS drops as entities spawn | Object churn, physics bodies, tweens, or event leaks | Pool or reuse objects; inspect active counts |
| FPS drops only with effects enabled | Filters, lighting, render targets, or fill-rate | Disable effects one by one and compare |
| Tiles shimmer or show seams | Texture filtering, atlas padding, non-power-of-two texture precision, or tile layer path | Verify padding, texture size, filtering, and tile renderer choice |
| Render texture appears blank or stale | Buffered commands were not flushed | Confirm `render()` is called after drawing |
| GPU layer update spikes | Whole buffer or data texture is being rebuilt too often | Batch edits or use standard objects for dynamic members |
| Looks correct desktop, slow mobile | Fill-rate, DPR, framebuffer size, or mobile GPU behavior | Lower effect area or resolution; test target devices |

## Anti-Patterns

- Using shader/filter solutions for problems that tint, animation frames, or art direction could solve.
- Moving gameplay entities into `SpriteGPULayer` before proving object count is the bottleneck.
- Using `TilemapGPULayer` for every tilemap even when normal tilemaps are simpler and fast enough.
- Applying full-camera filters for object-local effects.
- Optimizing rendering before asset metadata and gameplay correctness are verified.
