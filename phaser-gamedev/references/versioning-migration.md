# Phaser Versioning and Migration

Use this reference when a task depends on Phaser 3 vs Phaser 4 behavior, when upgrading an existing game, or when errors mention renderer, filters, masks, tint, camera, DynamicTexture, RenderTexture, plugins, or removed APIs.

## Contents

- [Version Discovery](#version-discovery)
- [Decision Rules](#decision-rules)
- [Phaser 3 Baseline](#phaser-3-baseline)
- [Phaser 4 Migration Notes](#phaser-4-migration-notes)
- [Migration Workflow](#migration-workflow)
- [Verification Checklist](#verification-checklist)

## Version Discovery

Use project-local evidence before changing code:

```bash
rg -n "\"phaser\"|Phaser\\.VERSION|from ['\"]phaser['\"]|import Phaser" . -g 'package.json' -g '*lock*' -g 'src/**' -g 'public/**' -g 'assets/**'
```

If this returns no matches, inspect vendored bundles, HTML script tags, CDN URLs, and build output. If the game runs, log or inspect `Phaser.VERSION` in the browser console.

## Decision Rules

| Situation | Action |
|-----------|--------|
| Existing game on Phaser 3 and user asks for a feature | Stay on Phaser 3 unless the feature requires v4 or the user asks to migrate. |
| Existing game on Phaser 4 | Use current v4 docs and avoid v3 renderer internals. |
| Unknown version | Stop API-sensitive edits until the version is discovered. |
| Custom WebGL pipelines or shaders | Treat migration as high risk. Inventory rendering code before changing gameplay. |
| Standard sprites, text, tilemaps, and Arcade physics | Migration is often mostly mechanical, but still verify scene by scene. |

## Phaser 3 Baseline

Phaser 3 projects commonly rely on:
- `Phaser.AUTO` with Canvas fallback.
- WebGL pipelines and v3 FX/mask APIs.
- `setTintFill()` or v3 tint behavior.
- Camera behavior and `roundPixels` assumptions that may differ in v4.
- Immediate DynamicTexture or RenderTexture drawing patterns.

When staying on Phaser 3, use documentation for the installed minor version where possible. Do not copy v4-only APIs into v3 code.

## Phaser 4 Migration Notes

These notes reflect the Phaser 4.0/4.1 migration surface current to May 2026. Before making real migration edits, verify exact APIs against the official Phaser docs or changelog for the installed minor version.

Phaser 4 is not a full gameplay API rewrite, but the renderer changed substantially. Expect issues around:

- Renderer internals: v3 pipelines are replaced by render nodes.
- Canvas fallback: focus on WebGL unless the project explicitly requires Canvas.
- FX and masks: v4 unifies these into filters.
- Tinting: check `setTintFill()` and tint mode usage.
- Lighting: v4 has a simplified lighting model.
- Camera behavior: verify camera effects, bounds, scrolling, and pixel rounding.
- Texture orientation: compressed textures may need re-exporting.
- DynamicTexture and RenderTexture: verify render timing if output is blank.
- Removed pieces: Mesh, Plane, Camera3D, Layer3D, old bundled Spine plugins, and old browser polyfills may need replacement or scope changes.

Prefer official Phaser migration docs for exact before/after APIs during real migrations.

## Migration Workflow

1. Create an inventory of Phaser usage:

```bash
rg -n "pipeline|preFX|postFX|mask|setTintFill|DynamicTexture|RenderTexture|Camera3D|Layer3D|Mesh|Plane|Spine|roundPixels|Struct\\.|TileSprite|lighting|setPipeline" . -g 'src/**' -g 'public/**' -g 'assets/**'
```

2. Upgrade or inspect the dependency in an isolated branch or small commit.
3. Run the game and let runtime/type errors form the first task list.
4. Fix renderer/filter/camera/tint issues before gameplay tuning.
5. Verify asset rendering, tilemaps, collisions, UI overlays, and screen scaling.

## Verification Checklist

- Dependency resolves to the intended Phaser major and minor.
- Game boot reaches the first playable scene without console errors.
- Sprites, atlases, tilemaps, bitmap fonts, and UI panels render correctly.
- Camera follow, bounds, zoom, fades, and pixel rounding match the old behavior.
- Custom renderer code, filters, masks, tint, and lighting have been manually checked.
- DynamicTexture or RenderTexture output is nonblank.
- Build, typecheck, and browser smoke test have been run.
