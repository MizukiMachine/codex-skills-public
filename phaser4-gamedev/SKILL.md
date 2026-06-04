---
name: phaser4-gamedev
description: "Phaser 4専用のゲーム開発・移行を扱う。Phaser 4プロジェクト、Phaser 3からの移行、レンダラー、シェーダー、GPUレイヤー、v4固有の不具合調査で使う。Phaser 3のみ、またはバージョン不明の場合はphaser-gamedevを優先する。"
---

# Phaser 4 Game Development

## Purpose

Use this skill to implement, debug, optimize, or migrate Phaser 4 browser games with codebase-aware choices. Invoke it when the user explicitly asks for Phaser 4, the codebase confirms Phaser 4.x, or the task is a Phaser 3 to 4 migration. Produce working game code, measured asset metadata, explicit rendering or migration decisions, and verification from project scripts or a browser smoke test.

## Companion Skill

This skill extends `phaser-gamedev`; it does not replace the common Phaser workflow.

For any Phaser 4 task, first read enough of `phaser-gamedev/SKILL.md` to apply its shared Phaser guidance: version discovery, scene ownership, asset metadata, delta-time simulation, object lifecycle anti-patterns, debug visibility, and verification. Then apply this Phaser 4-specific skill for renderer, API, migration, and WebGL-focused decisions.

Do not deep-read extra `phaser-gamedev` references unless the task specifically needs them.

## Operating Model

Phaser 4 work is renderer-aware game engineering. The default target is WebGL; Canvas exists for compatibility, but filters, real-time lighting, GPU layers, and the modern renderer path are WebGL-centered. Preserve game feel first, then choose the simplest rendering path that satisfies the visual and performance constraints.

Prioritize:

1. Correct gameplay, input feel, and scene lifecycle.
2. Exact asset metadata: dimensions, frame size, spacing, margin, atlas frame names, and texture orientation.
3. Simple rendering paths before filters, shaders, render targets, or GPU layers.
4. Phaser 4 APIs verified against the installed minor version.
5. Browser evidence for visual, input, animation, and performance-sensitive changes.

Before acting, answer:

- Which Phaser 4 minor version is installed or vendored?
- Is this new Phaser 4 work, a bug fix, a performance pass, or a Phaser 3 migration?
- Which scene owns the objects, input, physics, UI, and transitions?
- What asset file is the source of truth, and what are its exact measurements?
- Does the feature need standard game objects, filters, lighting, shaders, `DynamicTexture`, `RenderTexture`, `SpriteGPULayer`, or `TilemapGPULayer`?
- What browser, mobile, DPR, pixel-art, and FPS constraints matter?

## Version And Renderer Contract

- Inspect the installed Phaser version before using version-specific APIs. Phaser 4 moved quickly, so do not rely on memory when API details matter.
- Prefer the project's installed version and local typings over generic snippets.
- Use official Phaser docs for the exact version when checking renderer, filter, shader, texture, or migration details.
- Start new Phaser 4 work with `Phaser.WEBGL` unless the project has a concrete Canvas compatibility requirement.
- Do not port Phaser 3 renderer internals, custom pipelines, masks, FX, or texture assumptions without a focused audit.
- Treat `DynamicTexture` and `RenderTexture` drawing as buffered work that usually needs explicit `render()` execution.
- Treat filters and lighting as architectural choices: they change render passes, can break batches, and are WebGL-only features.

Useful official starting points:

- `https://docs.phaser.io/api-documentation`
- `https://phaser.io/tutorials/phaser-4-rendering-concepts`
- `https://github.com/phaserjs/phaser/blob/v4.0.0/changelog/v4/4.0/CHANGELOG-v4.0.0.md`

## Reference Files

| Topic | File | Use When |
|-------|------|----------|
| Phaser 3 to 4 migration | [migration-hotspots.md](references/migration-hotspots.md) | Porting Phaser 3 code, removed APIs, renderer internals, masks, FX, math constants, or custom pipelines |
| Spritesheets, atlases, textures | [spritesheets-and-textures.md](references/spritesheets-and-textures.md) | Loading spritesheets, atlases, compressed textures, TileSprite, shaders, or texture-orientation-sensitive assets |
| Rendering and performance | [rendering-and-performance.md](references/rendering-and-performance.md) | Choosing GPU layers, filters, lighting, render targets, batching strategy, profiling, or performance fixes |

## Before Implementing

Discover the project before editing:

```bash
rg --files | rg '(^|/)(package.json|vite.config|webpack.config|src|public|assets|static|maps|tilemaps|textures|sprites)'
rg -n "\"phaser\"|from ['\"]phaser['\"]|Phaser\\.VERSION|new Phaser\\.Game|extends Phaser\\.Scene|scene:|this\\.scene\\.|this\\.load\\.|this\\.physics|this\\.anims" .
```

For migration or renderer-sensitive work, also search:

