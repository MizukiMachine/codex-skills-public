---
name: threejs-builder
description: "Three.js/WebGLのWeb体験を構築・デバッグ・改善する。GLTF/GLB、アニメーション、OrbitControls、照明・マテリアル、シェーダー、3Dゲーム、視覚検証で使う。"
---

# Three.js Builder

## Purpose

Use this skill to produce working, responsive Three.js experiences with correct imports, stable scene setup, calibrated 3D reference frames, and real browser verification. The output should be a usable scene, game, viewer, or fix, not a decorative code sample.

## Operating Model

Three.js work is scene-graph work plus rendering verification. Every visible result depends on five contracts being correct: module loading, camera/framing, lighting/materials, object transforms, and canvas/layout integration.

Prioritize:

1. A nonblank rendered canvas in the user's actual project/runtime
2. Correct reference frames: axes, forward direction, anchors, units, and camera basis
3. Project-native integration before standalone snippets
4. Performance through reuse, capped pixel ratio, and bounded draw calls
5. Correct ownership of render cadence, input routing, and DOM overlays
6. Visual polish that fits the requested scene, game, or product viewer

Before acting, establish:

- Existing stack: npm/Vite/React/Next/static HTML, installed `three` version, asset paths, and available scripts
- Scene purpose: showcase, product viewer, game, background, data visualization, or debugging/calibration
- Asset constraints: procedural primitives, GLTF/GLB, textures/HDRs, animation clips, compression, and expected scale
- UI integration: full-bleed canvas, embedded component, DOM HUD, toolbars, modals, labels, safe areas, and pointer/keyboard ownership
- Verification target: dev server URL, static file, screenshots, interaction test, or build command

## Reference Files

Read only the files needed for the current task.

| Topic | File | Use When |
|-------|------|----------|
| Scene setup | [scene-patterns.md](references/scene-patterns.md) | Creating the renderer/camera/lights/materials, choosing imports, adding controls, or fixing a blank basic scene |
| GLTF/GLB models | [gltf-loading-guide.md](references/gltf-loading-guide.md) | Loading models, caching/cloning, SkeletonUtils, animations, Draco/KTX2, normalization, or disposal |
| Reference frames | [reference-frame-contract.md](references/reference-frame-contract.md) | Fixing orientation, anchors, scale, camera-relative movement, floating models, inverted controls, or color-space issues |
| Game patterns | [game-patterns.md](references/game-patterns.md) | Building Three.js games, animation state machines, fixed cameras, object pools, time scaling, DOM HUD sync, and terminal states |
| Advanced topics | [advanced-topics.md](references/advanced-topics.md) | Adding post-processing, shaders, raycasting, instancing, physics, labels, or performance diagnostics |
| GLTF calibration helper | [install-gltf-calibration-helpers.py](scripts/install-gltf-calibration-helpers.py) | Installing the bundled helper into a project to visualize axes, bounds, forward direction, and model labels |

## Workflow

1. Discover the project shape before editing.
   - Use `rg --files | rg '(^|/)(package.json|vite|next|src|app|pages|components|public|assets|static|models|textures|index.html)'`.
   - Inspect package scripts, Three.js imports, render loops, and UI layers with `rg -n "from ['\"]three|GLTFLoader|OrbitControls|WebGLRenderer|setAnimationLoop|requestAnimationFrame|ResizeObserver|pointer-events|data-role|HUD|ui-layer|scene-layer" .`.
   - Prefer the installed `three` package and existing build tool. For standalone static HTML, use an import map and pin one Three.js version consistently for core and addons.

2. Choose the smallest durable implementation path.
   - Existing app: integrate in its component/module style, clean up renderer/listeners on unmount, and avoid global side effects.
   - Static page: create a minimal `index.html` plus module code or inline module script.
   - Game: define state, input, render cadence, camera convention, DOM HUD ownership, and terminal latches before adding effects.
   - GLTF work: calibrate one model first, then scale to many models.

3. Build the scene contract.
   - Renderer: antialias only when needed, `setPixelRatio(Math.min(devicePixelRatio, 2))`, parent-based resize handling, and `outputColorSpace = THREE.SRGBColorSpace`.
   - Camera: position, target, near/far planes, responsive aspect/frustum update, and composition offsets when DOM UI occupies screen space.
   - Lighting/materials: enough illumination for non-Basic materials; preserve atlas texture color unless intentionally tinting.
   - Scene graph: group related objects, reuse geometries/materials, and keep per-frame code to transforms/state updates.

4. Implement interaction and animation.
   - Use one render owner. Prefer `renderer.setAnimationLoop` for continuous animation, WebXR, or viewer controls; use a game engine `requestAnimationFrame` or on-demand `renderFrame()` path when state changes drive rendering.
   - Use `THREE.Clock` and clamp large `dt` values for games.
   - Update `OrbitControls` only when damping/auto-rotate requires it.
   - Keep DOM HUD, menus, and form controls outside the WebGL scene when they need accessibility, localization, focus, or long text.
   - Avoid object allocation, geometry creation, and loader calls inside the frame loop.

