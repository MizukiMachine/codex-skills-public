# Advanced Three.js Topics

Use this reference for post-processing, shaders, raycasting, instancing, labels, physics, and performance work.

## Post-Processing

```js
import { EffectComposer } from 'three/addons/postprocessing/EffectComposer.js';
import { RenderPass } from 'three/addons/postprocessing/RenderPass.js';
import { UnrealBloomPass } from 'three/addons/postprocessing/UnrealBloomPass.js';

const composer = new EffectComposer(renderer);
composer.addPass(new RenderPass(scene, camera));
composer.addPass(new UnrealBloomPass(
  new THREE.Vector2(width, height),
  0.8,
  0.35,
  0.85,
));

function resizePost(width, height) {
  composer.setSize(width, height);
}

renderer.setAnimationLoop(() => {
  composer.render();
});
```

Resize the composer whenever the renderer size changes. Avoid heavy bloom on mobile unless the scene budget supports it.

## ShaderMaterial

```js
const material = new THREE.ShaderMaterial({
  uniforms: {
    time: { value: 0 },
    colorA: { value: new THREE.Color(0x2df2ff) },
  },
  vertexShader: `
    varying vec2 vUv;
    void main() {
      vUv = uv;
      gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
    }
  `,
  fragmentShader: `
    uniform float time;
    uniform vec3 colorA;
    varying vec2 vUv;
    void main() {
      float wave = 0.5 + 0.5 * sin(time + vUv.x * 8.0);
      gl_FragColor = vec4(colorA * wave, 1.0);
    }
  `,
});

renderer.setAnimationLoop((time) => {
  material.uniforms.time.value = time * 0.001;
  renderer.render(scene, camera);
});
```

Use shaders when built-in materials cannot express the effect. Keep a simple material fallback while debugging.

## Raycasting

```js
const raycaster = new THREE.Raycaster();
const pointer = new THREE.Vector2();
const pickables = [];

function updatePointer(event) {
  const rect = renderer.domElement.getBoundingClientRect();
  pointer.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
  pointer.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;
}

renderer.domElement.addEventListener('pointerdown', (event) => {
  updatePointer(event);
  raycaster.setFromCamera(pointer, camera);
  const [hit] = raycaster.intersectObjects(pickables, true);
  if (hit) selectObject(hit.object);
});
```

Use canvas-relative pointer coordinates, not `window.innerWidth`, when the canvas is not full-screen.

## Instancing

```js
const count = 500;
const geometry = new THREE.BoxGeometry(0.25, 0.25, 0.25);
const material = new THREE.MeshStandardMaterial({ color: 0x8fd3ff });
const instances = new THREE.InstancedMesh(geometry, material, count);
const dummy = new THREE.Object3D();

for (let i = 0; i < count; i += 1) {
  dummy.position.set(
    (Math.random() - 0.5) * 40,
    Math.random() * 8,
    (Math.random() - 0.5) * 40,
  );
  dummy.rotation.set(Math.random(), Math.random(), Math.random());
  dummy.updateMatrix();
  instances.setMatrixAt(i, dummy.matrix);
}

scene.add(instances);
```

Use `InstancedMesh` for many identical objects. Use regular meshes for independently animated skinned characters.

## Text Labels

```js
function createTextSprite(text) {
  const canvas = document.createElement('canvas');
  const ctx = canvas.getContext('2d');
  canvas.width = 256;
  canvas.height = 64;
  ctx.font = '24px system-ui, sans-serif';
  ctx.fillStyle = 'white';
  ctx.textAlign = 'center';
  ctx.textBaseline = 'middle';
  ctx.fillText(text, canvas.width / 2, canvas.height / 2);

  const texture = new THREE.CanvasTexture(canvas);
  texture.colorSpace = THREE.SRGBColorSpace;
  const material = new THREE.SpriteMaterial({ map: texture, transparent: true });
  const sprite = new THREE.Sprite(material);
  sprite.scale.set(2.5, 0.625, 1);
  return sprite;
}
```

For dense labels, consider DOM overlays if occlusion and perspective scaling are not needed.

## Physics

Use a proven physics library such as `cannon-es`, Rapier, or Ammo when gameplay depends on rigid-body behavior. Keep render meshes and physics bodies synchronized from physics to Three.js, not both directions.

```js
world.step(1 / 60, dt, 3);
mesh.position.copy(body.position);
mesh.quaternion.copy(body.quaternion);
```

Use simple collision shapes and match the same units established in the reference-frame contract.

## Performance Diagnostics

- Cap pixel ratio to `2` or lower for heavy scenes.
- Reuse geometries, materials, vectors, quaternions, and matrices.
- Prefer instancing or merged geometry for many static/repeated objects.
- Avoid dynamic shadows on large crowds or particle-heavy scenes.
- Use lower segment counts unless close-up silhouettes need detail.
- Pause or reduce animation work when the scene is hidden.
- Dispose resources on teardown when ownership is clear.

## Useful Debug Helpers

```js
scene.add(new THREE.GridHelper(10, 10));
scene.add(new THREE.AxesHelper(2));
scene.add(new THREE.Box3Helper(new THREE.Box3().setFromObject(object), 0xff00ff));
```

Remove helpers or put them behind a debug flag before final delivery.
