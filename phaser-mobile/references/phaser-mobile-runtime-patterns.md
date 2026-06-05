# Phaser Mobile Runtime Patterns for Capacitor (iOS / Android)

Use this when editing Phaser game code that must behave correctly inside a mobile WebView (iOS WKWebView or Android System WebView / Chromium).

**The web/Phaser layer is nearly identical across iOS and Android.** Platform-specific notes are called out inline; everything else applies to both.

## Discovery

Start with local evidence:

```bash
rg -n "\"phaser\"|from ['\"]phaser['\"]|Phaser\\.VERSION|new Phaser\\.Game" . -g 'package.json' -g '*lock*' -g 'src/**' -g 'public/**'
rg -n "new Phaser\\.Game|type: Phaser|scale:|scene:|extends Phaser\\.Scene|this\\.load\\.|this\\.input|this\\.sound|this\\.anims|tilemap|Matter|Arcade" src public
rg --files | rg '(^|/)(capacitor.config|vite.config|src|public|assets|static|maps|tilemaps|textures|audio|ios|android)'
```

Extract:
- Phaser major/minor.
- Entry point and `Phaser.Types.Core.GameConfig`.
- Scene keys, scene list, and transition flow.
- Asset folders, loader keys, spritesheet frame config, atlas formats, audio formats, and tilemap paths.
- Scale mode, virtual size, CSS container rules, viewport metadata, pixel-art flags, orientation assumptions, camera bounds, and (iOS) safe-area use.
- Input model, active pointer count, virtual controls, keyboard fallback, pause/resume behavior, and back/navigation rules (Android hardware back button vs iOS in-game navigation).

## Vite + Phaser + Capacitor Shape

Typical `index.html` (the `viewport-fit=cover` meta matters for iOS safe areas; it is harmless on Android):

```html
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<div id="app"></div>
<script type="module" src="/src/main.ts"></script>
```

Typical CSS:

```css
html,
body,
#app {
  box-sizing: border-box;
  width: 100%;
  height: 100%;
  margin: 0;
  overflow: hidden;
  background: #0b0d12;
}

*,
*::before,
*::after {
  box-sizing: inherit;
}

/* iOS: inset the playable area only if the design wants it.
   Full-bleed games usually keep the canvas full-screen and apply
   env(safe-area-inset-*) to HUD/virtual controls instead. */
#app {
  padding: env(safe-area-inset-top) env(safe-area-inset-right)
    env(safe-area-inset-bottom) env(safe-area-inset-left);
}

#app canvas {
  display: block;
  touch-action: none;
}
```

Typical Phaser config:

```ts
const DPR_LIMIT = 2;

const config: Phaser.Types.Core.GameConfig = {
  type: Phaser.AUTO,
  parent: 'app',
  width: 1280,
  height: 720,
  backgroundColor: '#0b0d12',
  resolution: Math.min(window.devicePixelRatio || 1, DPR_LIMIT),
  scale: {
    mode: Phaser.Scale.FIT,
    autoCenter: Phaser.Scale.CENTER_BOTH
  },
  input: {
    activePointers: 3
  },
  physics: {
    default: 'arcade',
    arcade: {
      gravity: { y: 0 },
      debug: false
    }
  },
  scene: [BootScene, PreloadScene, GameScene, UIScene]
};
```

For pixel art:
- Set `pixelArt: true`.
- Prefer integer-friendly virtual resolutions.
- Use camera rounding where appropriate.
- Check texture bleeding in atlases and tilemaps on simulator/emulator/device screenshots.

## Asset Paths

For files in `public/assets`, use stable absolute paths:

```ts
this.load.image('player', '/assets/sprites/player.png');
this.load.atlas('ui', '/assets/atlases/ui.png', '/assets/atlases/ui.json');
this.load.tilemapTiledJSON('level-1', '/assets/maps/level-1.json');
// List multiple formats so each platform's WebView can pick a supported one.
this.load.audio('jump', ['/assets/audio/jump.webm', '/assets/audio/jump.m4a', '/assets/audio/jump.mp3']);
```

Avoid:
- `file://` paths.
- URLs containing a dev-machine hostname unless live reload is intentional.
- Relative paths that depend on a nested route.
- Case mismatches that work on a permissive local filesystem but fail in Android/iOS packaging or CI.
- Audio formats that have not been tested in the target WebView (especially iOS WKWebView).

Add loader diagnostics during device debugging:

```ts
this.load.on('loaderror', (file: Phaser.Loader.File) => {
  console.error('loaderror', { key: file.key, src: file.src, type: file.type });
});
```

## Scene and Lifecycle

Keep scene responsibilities narrow:

```text
BootScene      # global setup, version/logging, device checks
PreloadScene   # loader progress, asset packs, error surface
MenuScene      # menus and settings
GameScene      # gameplay simulation
UIScene        # HUD overlay launched in parallel
PauseScene     # pause menu, Android back-button target, app background/resume target
```

Use delta time or physics velocities for movement:

```ts
update(_time: number, delta: number) {
  const seconds = delta / 1000;
  this.player.x += this.speed * seconds;
}
```

