# Gotchas and Fast Fixes for Capacitor Phaser Games (iOS / Android)

Most failures are shared across platforms. Platform-specific causes and fixes are tagged **(iOS)** / **(Android)**; everything else applies to both. To inspect the WebView console: **Android** uses `chrome://inspect`, **iOS** uses Safari Develop tools / Web Inspector.

## Browser Works but Simulator/Emulator/Device Fails

Common causes:
- stale native web assets
- `webDir` mismatch
- bad static asset path
- production build accidentally using `server.url`
- Phaser loader error hidden from normal terminal output
- WebView console error not visible in the terminal

Fix:
1. `npm run build`
2. `npx cap sync ios` / `npx cap sync android`
3. confirm `capacitor.config.*` uses the actual output dir, usually `webDir: 'dist'`
4. use `/assets/...` URLs for files under `public/assets`
5. remove `server.url` unless live reload is intentional
6. inspect the WebView console: **Android** `chrome://inspect`, **iOS** Safari Develop tools

## Blank or Black Canvas

Common causes:
- the Phaser parent element has zero height
- CSS allows the page to scroll while the canvas is offscreen or clipped
- **(iOS)** missing `viewport-fit=cover` when safe-area layout is expected
- asset preload failed before the first scene started
- WebGL context failed or was lost
- game code ran before the DOM container existed

Fix:
- set `html`, `body`, and the Phaser parent to `width: 100%; height: 100%; margin: 0; overflow: hidden`
- confirm `new Phaser.Game(config)` runs after the container exists
- **(iOS)** add `viewport-fit=cover` when using safe-area inset layout
- add `this.load.on('loaderror', ...)` in the preload scene
- inspect the WebView console (`chrome://inspect` / Safari Develop tools)
- capture a simulator/emulator/device screenshot and verify pixels, not just process launch

## Assets Load in Dev but Not on Device

Common causes:
- relative paths depend on Vite dev server routing
- asset files are outside `public/` and not imported into the bundle
- case mismatch in filenames
- Tiled map references tilesets or images using paths that do not exist in the built app
- audio format is unsupported or not tested in the target WebView **(iOS WKWebView especially)**

Fix:
- move runtime files to `public/assets` or import them through Vite
- load public files with `/assets/...`
- check filename case exactly
- inspect generated `dist` contents
- update Tiled tileset/image paths to match bundled output
- include the audio formats already supported by the project and test on device

## Touch Controls Scroll, Zoom, or Sit Under a Safe Area

Common causes:
- missing `touch-action: none`
- body or container has scrollable overflow
- too few active pointers for virtual controls
- UI scene and gameplay scene both handle the same pointer
- **(iOS)** controls ignore `env(safe-area-inset-*)` and sit under the notch/home indicator

Fix:
- set `touch-action: none` on the canvas or parent
- set `overflow: hidden` on `html`, `body`, and parent container
- configure `input.activePointers` or call `this.input.addPointer(...)`
- make UI/gameplay input ownership explicit
- **(iOS)** keep HUD and controls away from notch and home indicator safe areas
- **(Android)** treat the navigation bar and notch as layout constraints near edges

## Audio Does Not Play

Common causes:
- audio starts before a user gesture
- app resumes while sounds remain paused
- unsupported audio format
- **(iOS)** silent-mode (mute switch) expectations were not tested on device
- backgrounding leaves music/timers in an inconsistent state

Fix:
- start or resume audio inside a first `pointerdown`/gesture path
- listen for Phaser sound unlock events when needed
- pause audio on Capacitor `pause`
- resume intentionally on `resume`
- test on device, not only desktop Chrome; **(iOS)** test real device when the silent switch or audio focus matters

## Scale, Orientation, or Pixel Art Looks Wrong

Common causes:
- Phaser scale mode was chosen for desktop only
- canvas CSS, viewport metadata, and Phaser scale config disagree
- high mobile DPR makes rendering too expensive
- pixel art uses smoothing or non-integer-friendly scaling
- native orientation policy (Android manifest / iOS Xcode) differs from game assumptions

Fix:
- choose `FIT`, `RESIZE`, or a custom scale strategy intentionally
- align CSS container dimensions (and viewport metadata) with Phaser config
- cap `resolution` for high-DPI screens
- set `pixelArt: true` and check camera rounding for pixel art
- update the native orientation policy only when it matches product behavior

## Game Freezes or Breaks After Backgrounding

Common causes:
- simulation timers keep running while app is paused
- audio is paused but not resumed deliberately
- WebGL context loss or custom renderer resources are not handled
- scene restarts duplicate event listeners

Fix:
- use `@capacitor/app` `pause`, `resume`, and (iOS) `appStateChange` listeners
- pause gameplay and audio on backgrounding
- wake the game loop and resume audio intentionally
- clean scene event listeners on shutdown
- inspect the WebView console after returning to the app

## Hardware Back Button Closes the App Unexpectedly (Android)

Fix:
- add `@capacitor/app` if missing
- listen with `App.addListener('backButton', ...)`
- decide whether to close modal UI, open pause menu, pop route state, return to menu, or allow exit

Do not intercept back globally without a product rule. Android users expect back to do something predictable. (iOS has no hardware back button — model back navigation as in-game UI or gestures.)

## Gradle, JDK, or SDK Errors (Android)

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

## Device Not Detected (Android)

Fix:
- `adb devices` should list it
- enable Developer options and USB debugging
- accept the RSA prompt
- try a different USB cable/port if the device appears as charging-only
- for emulators, ensure the AVD platform is supported by the project's Capacitor version and hardware graphics are enabled

## WSL2 Emulator GUI Controls Do Not Respond (Android)

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

See `references/windows-wsl-emulator-workflow.md` for the full workflow.

## Capacitor Asks for CocoaPods or Xcode Shape Looks Wrong (iOS)

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

## Xcode Build, Signing, or Package Resolution Fails (iOS)

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

## Plugin Not Implemented (iOS)

Common causes:
- plugin installed in `package.json` but not synced into native project
- using a plugin that does not support the selected package manager
- missing permission strings or capabilities

Fix:
- run `npx cap sync ios`
- inspect package dependencies or CocoaPods integration depending on project type
- confirm required `Info.plist` usage strings
- confirm Signing & Capabilities match plugin requirements

## Phaser Is Slow or Janky on Mobile

Common causes:
- effective render resolution is too high
- many small textures or draw calls
- objects, text, graphics, sounds, or tweens are created every frame
- particle counts, render textures, filters, lighting, or post-processing are too expensive
- update logic is frame-count based instead of delta-time based
- **(iOS)** thermal throttling or low-power mode changes device behavior

Fix:
- cap Phaser `resolution`
- use atlases where appropriate
- pool frequently spawned objects
- avoid per-frame allocation
- profile the busiest scene on device (and a real iOS device when possible)
- use delta time or physics velocities for movement
