// GLTF Calibration Helpers (Three.js)
// Purpose: make axes, bounds, and local -Z forward direction visible during model calibration.
//
// Usage:
//   import { attachGltfCalibrationHelpers } from './gltf-calibration-helpers.mjs';
//   attachGltfCalibrationHelpers({ scene, root: modelRoot, label: 'Hero', boundsMode: 'mesh' });

import * as THREE from 'three';

const LAYER_NAME = '__gltf_calibration_helpers__';
const BOX_NAME = '__gltf_calibration_bounds__';
const GRID_NAME = '__gltf_calibration_grid__';
const CALIBRATION_NAMES = new Set([LAYER_NAME, BOX_NAME, GRID_NAME]);

const DEFAULTS = Object.freeze({
  axisSize: 0.6,
  forwardArrowLength: 1.2,
  forwardArrowColor: 0xff00ff,
  boundsColor: 0xff00ff,
  labelColor: '#ff00ff',
  labelFont: '12px ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, sans-serif',
  anchorLocal: new THREE.Vector3(0, 1.2, 0),
});

function removeNamed(parent, name) {
  if (!parent) return;
  const existing = parent.getObjectByName(name);
  if (existing) existing.parent?.remove(existing);
}

function ensureLayer(root, replaceExisting) {
  if (!replaceExisting) {
    const existing = root.getObjectByName(LAYER_NAME);
    if (existing) return existing;
  }
  removeNamed(root, LAYER_NAME);
  const layer = new THREE.Group();
  layer.name = LAYER_NAME;
  root.add(layer);
  return layer;
}

function expandGeometryBounds(root, box, { meshOnly }) {
  function walk(node) {
    if (node !== root && CALIBRATION_NAMES.has(node.name)) return;

    if (node.geometry && (!meshOnly || node.isMesh)) {
      node.geometry.computeBoundingBox();
      if (node.geometry.boundingBox) {
        const nodeBox = node.geometry.boundingBox.clone();
        nodeBox.applyMatrix4(node.matrixWorld);
        box.union(nodeBox);
      }
    }

    for (const child of node.children) walk(child);
  }

  root.updateMatrixWorld(true);
  walk(root);
  return box;
}

function computeFilteredObjectBounds(root) {
  const box = new THREE.Box3();
  return expandGeometryBounds(root, box, { meshOnly: false });
}

export function computeVisibleMeshBounds(root) {
  const box = new THREE.Box3();
  expandGeometryBounds(root, box, { meshOnly: true });

  return box.isEmpty() ? computeFilteredObjectBounds(root) : box;
}

function computeBounds(root, boundsMode) {
  return boundsMode === 'mesh'
    ? computeVisibleMeshBounds(root)
    : computeFilteredObjectBounds(root);
}

function makeLabelSprite(text, { color, font }) {
  const canvas = document.createElement('canvas');
  const ctx = canvas.getContext('2d');
  const paddingX = 10;
  const paddingY = 6;

  ctx.font = font;
  const metrics = ctx.measureText(text);
  canvas.width = Math.max(1, Math.ceil(metrics.width + paddingX * 2));
  canvas.height = Math.max(1, Math.ceil(20 + paddingY * 2));

  ctx.clearRect(0, 0, canvas.width, canvas.height);
  ctx.fillStyle = 'rgba(0,0,0,0.55)';
  ctx.fillRect(0, 0, canvas.width, canvas.height);

  ctx.font = font;
  ctx.fillStyle = color;
  ctx.textBaseline = 'middle';
  ctx.fillText(text, paddingX, canvas.height / 2);

  const texture = new THREE.CanvasTexture(canvas);
  texture.colorSpace = THREE.SRGBColorSpace;
  texture.needsUpdate = true;

  const material = new THREE.SpriteMaterial({ map: texture, transparent: true });
  const sprite = new THREE.Sprite(material);
  sprite.scale.set(1.2, 0.3, 1);
  sprite.renderOrder = 999;
  return sprite;
}

export function attachGltfCalibrationHelpers({
  scene = null,
  root,
  label = 'model',
  axisSize = DEFAULTS.axisSize,
  forwardArrowLength = DEFAULTS.forwardArrowLength,
  forwardArrowColor = DEFAULTS.forwardArrowColor,
  boundsColor = DEFAULTS.boundsColor,
  labelColor = DEFAULTS.labelColor,
  labelFont = DEFAULTS.labelFont,
  anchorLocal = DEFAULTS.anchorLocal,
  boundsMode = 'mesh',
  showGrid = false,
  gridSize = 10,
  gridDivisions = 10,
  log = true,
  replaceExisting = true,
} = {}) {
  if (!root) throw new Error('attachGltfCalibrationHelpers: missing { root }');

  if (replaceExisting) {
    removeNamed(root, LAYER_NAME);
    removeNamed(scene, BOX_NAME);
    removeNamed(scene, GRID_NAME);
  }

  root.updateMatrixWorld(true);
  const box = computeBounds(root, boundsMode);
  const layer = ensureLayer(root, replaceExisting);

  const axes = new THREE.AxesHelper(axisSize);
  layer.add(axes);

  const localForward = new THREE.Vector3(0, 0, -1);
  const arrow = new THREE.ArrowHelper(
    localForward,
    anchorLocal.clone(),
    forwardArrowLength,
    forwardArrowColor,
  );
  layer.add(arrow);

  const labelSprite = makeLabelSprite(label, { color: labelColor, font: labelFont });
  labelSprite.position.copy(anchorLocal).add(new THREE.Vector3(0, 0.45, 0));
  layer.add(labelSprite);

  const boxHelper = new THREE.Box3Helper(box, boundsColor);
  boxHelper.name = BOX_NAME;

  // Box3Helper uses world-space bounds. Add it to the scene when possible to avoid
  // applying the model root transform a second time.
  (scene || layer).add(boxHelper);

  let grid = null;
  if (showGrid && scene) {
    grid = new THREE.GridHelper(gridSize, gridDivisions, 0xffffff, 0xffffff);
    grid.material.opacity = 0.18;
    grid.material.transparent = true;
    grid.position.y = 0.001;
    grid.name = GRID_NAME;
    scene.add(grid);
  }

  const worldForward = new THREE.Vector3();
  const worldPos = new THREE.Vector3();
  const size = box.getSize(new THREE.Vector3());
  root.getWorldDirection(worldForward);
  root.getWorldPosition(worldPos);

  if (log) {
    console.log(`[calibrate] ${label}`);
    console.log('  boundsMode:', boundsMode);
    console.log('  worldPos:', worldPos.toArray());
    console.log('  bboxSize:', size.toArray());
    console.log('  worldForward(-Z):', worldForward.toArray());
  }

  return {
    layer,
    axes,
    box,
    boxHelper,
    arrow,
    grid,
    labelSprite,
    recomputeBounds(nextMode = boundsMode) {
      root.updateMatrixWorld(true);
      box.copy(computeBounds(root, nextMode));
      return box;
    },
    dispose() {
      removeNamed(root, LAYER_NAME);
      removeNamed(scene, BOX_NAME);
      removeNamed(scene, GRID_NAME);
      labelSprite.material.map?.dispose();
      labelSprite.material.dispose();
    },
  };
}