Clean up subscriptions and timers:

```ts
this.events.once(Phaser.Scenes.Events.SHUTDOWN, () => {
  this.input.off('pointerdown', this.handlePointerDown, this);
  this.time.removeAllEvents();
});
```

## Capacitor Pause and Resume (both platforms)

Use `@capacitor/app` when native lifecycle matters:

```ts
import { App } from '@capacitor/app';

export function installLifecycle(game: Phaser.Game) {
  App.addListener('pause', () => {
    game.sound.pauseAll();
    game.loop.sleep();
  });

  App.addListener('resume', () => {
    game.loop.wake();
    game.sound.resumeAll();
  });

  // iOS in particular benefits from appStateChange for backgrounding edge cases.
  App.addListener('appStateChange', ({ isActive }) => {
    if (!isActive) {
      game.sound.pauseAll();
      game.loop.sleep();
    }
  });
}
```

Adjust this to the product:
- Pause gameplay and open a pause scene for action games.
- Close modal UI or settings first for menu-heavy games.
- Pop router history only if the app has a route stack.

## Back Navigation

**Android — hardware back button.** Only register `backButton` when the game has a product rule for it. Listening for this event disables Capacitor's default back-button handling, so always route to in-game behavior, browser history, or an explicit app exit:

```ts
import { App } from '@capacitor/app';

export function installAndroidBackButton(game: Phaser.Game) {
  App.addListener('backButton', ({ canGoBack }) => {
    const scene = game.scene.getScene('UIScene');
    const event = { canGoBack, handled: false };
    scene.events.emit('android-back', event);

    if (event.handled) {
      return;
    }

    if (canGoBack) {
      window.history.back();
      return;
    }

    App.exitApp();
  });
}
```

Route it to the product:
- Pause gameplay and open a pause scene for action games.
- Close modal UI or settings first for menu-heavy games.
- Pop router history only if the app has a route stack.
- Exit the app only when there is no in-game back behavior and no route history to pop.

**iOS — no physical back button.** Model back navigation as in-game UI, gestures, menu state, or route history. Do not rely on a hardware affordance that does not exist.

## Touch Controls (and iOS Safe Areas)

Use explicit touch layout instead of relying on mouse-only logic:
- Add enough active pointers for virtual stick + action buttons.
- Keep touch target sizes usable on small phones.
- Separate UI scene input from gameplay scene input deliberately.
- Avoid page scroll and browser zoom with CSS `touch-action: none` and `overflow: hidden`.
- **Android:** treat notches and the navigation bar as layout constraints when UI sits near edges.
- **iOS:** keep critical HUD and controls out of notches, rounded corners, and the home indicator using `env(safe-area-inset-*)`.

Example multi-touch setup:

```ts
this.input.addPointer(2);

this.input.on('pointerdown', (pointer: Phaser.Input.Pointer) => {
  if (pointer.x < this.scale.width * 0.45) {
    this.virtualStick.start(pointer);
  } else {
    this.fireButton.press(pointer);
  }
});
```

## Audio Unlock

Browser and WebView audio often require a user gesture:

```ts
this.input.once('pointerdown', () => {
  if (this.sound.locked) {
    this.sound.once(Phaser.Sound.Events.UNLOCKED, () => {
      this.sound.play('music');
    });
  } else {
    this.sound.play('music');
  }
});
```

Use short, compressed audio for mobile. Include a platform-tested format when the project already uses multiple formats. Pause or mute long-running sounds during app backgrounding. On **iOS**, verify real devices when silent-mode (mute switch) behavior or audio focus matters.

## WebGL Context and Render Stability

Phaser handles common renderer setup, but mobile can still expose memory and context issues:
- Keep texture sizes appropriate for mobile GPUs.
- Avoid large render textures unless measured.
- Recreate custom pipelines or render-texture-dependent resources after context restore if used.
- Surface WebGL errors with the WebView inspector rather than guessing from a blank screen:
  - **Android:** `chrome://inspect`.
  - **iOS:** Safari Web Inspector (Develop menu).

Add canvas-level diagnostics when debugging custom rendering:

```ts
const canvas = game.canvas;
canvas.addEventListener('webglcontextlost', (event) => {
  event.preventDefault();
  console.warn('webglcontextlost');
});
canvas.addEventListener('webglcontextrestored', () => {
  console.warn('webglcontextrestored');
});
```

## Verification

For mobile-facing Phaser changes, verify:
- Production `npm run build` succeeds.
- `npx cap sync ios` / `npx cap sync android` runs after build.
- Simulator/emulator/device shows a nonblank canvas.
- Phaser loader errors are absent in the WebView console (Safari Web Inspector on iOS, `chrome://inspect` on Android).
- Touch controls work with multi-touch where required.
- Audio starts after first gesture and pauses/resumes correctly.
- Orientation and scale remain correct after rotation or resume; (iOS) safe-area layout stays correct.
- (Android) the hardware back button follows the product rule.
- FPS is stable during the busiest expected scene.
