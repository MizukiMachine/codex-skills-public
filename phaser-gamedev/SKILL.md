---
name: phaser-gamedev
description: "Phaser 3/4の2Dブラウザゲームを構築・デバッグ・最適化する。シーン、入力、物理、タイルマップ、UI、アニメーション、移行相談で使う。"
---

# Phaser Game Development

## Purpose

Use this skill to implement, debug, optimize, or migrate Phaser browser games with codebase-aware choices. Produce working game code, asset metadata, focused tests or smoke checks, and a concise summary of the Phaser version and verification performed.

## Operating Model

Phaser quality comes from three contracts: exact asset metadata, clear scene ownership, and frame-rate independent simulation.

Prioritize:
1. Correct gameplay and input feel
2. Measured asset dimensions and stable loader keys
3. Scene boundaries that keep gameplay, UI, menus, and loading separate
4. Browser/mobile performance backed by profiling or visual checks
5. Small, reversible changes that match the existing project style

Before acting, answer:
- Which Phaser major/minor is installed or vendored?
- What assets are source of truth, and what are their exact dimensions, spacing, margin, frame names, or Tiled properties?
- Which physics model fits the mechanic: Arcade, Matter, or no physics?
- Which scene owns each object, and how does state cross scene transitions?
- Which objects churn every frame or spawn/despawn often enough to need pooling?

## Version Contract

Do not assume a Phaser 3 API just because the project is a Phaser game. Inspect the installed or vendored version before using version-specific APIs.

Use local evidence first:

```bash
rg -n "\"phaser\"|from ['\"]phaser['\"]|Phaser\\.VERSION|new Phaser\\.Game" . -g 'package.json' -g '*lock*' -g 'src/**' -g 'public/**' -g 'assets/**'
```

This command may return no matches; that is a signal to inspect vendored bundles, HTML script tags, or runtime `Phaser.VERSION`, not a final conclusion.

Then apply these rules:

| Project state | Rule |
|---------------|------|
| Phaser 4.x | Prefer WebGL-focused patterns. Treat v3 renderer pipelines, masks, FX, tint fill, camera internals, and DynamicTexture timing as migration-sensitive. Read `references/versioning-migration.md`. |
| Phaser 3.x | Use the matching 3.x docs and examples. Prefer built-in `NineSlice` only for 3.60+ and check WebGL needs. |
| Unknown version | Find the dependency, vendored file banner, or `Phaser.VERSION` before editing API-sensitive code. |
| User asks for migration | Inventory removed APIs and custom rendering before changing gameplay logic. |

When current API details matter, verify against official Phaser docs for the exact major/minor rather than relying on memory.

## Before Implementing

Discover the existing project shape before writing code:

```bash
rg --files | rg '(^|/)(package.json|vite.config|src|public|assets|static|maps|tilemaps|textures|sprites)'
rg -n "class .*Scene|extends Phaser\\.Scene|scene:|this\\.scene\\.|this\\.load\\.|this\\.physics|this\\.anims|tilemap|nineslice|NineSlice|Matter|Arcade" .
```

Extract:
- Entry point and `Phaser.GameConfig`
- Scene list, scene keys, and transition flow
- Asset locations, loader keys, spritesheet frame configs, atlas formats, and Tiled map names
- Input model, camera/scale mode, physics system, and debug toggles
- Available scripts for typecheck, lint, test, build, or dev preview

Ask at most one or two questions only when missing rules, controls, art direction, or target platform would materially change the implementation.

## Workflow

1. Discover version, architecture, and assets.
2. Choose or preserve the scene and state model before adding content.
3. Measure assets and lock loader config before creating animations, tilemaps, or UI.
4. Implement gameplay with delta-time movement, explicit physics bodies, and stable object lifecycle.
5. Add debug visibility for fragile systems: collision bodies, tile collision, animation test scenes, FPS, or bounds overlays.
6. Verify with the repo's scripts and a browser smoke test when a playable surface exists.

## Reference Files

| Topic | File | Use When |
|-------|------|----------|
| Phaser 3/4 compatibility and migration | `references/versioning-migration.md` | Version-specific APIs, Phaser 3 to 4 migrations, renderer/filter/camera/tint changes |
| Spritesheets, animation frames, UI slicing | `references/spritesheets-nineslice.md` | Loading spritesheets, measuring frames, texture atlases, nine-slice panels |
| Tiled tilemaps and collision layers | `references/tilemaps.md` | Loading JSON maps, tilesets, object layers, tile collisions, cameras, parallax |
| Arcade physics tuning and pooling | `references/arcade-physics.md` | Arcade bodies, colliders, overlaps, groups, collision categories, debug rendering |
| Performance and profiling | `references/performance.md` | FPS drops, object churn, draw calls, memory leaks, update-loop costs |