```bash
rg -n "setTintFill|tintFill|BitmapMask|GeometryMask|preFX|postFX|ColorMatrix|Phaser\\.Geom\\.Point|Math\\.TAU|Math\\.PI2|setPipeline\\(['\"]Light2D['\"]\\)|DynamicTexture|RenderTexture|TileSprite|Shader|Pipeline|WebGLRenderer|gl\\." .
```

Extract:

- Entry point, bundler, `Phaser.GameConfig`, scale mode, and renderer type.
- Scene list, scene keys, boot/preload flow, UI overlay strategy, and restart flow.
- Asset locations, loader keys, frame config, atlas JSON, tilesets, and Tiled map names.
- Physics system, collision setup, input model, camera behavior, and debug toggles.
- Existing scripts for typecheck, lint, tests, build, and dev preview.

Ask only when missing rules, controls, art direction, target platform, or migration scope would materially change the implementation.

## Workflow

1. Discover the installed version, architecture, scenes, assets, and verification scripts.
2. Classify the work as feature, bug, optimization, asset integration, or migration.
3. Choose or preserve scene ownership, state flow, physics system, and rendering path before writing code.
4. Measure assets and lock loader config before creating animations, tilemaps, UI slices, or GPU layer data.
5. Implement with standard game objects first unless the requirement justifies filters, shaders, render targets, or GPU layers.
6. Add debug visibility for fragile systems: collision bodies, tile collision, animation frame probes, bounds overlays, FPS, or batching checks.
7. Verify through scripts and browser behavior. For playable changes, run the dev server and inspect the canvas, console, transitions, input, animation, and performance.

## Rendering Path Decisions

| Path | Use When | Avoid When |
|------|----------|------------|
| Standard game objects | Most gameplay, UI, ordinary sprites, text, and interactive entities | The scene is dominated by huge counts of simple, similar quads |
| `SpriteGPULayer` | Large numbers of simple quads with predictable animation, such as starfields, dense background motion, or particle-like decoration | Members need rich gameplay logic, frequent structural edits, multiple texture sources, or constant per-member mutation |
| `TilemapGPULayer` | Very large orthographic tile layers, one tileset, high visible tile counts, or smooth filtered tile boundaries | Isometric/staggered maps, frequent tile edits without regeneration, multiple tilesets, or small ordinary maps |
| `DynamicTexture` / `RenderTexture` | Runtime compositing, capture, stamping, generated textures, multi-pass setup, or reusable rendered output | A plain sprite, atlas frame, tint, or simple animation would solve it |
| Filters / lighting | The effect is image-space, light-aware, mask-like, or visually worth the extra render passes | The same look can be achieved with art, tint, animation frames, or a cheaper object-level effect |
| Custom shaders / raw WebGL | The effect cannot be expressed with Phaser objects, filters, or supported renderer integration | The code would mutate renderer state unpredictably or rely on Phaser 3 pipeline internals |

## Physics System Decisions

| System | Use When |
|--------|----------|
| Arcade | Platformers, shooters, top-down action, tile collisions, AABB bodies, and most 2D action games |
| Matter | Irregular shapes, compound bodies, sensors, constraints, physics puzzles, or more realistic collisions |
| None | Menus, visual novels, puzzle boards, card games, static UI, and purely visual scenes |

## Core Patterns

Prefer explicit WebGL for new Phaser 4 work:

```ts
const config: Phaser.Types.Core.GameConfig = {
  type: Phaser.WEBGL,
  width: 800,
  height: 600,
  roundPixels: false,
  scale: {
    mode: Phaser.Scale.FIT,
    autoCenter: Phaser.Scale.CENTER_BOTH
  },
  physics: {
    default: 'arcade',
    arcade: { gravity: { y: 300 }, debug: false }
  },
  scene: [BootScene, MenuScene, GameScene, UIScene]
};
```

Keep scene lifecycle explicit:

```ts
class GameScene extends Phaser.Scene {
  init(data: unknown) {}
  preload() {}
  create() {}
  update(time: number, delta: number) {
    this.player.x += this.speed * (delta / 1000);
  }
}
```

Use scene transitions intentionally:

```ts
this.scene.start('GameScene', { level: 1 });
this.scene.launch('UIScene');
this.scene.pause('GameScene');
this.scene.stop('UIScene');
```

Flush render-target work deliberately:

```ts
const rt = this.add.renderTexture(0, 0, 256, 256);

rt.draw(sprite, 0, 0);
rt.render();
```

Apply object filters only after enabling them, guard availability because filters are WebGL-only, and prefer internal filters unless a full-camera effect is required:

```ts
sprite.enableFilters();

if (sprite.filters) {
  sprite.filters.internal.addGlow(0xffffff, 2, 0);
}
```

## Migration Replacements To Verify

