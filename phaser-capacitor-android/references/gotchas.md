# Gotchas and Fast Fixes for Capacitor Android Phaser Games

## Browser Works but Device/Emulator Fails

Common causes:
- stale native web assets
- `webDir` mismatch
- bad static asset path
- production build accidentally using `server.url`
- Phaser loader error hidden from normal terminal output
- Android WebView console error not visible in the terminal

Fix:
1. `npm run build`
2. `npx cap sync android`
3. confirm `capacitor.config.*` uses the actual output dir, usually `webDir: 'dist'`
4. use `/assets/...` URLs for files under `public/assets`
5. remove `server.url` unless live reload is intentional
6. use `chrome://inspect` to read WebView console/network/WebGL/Phaser loader errors

## Blank or Black Canvas

Common causes:
- the Phaser parent element has zero height
- CSS allows the page to scroll while the canvas is offscreen or clipped
- asset preload failed before the first scene started
- WebGL context failed or was lost
- game code ran before the DOM container existed

Fix:
- set `html`, `body`, and the Phaser parent to `width: 100%; height: 100%; margin: 0; overflow: hidden`
- confirm `new Phaser.Game(config)` runs after the container exists
- add `this.load.on('loaderror', ...)` in the preload scene
- inspect WebView console with `chrome://inspect`
- capture an emulator/device screenshot and verify pixels, not just process launch

## Assets Load in Dev but Not Android

Common causes:
- relative paths depend on Vite dev server routing
- asset files are outside `public/` and not imported into the bundle
- case mismatch in filenames
- Tiled map references tilesets or images using paths that do not exist in the built app
- audio format is unsupported or MIME handling differs

Fix:
- move runtime files to `public/assets` or import them through Vite
- load public files with `/assets/...`
- check filename case exactly
- inspect generated `dist` contents
- update Tiled tileset/image paths to match bundled output
- include the audio formats already supported by the project and test on device

## Touch Controls Scroll or Zoom the WebView

Common causes:
- missing `touch-action: none`
- body or container has scrollable overflow
- too few active pointers for virtual controls
- UI scene and gameplay scene both handle the same pointer

Fix:
- set `touch-action: none` on the canvas or parent
- set `overflow: hidden` on `html`, `body`, and parent container
- configure `input.activePointers` or call `this.input.addPointer(...)`
- make UI/gameplay input ownership explicit

## Audio Does Not Play

Common causes:
- audio starts before a user gesture
- app resumes while sounds remain paused
- unsupported audio format
- backgrounding leaves music/timers in an inconsistent state

Fix:
- start or resume audio inside a first `pointerdown`/gesture path
- listen for Phaser sound unlock events when needed
- pause audio on Capacitor `pause`
- resume intentionally on `resume`
- test on device, not only desktop Chrome

## Scale, Orientation, or Pixel Art Looks Wrong

Common causes:
- Phaser scale mode was chosen for desktop only
- canvas CSS and Phaser scale config disagree
- high Android DPR makes rendering too expensive
- pixel art uses smoothing or non-integer-friendly scaling
- Android manifest orientation differs from game assumptions

Fix:
- choose `FIT`, `RESIZE`, or a custom scale strategy intentionally
- align CSS container dimensions with Phaser config
- cap `resolution` for high-DPI screens
- set `pixelArt: true` and check camera rounding for pixel art
- update Android orientation policy only when it matches product behavior

## Game Freezes or Breaks After Backgrounding

Common causes:
- simulation timers keep running while app is paused
- audio is paused but not resumed deliberately
- WebGL context loss or custom renderer resources are not handled
- scene restarts duplicate event listeners

Fix:
- use `@capacitor/app` `pause` and `resume` listeners
- pause gameplay and audio on backgrounding
- wake the game loop and resume audio intentionally
- clean scene event listeners on shutdown
- inspect WebView console after returning to the app

## Hardware Back Button Closes the App Unexpectedly

Fix:
- add `@capacitor/app` if missing
- listen with `App.addListener('backButton', ...)`
- decide whether to close modal UI, open pause menu, pop route state, return to menu, or allow exit

Do not intercept back globally without a product rule. Android users expect back to do something predictable.

## Gradle, JDK, or SDK Errors

Common causes:
- `JAVA_HOME` points at a runtime incompatible with the project
- Android SDK path is missing
- Android Studio and Capacitor major-version requirements do not match
- Gradle cache/state is stale after dependency changes

Fix:
- compare the project against official Capacitor docs for its major version
- prefer Android Studio's configured Gradle JDK unless the project says otherwise
- create `android/local.properties` with `sdk.dir=...` or set `ANDROID_HOME`
- run `npx cap doctor`
- use Android Studio Gradle sync
- then try `cd android && ./gradlew --stop && ./gradlew clean`

## Device Not Detected

Fix:
- `adb devices` should list it
- enable Developer options and USB debugging
- accept the RSA prompt
- try a different USB cable/port if the device appears as charging-only
- for emulators, ensure the AVD platform is supported by the project's Capacitor version and hardware graphics are enabled

## WSL2 Emulator GUI Controls Do Not Respond

Common causes:
- emulator UI/tool window integration is unreliable under the WSL2 display stack
- Linux `adb` and Windows `adb.exe` are checking different ADB servers
- Windows commands are being launched from a WSL UNC current directory

Fix:
- keep the build in WSL if it already works
- run the emulator on Windows through Android Studio Device Manager or Windows `emulator.exe`
- install the WSL-built APK with Windows `adb.exe`
- convert APK paths with `wslpath -w`
- use `/mnt/c` as the working directory for PowerShell or `cmd.exe` calls from WSL

## Phaser Is Slow or Janky on Android

Common causes:
- effective render resolution is too high
- many small textures or draw calls
- objects, text, graphics, sounds, or tweens are created every frame
- particle counts, render textures, or post-processing are too expensive
- update logic is frame-count based instead of delta-time based

Fix:
- cap Phaser `resolution`
- use atlases where appropriate
- pool frequently spawned objects
- avoid per-frame allocation
- profile the busiest scene on device
- use delta time or physics velocities for movement
