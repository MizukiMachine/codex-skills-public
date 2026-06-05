# Gotchas and Fast Fixes for Capacitor Three.js Apps

Sections below are split into **shared** issues (apply to both Android and iOS) and
**platform-specific** issues. Start with the shared web/contract checks before opening
Android Studio or Xcode — most "works in browser, fails on device" bugs live in the web layer.

---

## Shared (Android + iOS)

### Browser Works but Device/Simulator Fails

Common causes:
- stale native web assets
- `webDir` mismatch
- bad static asset path
- production build accidentally using `server.url`
- WebView (Android System WebView / WKWebView) console error hidden from normal terminal output

Fix:
1. `npm run build`
2. `npx cap sync android` or `npx cap sync ios`
3. confirm `capacitor.config.*` uses the actual output dir, usually `webDir: 'dist'`
4. use `/assets/...` URLs for files under `public/assets`
5. remove `server.url` unless live reload is intentional
6. read WebView console/network/WebGL errors:
   - Android: `chrome://inspect`
   - iOS: Safari Develop tools

### Animation Button Does Nothing

Common causes:
- `sourceClipName` mismatch
- clip exists in a different GLB than expected
- default action id missing
- UI was hardcoded and drifted from asset metadata

Fix:
- list available `AnimationClip.name` values
- compare exact strings with `assets_index.json`
- warn at startup for unresolved entries
- build UI from metadata ids, not raw clip names

### Touch Pan/Rotate Feels Wrong or Gestures Scroll the Page

Common causes:
- missing `touch-action: none` on the canvas
- default `OrbitControls` mappings not aligned with UX
- custom pan constraint applied before `controls.update()`
- overlay UI absorbing pointer events unintentionally
- (iOS) controls placed under notch/home indicator safe areas

Fix:
- set `canvas.style.touchAction = 'none'`
- set both `mouseButtons` and `touches` explicitly
- apply pan/camera constraints after `controls.update()`
- check CSS `pointer-events` on overlays
- (iOS) use `env(safe-area-inset-*)` for edge controls

### Black Screen After Backgrounding

Common causes:
- WebGL context lost under memory pressure
- render loop kept running while backgrounded
- textures/render targets not recreated after context restore

Fix:
- listen for `webglcontextlost`, call `event.preventDefault()`, and pause rendering
- listen for `webglcontextrestored` and recreate renderer-dependent resources if needed
- pause on Capacitor `App.addListener('pause', ...)`
- resume intentionally on `App.addListener('resume', ...)`

### WebGL Is Slow or Janky on High-DPI Devices

Common causes:
- pixel ratio set to full `devicePixelRatio` (many phone screens are 3x–4x)
- expensive shadows/post-processing enabled by default
- render loop runs while tab/app is paused
- too many draw calls/material variants

Fix:
- use `renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2))`
- profile before adding post-processing
- pause on app `pause`
- batch/reuse geometry and materials where practical
- reduce texture sizes for mobile builds when assets are oversized

---

## Android-specific

### Gradle, JDK, or SDK Errors

Common causes:
- manually configured `JAVA_HOME` points at the wrong runtime
- Android SDK path is missing
- Android Studio and Capacitor major-version requirements do not match
- Gradle cache/state is stale after dependency changes

Fix:
- prefer Android Studio's bundled Gradle JDK
- if `JAVA_HOME` is required, set it to Android Studio's Gradle JDK path
- create `android/local.properties` with `sdk.dir=...` or set `ANDROID_HOME`
- run `npx cap doctor`
- use Android Studio Gradle sync
- then try `cd android && ./gradlew --stop && ./gradlew clean`

### Hardware Back Button Closes the App Unexpectedly

Fix:
- add `@capacitor/app` if missing
- listen with `App.addListener('backButton', ...)`
- decide whether to close modal UI, pop route state, reset the camera, or allow exit

Do not intercept back globally without a product rule. Android users expect back to do something predictable.

### Device Not Detected

Fix:
- `adb devices` should list it
- enable Developer options and USB debugging
- accept the RSA prompt
- try a different USB cable/port if the device appears as charging-only
- for emulators, ensure the AVD uses API 24+ and hardware GL

### WSL2 Emulator GUI Controls Do Not Respond

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

See `windows-wsl-emulator-workflow.md` for the full host-split workflow.

---

## iOS-specific

### Capacitor Asks for CocoaPods or Xcode Shape Looks Wrong

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

### Xcode Build, Signing, or Package Resolution Fails

Common causes:
- wrong Xcode version for the Capacitor major version
- Command Line Tools not selected
- stale Derived Data
- signing team/bundle id mismatch
- package resolution cache is stale

Fix:
- verify `xcode-select -p`
- run `npx cap doctor`
- open with `npx cap open ios`
- use Xcode Product > Clean Build Folder
- remove Derived Data only after simpler checks
- resolve packages in Xcode
- verify bundle id, team, provisioning, and capabilities

### Plugin Not Implemented on iOS

Common causes:
- plugin installed in `package.json` but not synced into native project
- using a plugin that does not support the selected package manager
- missing permission strings or capabilities

Fix:
- run `npx cap sync ios`
- inspect package dependencies or CocoaPods integration depending on project type
- confirm required `Info.plist` usage strings
- confirm Signing & Capabilities match plugin requirements
