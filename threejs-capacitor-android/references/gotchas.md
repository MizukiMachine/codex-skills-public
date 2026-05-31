# Gotchas and Fast Fixes for Capacitor Android Three.js Apps

## Browser Works but Device/Emulator Fails

Common causes:
- stale native web assets
- `webDir` mismatch
- bad static asset path
- production build accidentally using `server.url`
- WebView console error hidden from normal terminal output

Fix:
1. `npm run build`
2. `npx cap sync android`
3. confirm `capacitor.config.*` uses the actual output dir, usually `webDir: 'dist'`
4. use `/assets/...` URLs for files under `public/assets`
5. remove `server.url` unless live reload is intentional
6. use `chrome://inspect` to read WebView console/network/WebGL errors

## Animation Button Does Nothing

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

## Touch Pan/Rotate Feels Wrong or Gestures Scroll the Page

Common causes:
- missing `touch-action: none` on the canvas
- default `OrbitControls` mappings not aligned with UX
- custom pan constraint applied before `controls.update()`
- overlay UI absorbing pointer events unintentionally

Fix:
- set `canvas.style.touchAction = 'none'`
- set both `mouseButtons` and `touches` explicitly
- apply pan/camera constraints after `controls.update()`
- check CSS `pointer-events` on overlays

## Black Screen After Backgrounding

Common causes:
- WebGL context lost under memory pressure
- render loop kept running while backgrounded
- textures/render targets not recreated after context restore

Fix:
- listen for `webglcontextlost`, call `event.preventDefault()`, and pause rendering
- listen for `webglcontextrestored` and recreate renderer-dependent resources if needed
- pause on Capacitor `App.addListener('pause', ...)`
- resume intentionally on `App.addListener('resume', ...)`

## Gradle, JDK, or SDK Errors

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

## Hardware Back Button Closes the App Unexpectedly

Fix:
- add `@capacitor/app` if missing
- listen with `App.addListener('backButton', ...)`
- decide whether to close modal UI, pop route state, reset the camera, or allow exit

Do not intercept back globally without a product rule. Android users expect back to do something predictable.

## Device Not Detected

Fix:
- `adb devices` should list it
- enable Developer options and USB debugging
- accept the RSA prompt
- try a different USB cable/port if the device appears as charging-only
- for emulators, ensure the AVD uses API 24+ and hardware GL

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

## WebGL Is Slow or Janky on High-DPI Android

Common causes:
- pixel ratio set to full `devicePixelRatio`
- expensive shadows/post-processing enabled by default
- render loop runs while tab/app is paused
- too many draw calls/material variants

Fix:
- use `renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2))`
- profile before adding post-processing
- pause on app `pause`
- batch/reuse geometry and materials where practical
- reduce texture sizes for mobile builds when assets are oversized
