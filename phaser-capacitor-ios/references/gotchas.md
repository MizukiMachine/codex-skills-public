# Gotchas and Fast Fixes for Capacitor iOS Phaser Games

## Browser Works but Simulator/Device Fails

Common causes:
- stale native web assets
- `webDir` mismatch
- bad static asset path
- production build accidentally using `server.url`
- Phaser loader error hidden from normal terminal output
- WKWebView console error not visible in the terminal

Fix:
1. `npm run build`
2. `npx cap sync ios`
3. confirm `capacitor.config.*` uses the actual output dir, usually `webDir: 'dist'`
4. use `/assets/...` URLs for files under `public/assets`
5. remove `server.url` unless live reload is intentional
6. inspect the WebView with Safari Develop tools

## Blank or Black Canvas

Common causes:
- the Phaser parent element has zero height
- CSS allows the page to scroll while the canvas is offscreen or clipped
- missing `viewport-fit=cover` when safe-area layout is expected
- asset preload failed before the first scene started
- WebGL context failed or was lost
- game code ran before the DOM container existed

Fix:
- set `html`, `body`, and the Phaser parent to `width: 100%; height: 100%; margin: 0; overflow: hidden`
- confirm `new Phaser.Game(config)` runs after the container exists
- add `viewport-fit=cover` when using safe-area inset layout
- add `this.load.on('loaderror', ...)` in the preload scene
- inspect WebView console with Safari Develop tools
- capture simulator/device screenshots and verify pixels, not just app launch

## Assets Load in Dev but Not iOS

Common causes:
- relative paths depend on Vite dev server routing
- asset files are outside `public/` and not imported into the bundle
- case mismatch in filenames
- Tiled map references tilesets or images using paths that do not exist in the built app
- audio format is unsupported or not tested in WKWebView

Fix:
- move runtime files to `public/assets` or import them through Vite
- load public files with `/assets/...`
- check filename case exactly
- inspect generated `dist` contents
- update Tiled tileset/image paths to match bundled output
- include the audio formats already supported by the project and test on device

## Touch Controls Scroll, Zoom, or Sit Under the Home Indicator

Common causes:
- missing `touch-action: none`
- body or container has scrollable overflow
- too few active pointers for virtual controls
- UI scene and gameplay scene both handle the same pointer
- controls ignore `env(safe-area-inset-*)`

Fix:
- set `touch-action: none` on the canvas or parent
- set `overflow: hidden` on `html`, `body`, and parent container
- configure `input.activePointers` or call `this.input.addPointer(...)`
- make UI/gameplay input ownership explicit
- keep HUD and controls away from notch and home indicator safe areas

## Audio Does Not Play

Common causes:
- audio starts before a user gesture
- app resumes while sounds remain paused
- unsupported audio format
- silent-mode expectations were not tested on device
- backgrounding leaves music/timers in an inconsistent state

Fix:
- start or resume audio inside a first `pointerdown`/gesture path
- listen for Phaser sound unlock events when needed
- pause audio on Capacitor `pause`
- resume intentionally on `resume`
- test on real device when silent switch or audio focus matters

## Scale, Orientation, or Pixel Art Looks Wrong

Common causes:
- Phaser scale mode was chosen for desktop only
- canvas CSS, viewport metadata, and Phaser scale config disagree
- high iOS DPR makes rendering too expensive
- pixel art uses smoothing or non-integer-friendly scaling
- Xcode orientation policy differs from game assumptions

Fix:
- choose `FIT`, `RESIZE`, or a custom scale strategy intentionally
- align CSS container dimensions and viewport metadata with Phaser config
- cap `resolution` for high-DPI screens
- set `pixelArt: true` and check camera rounding for pixel art
- update iOS orientation policy only when it matches product behavior

## Game Freezes or Breaks After Backgrounding

Common causes:
- simulation timers keep running while app is paused
- audio is paused but not resumed deliberately
- WebGL context loss or custom renderer resources are not handled
- scene restarts duplicate event listeners

Fix:
- use `@capacitor/app` `pause`, `resume`, or `appStateChange` listeners
- pause gameplay and audio on backgrounding
- wake the game loop and resume audio intentionally
- clean scene event listeners on shutdown
- inspect Safari Web Inspector console after returning to the app

## Capacitor Asks for CocoaPods or Xcode Shape Looks Wrong

Common causes:
- project was created with an older Capacitor template
- SPM and CocoaPods assumptions are mixed
- plugin does not support SPM cleanly
- generated `CapApp-SPM` files were edited manually

Fix:
- use one package manager strategy per project
- for modern projects, add iOS with `npx cap add ios --packagemanager SPM`
- for existing CocoaPods projects, migrate intentionally with `npx cap spm-migration-assistant` or recreate `ios/` after backing up native changes
- do not edit generated SPM package internals; let `npx cap sync ios` manage them

## Xcode Build, Signing, or Package Resolution Fails

Common causes:
- wrong Xcode version for the Capacitor major version
- Command Line Tools not selected
- stale Derived Data
- signing team/bundle id mismatch
- package resolution cache is stale
- missing `Info.plist` usage strings or capabilities for plugins

Fix:
- verify `xcode-select -p`
- run `npx cap doctor`
- open with `npx cap open ios`
- use Xcode Product > Clean Build Folder
- remove Derived Data only after simpler checks
- resolve packages in Xcode
- verify bundle id, team, provisioning, capabilities, and permission strings

## Plugin Not Implemented on iOS

Common causes:
- plugin installed in `package.json` but not synced into native project
- using a plugin that does not support the selected package manager
- missing permission strings or capabilities

Fix:
- run `npx cap sync ios`
- inspect package dependencies or CocoaPods integration depending on project type
- confirm required `Info.plist` usage strings
- confirm Signing & Capabilities match plugin requirements

## Phaser Is Slow or Janky on iOS

Common causes:
- effective render resolution is too high
- many small textures or draw calls
- objects, text, graphics, sounds, or tweens are created every frame
- particle counts, render textures, filters, lighting, or post-processing are too expensive
- update logic is frame-count based instead of delta-time based
- thermal throttling or low-power mode changes device behavior

Fix:
- cap Phaser `resolution`
- use atlases where appropriate
- pool frequently spawned objects
- avoid per-frame allocation
- profile the busiest scene on simulator and real device when possible
- use delta time or physics velocities for movement
