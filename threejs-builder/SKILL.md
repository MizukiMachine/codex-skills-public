---
name: threejs-builder
description: "Three.js/WebGLのWeb体験を構築・デバッグ・改善する。GLTF/GLB、アニメーション、OrbitControls、照明・マテリアル、シェーダー、3Dゲーム、視覚検証で使う。"
---

# Three.js Builder

## 目的

correct imports、stable scene setup、calibrated 3D reference frames、real browser verification を伴う working / responsive Three.js experiences を作る。decorative code sample ではなく、usable scene、game、viewer、fix を出す。

## 基本方針

Three.js work は scene graph work と rendering verification。visible result は module loading、camera/framing、lighting/materials、object transforms、canvas/layout integration の5 contract に依存する。

優先順位:

1. ユーザーの actual project/runtime で nonblank rendered canvas
2. axes、forward direction、anchors、units、camera basis など correct reference frames
3. standalone snippets より project-native integration
4. reuse、capped pixel ratio、bounded draw calls による performance
5. render cadence、input routing、DOM overlays の ownership
6. scene、game、product viewer に合う visual polish

作業前に確認すること:

- stack: npm/Vite/React/Next/static HTML、installed `three` version、asset paths、scripts
- scene purpose: showcase、product viewer、game、background、data visualization、debugging/calibration
- assets: procedural primitives、GLTF/GLB、textures/HDRs、animation clips、compression、expected scale
- UI integration: full-bleed canvas、embedded component、DOM HUD、toolbars、modals、labels、safe areas、pointer/keyboard ownership
- verification target: dev server URL、static file、screenshots、interaction test、build command

## 参照ファイル

必要な reference だけ読む。

| Topic | File | Use When |
|-------|------|----------|
| Scene setup | [scene-patterns.md](references/scene-patterns.md) | renderer/camera/lights/materials、imports、controls、blank scene fix |
| GLTF/GLB models | [gltf-loading-guide.md](references/gltf-loading-guide.md) | loading、caching/cloning、SkeletonUtils、animations、Draco/KTX2、normalization、disposal |
| Reference frames | [reference-frame-contract.md](references/reference-frame-contract.md) | orientation、anchors、scale、camera-relative movement、floating models、inverted controls、color-space |
| Game patterns | [game-patterns.md](references/game-patterns.md) | games、state machines、fixed cameras、pools、time scaling、DOM HUD、terminal states |
| Advanced topics | [advanced-topics.md](references/advanced-topics.md) | post-processing、shaders、raycasting、instancing、physics、labels、performance diagnostics |
| GLTF calibration helper | [install-gltf-calibration-helpers.py](scripts/install-gltf-calibration-helpers.py) | axes、bounds、forward direction、model labels の helper install |

## ワークフロー

1. 編集前に project shape を調べる
   - `rg --files | rg '(^|/)(package.json|vite|next|src|app|pages|components|public|assets|static|models|textures|index.html)'`
   - `rg -n "from ['\"]three|GLTFLoader|OrbitControls|WebGLRenderer|setAnimationLoop|requestAnimationFrame|ResizeObserver|pointer-events|data-role|HUD|ui-layer|scene-layer" .`
   - installed `three` と existing build tool を優先する。static HTML では import map を使い、core/addons の version を揃える
2. 最小で durable な implementation path を選ぶ
   - existing app: component/module style に統合し、unmount で renderer/listeners を cleanup
   - static page: minimal `index.html` + module code
   - game: state、input、render cadence、camera convention、DOM HUD ownership、terminal latches を先に決める
   - GLTF: まず1 model を calibrate する
3. scene contract を作る
   - renderer: `setPixelRatio(Math.min(devicePixelRatio, 2))`、parent-based resize、`outputColorSpace = THREE.SRGBColorSpace`
   - camera: position、target、near/far、responsive aspect/frustum update、DOM UI による composition offsets
   - lighting/materials: non-Basic materials に十分な light。意図しない tint を避ける
   - scene graph: related objects を group、geometries/materials を reuse、frame loop は transforms/state updates に絞る