5. Verify in a real browser.
   - Run the repo's available `lint`, `typecheck`, `test`, and `build` scripts as relevant.
   - Start the dev server when the app needs one, or a simple local server for static GLTF/CDN imports.
   - Capture desktop and mobile screenshots for user-facing scenes.
   - For canvas/WebGL work, confirm the canvas is nonblank, correctly framed, responsive, animated or interactive as requested, and free of console errors.
   - When DOM overlays are present, verify they do not hide critical 3D content, pointer events reach the intended layer, and keyboard focus does not break gameplay or controls.

## Core Patterns

Use modern ES modules:

```js
import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
```

For CDN/static HTML, use an import map and keep every Three.js URL on the same version and CDN. The example is copyable; when a project already has a Three.js version, match that version instead of mixing versions:

```html
<script type="importmap">
{
  "imports": {
    "three": "https://cdn.jsdelivr.net/npm/three@0.160.0/build/three.module.js",
    "three/addons/": "https://cdn.jsdelivr.net/npm/three@0.160.0/examples/jsm/"
  }
}
</script>
```

For GLTF calibration, install the helper into the target project:

```bash
python3 /home/mizuki2/.codex/skills/threejs-builder/scripts/install-gltf-calibration-helpers.py \
  --out ./gltf-calibration-helpers.mjs
```

Then import it from the project module after normalization/yaw offsets:

```js
import { attachGltfCalibrationHelpers } from './gltf-calibration-helpers.mjs';

attachGltfCalibrationHelpers({
  scene,
  root: modelRoot,
  label: 'Hero',
  showGrid: true,
  boundsMode: 'mesh',
});
```

## Anti-Patterns

**Blank-scene guessing**

Why bad: Blank canvases usually come from import errors, camera/frustum mistakes, no lights, invisible materials, a zero-size canvas, or CORS/asset paths.

Better: Check console errors, canvas size, camera target, light/material compatibility, and actual asset network paths before rewriting the scene.

**GLTF offset roulette**

Why bad: Random `position.y` fixes accumulate and break the next model or animation.

Better: Define anchor rules by asset class, normalize once into a wrapper, and calibrate bounds/forward direction with helpers.

**Per-frame allocation**

Why bad: Creating geometries, materials, vectors, loaders, or DOM nodes in the animation loop causes garbage collection and frame drops.

Better: Allocate reusable objects once and mutate transforms or buffer attributes in the loop.

**Competing render loops**

Why bad: Running `setAnimationLoop`, a game `requestAnimationFrame`, and ad hoc effect loops without ownership can double-render, desynchronize HUD state, or keep rendering after disposal.

Better: Pick one continuous loop owner, or make the renderer event-driven with short owned rAF effects. Dispose or cancel every loop path.

**Canvas/HUD drift**

Why bad: A correctly rendered scene can still be unusable when DOM panels cover the subject, pointer events are intercepted, or resize logic reads the wrong element.

Better: Treat canvas layout, camera composition, safe zones, and DOM HUD z-index/pointer rules as part of the Three.js integration contract.

**Generic 3D demo**

Why bad: A default cube with default lighting ignores whether the user asked for a game, product viewer, background, or visualization.

Better: Choose camera, materials, motion, controls, and density around the requested use case.

## Variation Guidance

Vary based on:

- Product viewer: realistic lighting, PBR materials, orbit controls, loading state, bounded zoom, neutral background
- Game: fixed or constrained camera, snappy input, state machine, pooled objects, clear collision/debug views, DOM HUD for readable controls/status, WebGL cues for spatial state
- Showcase/portfolio: cinematic composition, intentional palette, subtle motion, responsive framing
- Data visualization: readable scale, labels, raycast selection, consistent color legend, performance-aware instancing
- Background effect: low contrast, slow motion, reduced interaction, strict performance budget

Avoid converging on:

- The same rotating cube or particle field for every request
- Hardcoded `camera.position.z = 5` without framing the content
- Mixing CDN and npm imports or different Three.js versions
- Treating GLTF models as if they all share the same scale, origin, or forward direction

## Verification

Use the narrowest checks that prove the requested behavior:

- Build checks: `npm run lint`, `npm run typecheck`, `npm test`, `npm run build` when those scripts exist
- Runtime checks: browser console clean, network assets loaded, no WebGL context errors
- Visual checks: desktop and mobile screenshots; canvas nonblank; scene framed; no UI overlap; resize works
- Interaction checks: orbit/pointer/keyboard/touch behavior matches the request; DOM overlays do not steal input except on controls
- GLTF checks: animation clip names logged, anchors calibrated, forward direction verified, clones animate independently

## Deliverables

Return the changed files, the scene/game/viewer behavior implemented, verification commands and visual checks performed, the local URL when a dev server is running, and any remaining risk such as missing assets or an untested browser path.