| Phaser 3 Pattern | Phaser 4 Direction |
|------------------|--------------------|
| `sprite.setTintFill(color)` | `sprite.setTint(color).setTintMode(Phaser.TintModes.FILL)` |
| `Math.PI2` | `Math.TAU` |
| `Math.TAU` used as PI / 2 in old code | `Math.PI_OVER_2` |
| `sprite.setPipeline('Light2D')` | `sprite.setLighting(true)` |
| `preFX` / `postFX` | Phaser 4 filters |
| `BitmapMask`-style masking | Phaser 4 `Mask` filter or current filter APIs |
| `Phaser.Geom.Point` helpers | `Phaser.Math.Vector2` or new math helpers |
| Custom pipelines | Renderer `RenderNode` or supported Phaser 4 shader/filter APIs |

Read [migration-hotspots.md](references/migration-hotspots.md) before applying these mechanically.

## Capabilities And Deliverables

Use this skill to:

- Add or refactor Phaser 4 scenes, boot flows, game config, input, cameras, UI overlays, and transitions.
- Load and validate spritesheets, atlases, compressed textures, audio, tilemaps, and generated assets.
- Implement Arcade or Matter physics, collisions, overlaps, groups, pooling, and debug overlays.
- Build tilemap-driven levels from Tiled JSON with camera bounds, collision layers, object layers, and parallax.
- Choose between ordinary game objects, GPU layers, render textures, filters, lighting, and shaders.
- Migrate Phaser 3 projects toward Phaser 4 while preserving behavior and visual output.
- Profile and reduce object churn, batch breaks, fill-rate problems, memory leaks, and update-loop costs.

Deliver:

- Code edits that match the existing framework, TypeScript style, asset paths, scene keys, and naming.
- Measured asset constants or map property assumptions used by the implementation.
- A short explanation of rendering-path, physics, and migration choices.
- Verification output: scripts run, browser URL or smoke result, and any remaining risk.

## Anti-Patterns

| Anti-pattern | Why It Fails | Better |
|--------------|--------------|--------|
| Treating Phaser 4 as a drop-in Phaser 3 upgrade | Renderer, filters, masks, shaders, texture orientation, and math constants changed | Audit hotspots first, then port intentionally |
| Guessing spritesheet or atlas metadata | Off-by-one frame math causes animation corruption far from the loader config | Measure dimensions, spacing, margin, and frame names before loading |
| Starting with shaders, filters, or GPU layers | Adds render-pass cost and debugging complexity too early | Use standard objects until requirements justify advanced rendering |
| Moving gameplay entities into `SpriteGPULayer` | GPU layer speed comes from constrained members, not rich object behavior | Keep interactive entities as normal objects or physics sprites |
| Editing `TilemapGPULayer` data without regeneration | GPU-side tile data goes stale | Regenerate the layer tile data texture after edits |
| Forgetting `render()` on dynamic render targets | Queued drawing commands never appear | Call `render()` at the point the texture must update |
| Applying lighting or filters everywhere | Shader and render target changes break batches and increase fill-rate | Apply effects to visually important objects or cameras only |
| Debugging animation timing before frame metadata | Bad frame config can look like skipped or mistimed animation | Prove the frame grid first |
| Mutating renderer state with raw `gl` calls | Phaser's renderer can desynchronize | Use Phaser 4 APIs, `Extern`, filters, or render nodes intentionally |

## Variation Guidance

Vary decisions by context:

- Migration: inventory risky APIs first, preserve behavior, then modernize renderer paths selectively.
- New small game: keep scenes few, use standard objects, and verify in browser quickly.
- Larger TypeScript project: add typed scene data, typed asset keys, service modules, and focused tests.
- Mobile target: verify DPR, touch input, audio unlock, scale mode, memory, and worst-case FPS on a constrained device.
- Pixel art: measure frames, use nearest filtering where appropriate, test camera motion, and apply rounding deliberately.
- Asset-heavy game: prefer atlases or packs, preload progress, pooled objects, and stable asset key naming.
- Performance-heavy scene: profile object count, update churn, batch breakers, fill-rate, and GPU layer fit before rewriting architecture.

Avoid using one fixed game architecture for every Phaser 4 project. Let controls, level format, asset volume, target device, and renderer constraints decide the shape.

## Verification

Run the strongest project checks available without inventing unrelated tooling:

```bash
npm run typecheck
npm run lint
npm test
npm run build
npm run dev
```

For playable or visual changes, open the game and verify:

- Canvas is nonblank, correctly sized, and free of console loader errors.
- Boot, preload, scene transitions, restart, and UI overlays work.
- Input works on the target devices or viewport sizes.
- Movement uses `delta` or physics velocity and remains stable at variable frame rates.
- Collision bodies, tile collisions, object bounds, and camera bounds match the visible art.
- Animations use the intended frames without bleeding, offset rows, skipped frames, or orientation errors.
- Filters, lighting, render textures, and GPU layers render as intended and do not destroy FPS on target hardware.
- Object pools reuse inactive objects and do not leak active bodies, timers, tweens, or event listeners.

If a check cannot run, state exactly why and what risk remains.
