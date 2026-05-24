# GLTF/GLB Loading Guide

Use this reference when loading, normalizing, animating, cloning, or disposing GLTF/GLB assets.

## Imports

```js
import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import * as SkeletonUtils from 'three/addons/utils/SkeletonUtils.js';
```

Use `DRACOLoader`, `KTX2Loader`, or meshopt decoders only when the asset requires them.

## Async Loading Pattern

```js
const loader = new GLTFLoader();

async function loadGltf(path) {
  const gltf = await loader.loadAsync(path);

  gltf.scene.traverse((child) => {
    if (!child.isMesh) return;
    child.castShadow = true;
    child.receiveShadow = true;
  });

  return gltf;
}
```

For production UI, wrap this with loading/error state and an explicit fallback mesh if the model is optional.

## Cache And Clone

Load once and clone for repeated instances. Use `SkeletonUtils.clone()` for animated or skinned models; regular `.clone()` can leave skinned mesh bones referencing the original.

```js
class GltfCache {
  constructor() {
    this.loader = new GLTFLoader();
    this.cache = new Map();
  }

  async load(path) {
    if (!this.cache.has(path)) {
      const gltf = await this.loader.loadAsync(path);
      this.cache.set(path, gltf);
    }
    return this.cache.get(path);
  }

  async createInstance(path) {
    const gltf = await this.load(path);
    const animated = gltf.animations.length > 0;
    const root = animated ? SkeletonUtils.clone(gltf.scene) : gltf.scene.clone(true);
    return { root, animations: gltf.animations };
  }
}
```

Each animated instance needs its own `AnimationMixer`.

## Animation Setup

```js
function createAnimationActions(root, clips) {
  const mixer = new THREE.AnimationMixer(root);
  const actions = new Map();

  for (const clip of clips) {
    actions.set(clip.name.toLowerCase(), mixer.clipAction(clip));
  }

  return { mixer, actions };
}
```

Log clip names once. Prefer exact names, then explicit fallback aliases. Avoid blindly playing `animations[0]`; the first clip might be a death, hit, or transition animation.

## Safe Clip Selection

```js
function selectSafeClip(clips, preferred = ['idle', 'walk', 'run']) {
  const safe = clips.filter((clip) => {
    const name = clip.name.toLowerCase();
    return !name.includes('death') && !name.includes('die') && !name.includes('dead');
  });

  for (const token of preferred) {
    const match = safe.find((clip) => clip.name.toLowerCase() === token)
      || safe.find((clip) => clip.name.toLowerCase().includes(token));
    if (match) return match;
  }

  return safe[0] || clips[0] || null;
}
```

## Mesh-Only Normalization

Use mesh-only bounds when skeletons or armatures inflate `Box3.setFromObject()`.

```js
function visibleBounds(root) {
  root.updateMatrixWorld(true);
  const box = new THREE.Box3();

  root.traverse((child) => {
    if (!child.isMesh || !child.geometry) return;
    child.geometry.computeBoundingBox();
    const meshBox = child.geometry.boundingBox.clone();
    meshBox.applyMatrix4(child.matrixWorld);
    box.union(meshBox);
  });

  return box.isEmpty() ? new THREE.Box3().setFromObject(root) : box;
}

function normalizeVisibleHeight(root, targetHeight, anchor = 'minY') {
  root.position.set(0, 0, 0);
  root.updateMatrixWorld(true);

  const box = visibleBounds(root);
  const size = box.getSize(new THREE.Vector3());
  if (size.y > 0) root.scale.multiplyScalar(targetHeight / size.y);

  root.updateMatrixWorld(true);
  const scaled = visibleBounds(root);
  root.position.y += anchor === 'maxY' ? -scaled.max.y : -scaled.min.y;
  root.updateMatrixWorld(true);
}
```

## Compression

Draco:

```js
import { DRACOLoader } from 'three/addons/loaders/DRACOLoader.js';

const draco = new DRACOLoader();
draco.setDecoderPath('/draco/');
loader.setDRACOLoader(draco);
```

KTX2 textures:

```js
import { KTX2Loader } from 'three/addons/loaders/KTX2Loader.js';

const ktx2 = new KTX2Loader().setTranscoderPath('/basis/');
ktx2.detectSupport(renderer);
loader.setKTX2Loader(ktx2);
```

Use local decoder/transcoder paths when the project has build assets; use CDN paths only when appropriate for the app.

## Disposal

When removing model instances that own their resources:

```js
root.traverse((child) => {
  if (!child.isMesh) return;
  child.geometry?.dispose();
  const materials = Array.isArray(child.material) ? child.material : [child.material];
  for (const material of materials) {
    for (const value of Object.values(material)) {
      if (value && value.isTexture) value.dispose();
    }
    material.dispose();
  }
});
```

Do not dispose shared cached resources while other instances still use them.

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| 404 or CORS error | Serve over HTTP and verify asset paths relative to the hosted page or public root |
| Model is black | Add lights or use an unlit debug material |
| Model is too large/small | Normalize visible bounds and lock target units |
| Character floats | Use mesh-only bounds and anchor to `minY` |
| Cloned character sticks at origin | Use `SkeletonUtils.clone()` and one mixer per instance |
| Animations do not play | Log clip names, create mixer for the displayed root, update mixer each frame |
