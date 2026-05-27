# Three.js Scene Patterns

Use this reference for basic scene creation, blank-scene debugging, imports, controls, lighting, materials, and responsive rendering.

## Import Strategy

Use the project's installed `three` package when a build tool exists:

```js
import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
```

For standalone HTML, use an import map. Pin one version and use the same CDN for `three` and `three/addons/`. The example is copyable; when an existing project already pins Three.js, match that project version instead:

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

Avoid global `THREE.OrbitControls`; addons are explicit ES module imports.

## Minimal Runtime Skeleton

```js
import * as THREE from 'three';

let canvas = document.querySelector('#scene');
if (!canvas) {
  canvas = document.createElement('canvas');
  canvas.id = 'scene';
  document.body.appendChild(canvas);
}

const scene = new THREE.Scene();
scene.background = new THREE.Color(0x101014);

const camera = new THREE.PerspectiveCamera(55, 1, 0.1, 200);
camera.position.set(4, 3, 6);
camera.lookAt(0, 0.8, 0);

const renderer = new THREE.WebGLRenderer({ canvas, antialias: true });
renderer.outputColorSpace = THREE.SRGBColorSpace;
renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));

function resize() {
  const parent = canvas.parentElement || document.body;
  const width = Math.max(1, parent.clientWidth);
  const height = Math.max(1, parent.clientHeight);
  renderer.setSize(width, height, false);
  camera.aspect = width / height;
  camera.updateProjectionMatrix();
}

window.addEventListener('resize', resize);
resize();

const ambient = new THREE.AmbientLight(0xffffff, 0.45);
scene.add(ambient);

const key = new THREE.DirectionalLight(0xffffff, 1.2);
key.position.set(4, 8, 5);
scene.add(key);

const geometry = new THREE.BoxGeometry(1, 1, 1);
const material = new THREE.MeshStandardMaterial({ color: 0x45c4ff, roughness: 0.55 });
const mesh = new THREE.Mesh(geometry, material);
scene.add(mesh);

renderer.setAnimationLoop((time) => {
  mesh.rotation.y = time * 0.001;
  renderer.render(scene, camera);
});
```

## Framework Cleanup Pattern

For React/Vue/Svelte/route components, always clean up:

```js
renderer.setAnimationLoop(null);
window.removeEventListener('resize', resize);
controls?.dispose();
renderer.dispose();
geometry.dispose();
material.dispose();
```

Dispose textures, render targets, post-processing composers, and cloned model resources when ownership is clear.

## Render Cadence Selection

Choose one owner for rendering:

| Cadence | Use When | Pattern |
|---------|----------|---------|
| Continuous `setAnimationLoop` | Viewer controls, auto-rotation, animation mixers, shaders, particles, WebXR | Update time-based state and render every frame |
| App/game `requestAnimationFrame` owner | A game engine already owns timing, input, scoring, physics, or pause state | Advance game state in the engine loop and call the renderer once per tick or when state changes |
| On-demand render | Turn-based tools, editors, configurators, mostly static scenes | Render after input, resize, asset load, or short effect updates |

Avoid mixing multiple continuous loops unless their ownership is explicit. Short effects may use their own `requestAnimationFrame`, but they must cancel on dispose and render through the same renderer/camera contract.

## Canvas Layout And DOM Overlays

When the canvas shares the screen with DOM UI:

- Size the renderer from the canvas parent or a measured host element, not from `window.innerWidth` unless the canvas is truly full-screen.
- Update camera aspect/frustum after layout changes and after CSS changes that alter the host size.
- Keep passive HUD layers from intercepting input with `pointer-events: none`; enable pointer events only on actual controls.
- Prefer DOM for menus, forms, long text, toolbars, HUD labels, and accessibility. Prefer WebGL for spatial cues, highlights, markers, particles, and objects that must occlude correctly in the scene.
- If panels reserve part of the viewport, adjust camera framing or scene host transforms deliberately and verify desktop/mobile screenshots.

## Lighting Choices

| Goal | Pattern |
|------|---------|
| Simple visible scene | `AmbientLight` plus one `DirectionalLight` |
| Product viewer | Key/fill/rim lights or HDR environment map |
| Toon/game look | Hemisphere or ambient fill, strong directional key, flat colors |
| Debug unlit geometry | `MeshBasicMaterial` or `MeshNormalMaterial` |
| Shadows | Enable renderer shadow map, light shadow, mesh cast/receive flags |

No light means `MeshStandardMaterial`, `MeshPhysicalMaterial`, and other lit materials render black.

## Material Selection

| Material | Use |
|----------|-----|
| `MeshBasicMaterial` | Unlit UI, labels, sky planes, debug visibility |
| `MeshStandardMaterial` | Default PBR surfaces |
| `MeshPhysicalMaterial` | Clearcoat, glass, transmission, high-end product surfaces |
| `MeshNormalMaterial` | Debug normals and orientation |
| `ShaderMaterial` | Custom visual effects when built-in materials cannot express the effect |

If a GLTF uses atlas textures, avoid multiplying `material.color` unless the pack expects tinting.

## Orbit Controls

```js
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';

const controls = new OrbitControls(camera, renderer.domElement);
controls.enableDamping = true;
controls.target.set(0, 0.8, 0);
controls.update();

renderer.setAnimationLoop(() => {
  controls.update();
  renderer.render(scene, camera);
});
```

Use OrbitControls for viewers and showcases. For games, prefer a fixed or constrained camera controlled by game state.

## Shadows

```js
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFSoftShadowMap;

key.castShadow = true;
key.shadow.mapSize.set(1024, 1024);
key.shadow.camera.near = 1;
key.shadow.camera.far = 40;

mesh.castShadow = true;
floor.receiveShadow = true;
```

Shadows are expensive. Keep map sizes bounded and only enable cast/receive on objects that need it.

## Blank Canvas Checklist

1. Browser console has no module import, CORS, MIME, or WebGL errors.
2. Canvas parent has nonzero width and height.
3. Renderer size and camera aspect update after layout.
4. Camera points at visible geometry and near/far planes include it.
5. Lit materials have lights; unlit debug material renders if lighting is suspect.
6. Object was added to the scene and is not behind the camera or scaled to zero.
7. Static GLTF/texture files are served over HTTP, not `file://`.
8. DOM overlays are not hiding the scene or intercepting required pointer events.
