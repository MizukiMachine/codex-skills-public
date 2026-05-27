# Reference Frame Contract

Most persistent Three.js bugs are reference-frame bugs: inverted controls, wrong-facing GLTFs, floating characters, collision offsets, or animations that appear broken because the model root is wrong.

## Contract To Lock First

Write these constants or comments before scaling the implementation:

- World axes: +X right, +Y up, and the project's chosen gameplay forward.
- Camera convention: whether input is world-relative, player-relative, or camera-relative.
- Asset forward: GLTF/GLB character packs often face local `-Z`, but verify per pack.
- Anchor rule by asset class:
  - Characters and props: visible bottom at `y = 0` (`minY` anchor).
  - Ground/tile pieces: walkable top at `y = 0` (`maxY` anchor) when appropriate.
- Units: define target heights or tile sizes in world units.
- Color output: set `renderer.outputColorSpace = THREE.SRGBColorSpace`.
- Screen composition: if DOM UI reserves space, decide whether camera framing, canvas host bounds, or a deliberate screen-space transform owns that offset. Keep world coordinates separate from layout compensation.
- State transitions: one owner for terminal states and one-way latches such as `hasEnded`.

## Axis And Forward Rules

Three.js is right-handed:

```text
      +Y up
       |
       |____ +X right
      /
     +Z toward viewer in many default diagrams
```

An `Object3D`'s forward direction is its local `-Z` axis. `root.getWorldDirection(v)` returns that world-space local `-Z` direction.

Common yaw offsets after calibration:

```js
const YAW = {
  keepDefault: 0,
  facePositiveZ: Math.PI,
  facePositiveX: -Math.PI / 2,
  faceNegativeX: Math.PI / 2,
};
```

Keep mesh-forward fixes separate from gameplay heading. Do not change input vectors to compensate for a wrong model yaw.

## 60-Second Calibration Pass

1. Add `AxesHelper`, `GridHelper`, and a visible ground datum at `y = 0`.
2. Load one representative model per asset class.
3. Show root axes, bounds, and a local `-Z` forward arrow.
4. Log animation clip names with `gltf.animations.map((a) => a.name)`.
5. Decide yaw offsets, anchor mode, and target scale constants.
6. Remove or gate debug helpers before production.

Use the bundled helper when useful:

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

## Anchoring Pattern

Normalize the imported scene once inside an anchor wrapper, then position the wrapper in world space. Use mesh-only bounds by default for GLTF characters and other animated/skinned assets; use `Box3.setFromObject()` only for static assets where helper bones or armatures do not inflate the bounds.

```js
function computeVisibleMeshBounds(root) {
  root.updateMatrixWorld(true);
  const box = new THREE.Box3();

  root.traverse((child) => {
    if (!child.isMesh || !child.geometry) return;
    child.geometry.computeBoundingBox();
    if (!child.geometry.boundingBox) return;
    const meshBox = child.geometry.boundingBox.clone();
    meshBox.applyMatrix4(child.matrixWorld);
    box.union(meshBox);
  });

  return box.isEmpty() ? new THREE.Box3().setFromObject(root) : box;
}

function normalizeToAnchor(root, { targetHeight, anchor = 'minY', bounds = computeVisibleMeshBounds }) {
  root.position.set(0, 0, 0);
  root.updateMatrixWorld(true);

  const box = bounds(root);
  const size = box.getSize(new THREE.Vector3());
  if (size.y > 0) root.scale.multiplyScalar(targetHeight / size.y);

  root.updateMatrixWorld(true);
  const scaledBox = bounds(root);
  const yOffset = anchor === 'maxY' ? -scaledBox.max.y : -scaledBox.min.y;
  root.position.y += yOffset;
  root.updateMatrixWorld(true);
}
```

For known-static assets, pass a simpler bounds function when appropriate:

```js
normalizeToAnchor(staticProp, {
  targetHeight: 1.5,
  bounds: (root) => new THREE.Box3().setFromObject(root),
});
```

## Camera-Relative Movement Basis

```js
const up = new THREE.Vector3(0, 1, 0);
const forward = new THREE.Vector3();
camera.getWorldDirection(forward);
forward.y = 0;
forward.normalize();

const right = new THREE.Vector3().crossVectors(forward, up).normalize();
```

If left/right is inverted, check cross-product order and camera convention first. If forward is visually backward, decide whether the project convention needs `forward.negate()` and document it.

## Troubleshooting Map

| Symptom | Likely Cause | First Fix |
|---------|--------------|-----------|
| Model floats or sinks | Missing anchor contract or skeleton-inflated bounds | Use mesh-only bounds and one anchor rule |
| Forward/back inverted | Asset forward differs from gameplay forward | Calibrate local `-Z`, set yaw offset |
| Left/right inverted | Wrong movement basis or camera convention | Verify cross-product order |
| Red or flat planes | Texture color space, atlas tinting, or fallback mesh | Set sRGB output and inspect materials/network |
| Game hangs near timeout | Multiple terminal paths or negative time | Clamp time and use one-way `hasEnded` latch |
| Canvas drifts under UI | Mixed transforms or zero-size parent | Center with layout, resize from parent bounds |
| Subject is hidden behind HUD | Camera framing ignores DOM safe zones | Reserve screen space or apply a deliberate composition offset and screenshot-check breakpoints |
