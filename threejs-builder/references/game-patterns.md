# Three.js Game Patterns

Use this reference for 3D browser games, character animation switching, fixed cameras, object pools, time scaling, and update loops.

## Game Loop

```js
const clock = new THREE.Clock();
const mixers = [];

const GameState = {
  LOADING: 'loading',
  MENU: 'menu',
  PLAYING: 'playing',
  PAUSED: 'paused',
  GAME_OVER: 'game_over',
};

const state = {
  mode: GameState.LOADING,
  timeScale: 1,
  hasEnded: false,
};

function gameLoop() {
  const dt = Math.min(clock.getDelta(), 0.1);
  const gameDt = dt * state.timeScale;

  for (const mixer of mixers) mixer.update(gameDt);

  if (state.mode === GameState.PLAYING) {
    updateInput(gameDt);
    updateActors(gameDt);
    updateCollisions();
    updateScore(dt);
  }

  updateEffects(dt);
  renderer.render(scene, camera);
}

renderer.setAnimationLoop(gameLoop);
```

Keep real-time scoring/timers separate from slowed game-time motion unless the design says otherwise.

## Terminal State Latch

```js
function endGame(reason) {
  if (state.hasEnded) return;
  state.hasEnded = true;
  state.mode = GameState.GAME_OVER;
  state.endReason = reason;
}

function updateTimer(dt) {
  if (state.hasEnded) return;
  state.timeLeft = Math.max(0, state.timeLeft - dt);
  if (state.timeLeft === 0) endGame('timeout');
}
```

One path should own terminal transitions. Avoid timer, collision, UI submit, and slow-motion callbacks all changing state independently.

## Animation Switching

```js
function switchAnimation(entity, name, { loop = true, fade = 0.12, timeScale = 1 } = {}) {
  const action = entity.actions.get(name.toLowerCase());
  if (!action) return;

  if (entity.currentAction === action) {
    if (!action.isRunning()) action.play();
    return;
  }

  if (entity.currentAction) entity.currentAction.fadeOut(fade);

  action.reset();
  action.setLoop(loop ? THREE.LoopRepeat : THREE.LoopOnce, loop ? Infinity : 1);
  action.clampWhenFinished = !loop;
  action.timeScale = timeScale;
  action.enabled = true;
  action.paused = false;
  action.fadeIn(fade).play();

  entity.currentAction = action;
}
```

Do not reset an already playing action every frame; that causes frozen first frames.

## Camera-Relative Input

```js
const move = new THREE.Vector3();
const forward = new THREE.Vector3();
const right = new THREE.Vector3();
const up = new THREE.Vector3(0, 1, 0);

function getCameraBasis(camera) {
  camera.getWorldDirection(forward);
  forward.y = 0;
  forward.normalize();
  right.crossVectors(forward, up).normalize();
}

function updatePlayer(dt) {
  getCameraBasis(camera);
  move.set(0, 0, 0);

  if (input.up) move.add(forward);
  if (input.down) move.sub(forward);
  if (input.right) move.add(right);
  if (input.left) move.sub(right);

  if (move.lengthSq() > 0) {
    move.normalize();
    player.root.position.addScaledVector(move, player.speed * dt);
    player.root.rotation.y = Math.atan2(move.x, move.z);
  }
}
```

For side-scrollers, use a fixed camera and a documented model yaw offset instead of camera-relative input.

## Fixed Game Camera

```js
function setupSideCamera(width, height) {
  const camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 120);
  camera.position.set(2, 5, 16);
  camera.lookAt(2, 1, 0);
  return camera;
}
```

Use OrbitControls for debugging only when they are not part of gameplay.

## Object Pool

```js
class ObjectPool {
  constructor(create, initialSize = 20) {
    this.create = create;
    this.free = [];
    this.active = [];

    for (let i = 0; i < initialSize; i += 1) {
      const item = create();
      item.visible = false;
      this.free.push(item);
    }
  }

  spawn(position) {
    const item = this.free.pop() || this.create();
    item.position.copy(position);
    item.visible = true;
    this.active.push(item);
    return item;
  }

  despawn(item) {
    item.visible = false;
    const index = this.active.indexOf(item);
    if (index !== -1) this.active.splice(index, 1);
    this.free.push(item);
  }

  updateEach(callback) {
    for (let i = this.active.length - 1; i >= 0; i -= 1) {
      if (callback(this.active[i])) this.despawn(this.active[i]);
    }
  }
}
```

Use pools for obstacles, bullets, pickups, particles, and repeated enemies.

## Time Scaling And Effects

```js
function triggerSlowMo(factor, holdSeconds) {
  state.timeScale = factor;
  window.setTimeout(() => {
    state.timeScale = 1;
  }, holdSeconds * 1000);
}
```

Use screen flash, camera shake, squash/stretch, or zoom pulse sparingly, and keep them independent from core physics state.

## Collision Debugging

- Add visible debug bounds during calibration.
- Keep collision shapes simpler than render meshes.
- Compute collision in consistent units after model normalization.
- For fast objects, consider swept tests or smaller fixed time steps.

## Game Anti-Patterns

| Bad Pattern | Failure | Replacement |
|-------------|---------|-------------|
| Creating objects in `update` | Memory churn and jank | Pool or preallocate |
| Multiple systems ending the game | Hangs or duplicate UI | One terminal latch |
| Score multiplied by slow motion | Rewards change unexpectedly | Use real `dt` for score unless designed |
| Blind partial animation matching | Death/attack clips play as idle | Exact names plus safe fallback aliases |
| OrbitControls in gameplay | Player loses camera contract | Fixed/constrained camera |