4. interaction / animation を実装する
   - render owner は1つ。continuous animation、WebXR、viewer controls では `renderer.setAnimationLoop` を優先
   - games では `THREE.Clock` と large `dt` clamp
   - `OrbitControls` は damping/auto-rotate 時だけ update
   - accessibility、localization、focus、long text が必要な UI は DOM HUD にする
   - frame loop 内で allocation、geometry creation、loader calls をしない
5. real browser で検証する
   - relevant scripts: lint、typecheck、test、build
   - 必要なら dev server または simple local server を起動
   - desktop/mobile screenshots
   - canvas が nonblank、framed、responsive、animated/interactive、console errors なし
   - DOM overlays が critical 3D content を隠さず、pointer/focus が正しい layer に届く

## Core Patterns

```js
import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
```

CDN/static HTML では import map を使い、Three.js URL の version と CDN を揃える。

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

GLTF calibration helper:

```bash
python3 /home/mizuki2/.codex/skills/threejs-builder/scripts/install-gltf-calibration-helpers.py \
  --out ./gltf-calibration-helpers.mjs
```

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

## 避けること

**blank-scene guessing**

問題: blank canvas は import error、camera/frustum、lighting、material、zero-size canvas、CORS/asset path など原因が多い。
改善: scene rewrite 前に console、canvas size、camera target、light/material compatibility、actual network paths を確認する。

**GLTF offset roulette**

問題: random `position.y` fixes は model や animation が変わるたびに崩れる。
改善: asset class ごとに anchor rules を決め、wrapper 内で normalize し、bounds / forward direction helper で calibrate する。

**per-frame allocation**

問題: animation loop 内で geometries、materials、vectors、loaders、DOM nodes を作ると GC と frame drops を起こす。
改善: reusable objects を先に allocate し、loop では transform や buffer attributes を mutate する。

**competing render loops**

問題: `setAnimationLoop` と ad hoc rAF effects が競合すると double-render、HUD desync、disposed 後の render が起きる。
改善: continuous loop owner を1つにし、event-driven rendering でも dispose / cancel を徹底する。

**Canvas/HUD drift**

問題: scene が正しく render されても、DOM panels が subject を隠したり pointer events を奪ったりすると usable ではない。
改善: canvas layout、camera composition、safe zones、z-index、pointer rules を integration contract として扱う。

**generic 3D demo**

問題: default cube / default lighting は game、product viewer、background、visualization などの用途を反映しない。
改善: use case に合う camera、materials、motion、controls、density を選ぶ。

## Variation Guidance

- Product viewer: realistic lighting、PBR、orbit controls、loading state、bounded zoom、neutral background
- Game: constrained camera、snappy input、state machine、pooled objects、debug views、DOM HUD
- Showcase/portfolio: cinematic composition、intentional palette、subtle motion、responsive framing
- Data visualization: readable scale、labels、raycast selection、legend、instancing
- Background effect: low contrast、slow motion、reduced interaction、strict performance budget

rotating cube / particle field、hardcoded `camera.position.z = 5`、CDN/npm version mixing、GLTF の scale/origin/forward direction の同一視に収束しない。

## 検証

- build checks: existing `npm run lint`、`npm run typecheck`、`npm test`、`npm run build`
- runtime checks: browser console clean、network assets loaded、no WebGL context errors
- visual checks: desktop/mobile screenshots、canvas nonblank、scene framed、UI overlap なし、resize works
- interaction checks: orbit/pointer/keyboard/touch、DOM overlays の input ownership
- GLTF checks: clip names、anchors、forward direction、independent clone animation

## 成果物

changed files、implemented scene/game/viewer behavior、verification commands、visual checks、dev server URL、remaining risk を報告する。