## Capabilities And Deliverables

Use the skill to:
- Add or refactor Phaser scenes, game config, input, cameras, UI overlays, and scene transitions.
- Load and validate spritesheets, texture atlases, audio, tilemaps, and generated assets.
- Implement Arcade or Matter physics, collision callbacks, groups, pooling, and debug visualization.
- Build tilemap-driven levels from Tiled JSON with collision and object layers.
- Profile and reduce object churn, draw calls, memory leaks, and expensive update work.
- Migrate Phaser 3 projects toward Phaser 4 while preserving behavior.

Deliver:
- Code edits that match the existing framework, TypeScript style, asset paths, and naming.
- Any measured asset constants or map property assumptions used by the implementation.
- Verification output: scripts run, browser URL or screenshot check when applicable, and remaining risk.

## Core Patterns

### Game Configuration

```ts
const config: Phaser.Types.Core.GameConfig = {
  type: Phaser.AUTO,
  width: 800,
  height: 600,
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

### Scene Lifecycle

```ts
class GameScene extends Phaser.Scene {
  init(data: unknown) {}      // Receive data from previous scene
  preload() {}                // Load assets before create
  create() {}                 // Set up objects, physics, input
  update(time: number, delta: number) {
    this.player.x += this.speed * (delta / 1000);
  }
}
```

### Scene Transitions

```ts
this.scene.start('GameScene', { level: 1 }); // Stop current, start new
this.scene.launch('UIScene');                // Run overlay in parallel
this.scene.pause('GameScene');
this.scene.stop('UIScene');
```

## Architecture Decisions

### Physics System

| System | Use When |
|--------|----------|
| Arcade | Platformers, shooters, top-down action, and most AABB collision games |
| Matter | Physics puzzles, irregular shapes, sensors, ragdoll-like motion, constraints |
| None | Menus, visual novels, card games, puzzle UIs, and static interactive screens |

### Scene Structure

```text
scenes/
  BootScene.ts      # Preload, loading UI, global asset packs
  MenuScene.ts      # Title, options, save selection
  GameScene.ts      # Main simulation and world objects
  UIScene.ts        # HUD overlay launched in parallel
  GameOverScene.ts  # Results, restart, progression
```

Prefer scene data, registries, services, or typed game-state modules over global `window` state.

## Anti-Patterns

| Anti-pattern | Why It Fails | Better |
|--------------|--------------|--------|
| Guessing Phaser version | Phaser 3 and 4 differ in renderer, filters, camera, tint, and some texture behavior | Inspect dependency or `Phaser.VERSION` first |
| Guessing spritesheet dimensions | Off-by-one frame math silently corrupts animations | Measure dimensions, spacing, and margin before loader config |
| Loading assets in `create()` | Objects can reference unloaded textures | Load in `preload()` or a Boot scene |
| Creating objects in `update()` | Causes GC pauses and frame spikes | Pre-create or pool with groups |
| Frame counting for movement | Game speed changes with FPS | Use `delta / 1000` or physics velocity |
| One giant scene | Menus, HUD, gameplay, and transitions become coupled | Split by lifecycle and ownership |
| Matter for simple AABB collisions | Adds complexity without gameplay value | Use Arcade until irregular shapes or constraints are required |
| Invisible collision setup | Tile/body issues become guesswork | Add debug graphics or toggles during implementation |

## Variation Guidance

Vary choices by project context:
- Small jam game: keep scenes few, ship simple constants, verify in browser.
- Larger TypeScript project: add typed asset keys, typed scene data, and focused modules.
- Mobile target: verify scale mode, touch input, DPR, audio unlock, and low-power FPS.
- Pixel art: set `pixelArt`, explicit camera rounding, nearest-neighbor CSS, and stable integer scaling.
- Asset-heavy game: prefer atlases, manifests, preload progress, and pooled objects.
- Phaser 4 project: use current WebGL/filter/rendering patterns and avoid v3 renderer internals.

Avoid using the same architecture for every game. Let controls, level format, physics complexity, asset volume, and target platform decide the shape.

## Verification

Run the strongest checks available without inventing unrelated tooling:

```bash
npm run typecheck
npm run lint
npm test
npm run build
npm run dev
```

For playable changes, open the game and verify:
- Canvas is nonblank and correctly sized at desktop and mobile widths.
- Main scene starts, transitions work, and no loader errors appear in the console.
- Movement uses delta or physics velocity and feels stable at variable frame rates.
- Collision bodies, tile collision, and object bounds match the visible art.
- Animations use correct frames without bleeding, offsets, or skipped rows.
- Object pools reuse inactive objects and do not leak active bodies.
- FPS and memory remain stable during the busiest expected moment.

If a check cannot run, state exactly why and what risk remains.
