---
name: phaser-capacitor-android
description: "Capacitor Android上のPhaser 3/4ゲームをViteとGradleで構築・出荷する。入力、音声、WebView、戻るボタン、Android同期・署名、ADB/エミュレータ連携の調査で使う。"
metadata:
  short-description: "Phaser + Capacitor Android/ADB ワークフロー"
---

# Phaser Capacitor Android

Build Phaser games that run in the browser and ship in an Android native shell via Capacitor.
Use this skill at the boundary where most breakage happens: Vite build output, static asset paths, Phaser version differences, mobile scale and orientation, touch/audio behavior, Android WebView lifecycle, Gradle setup, sync/run, signing, and WSL2 emulator or ADB workflows.

Use the `phaser-gamedev` skill for browser-only Phaser gameplay work. Use `phaser4-gamedev` alongside this skill when the project is confirmed Phaser 4.x, the user asks for Phaser 4, or the task touches Phaser 3 to 4 migration, renderer internals, filters, lighting, shaders, render textures, GPU layers, or texture orientation.

Use this skill when Android, Capacitor, WebView, native build, emulator, device, or Play Store packaging concerns are part of the task.

## Operating Model: Two Runtimes, One Game Contract

Treat the project as systems that must agree:
- A web game runtime: Phaser + Vite + browser APIs.
- A native wrapper: Capacitor Android + Android System WebView + Gradle.
- A host boundary when applicable: Linux/WSL builds, Windows Android Studio or emulator, and ADB device ownership.

Most failures happen when the contract is implicit. Make build output, asset URLs, scene startup, scale mode, orientation, input, audio unlock, pause/resume behavior, and signing choices explicit and testable.

Before implementing or debugging, establish:
- Phaser version: inspect the installed or vendored Phaser major/minor before using version-sensitive APIs.
- Web output: exact Vite output directory (`dist` or `www`) and matching Capacitor `webDir`.
- Assets: images, atlases, audio, tilemaps, and packs under `public/` or bundled imports, with loader URLs that work under the Android WebView origin.
- Scale/orientation: chosen Phaser scale mode, fixed or responsive game size, pixel-art rules, DPR cap, and Android orientation policy.
- Input: desktop keyboard/mouse/gamepad and mobile touch or virtual controls are both intentional.
- Audio: first-gesture unlock behavior and background pause/resume rules are defined.
- Lifecycle: WebView pause/resume, WebGL context loss, hardware back button, and scene cleanup have product rules.
- Android toolchain: Capacitor, Android Studio, SDK, Gradle JDK, and `adb` match the project's Capacitor major version.
- Host split: if WSL2/Linux builds but Windows owns Android Studio, the emulator, or `adb.exe`, treat Windows as the device host. Do not let `npx cap run android` or `npx cap open android` choose WSL-side Android Studio/ADB implicitly. Build/sync in WSL, then install with Windows `adb.exe`, or explicitly open Windows native Android Studio.

Core priorities:
1. Contract-first game boot: scene list, loader keys, asset paths, and scale behavior are discoverable and stable.
2. Toolchain-first Android setup: verify Capacitor, Android Studio, SDK, Gradle JDK, and `adb` before debugging game logic.
3. Mobile-first ergonomics: touch, audio unlock, orientation, safe areas, and resize behavior are not afterthoughts.
4. Build-sync discipline: native runs use freshly built and synced web assets.
5. Fast diagnosis: add small runtime checks for missing assets, loader failures, blank canvas, WebGL failures, and stale bundles before deep native debugging.

## Reference Files

| Topic | File | Use When |
| --- | --- | --- |
| Android workflow | [references/capacitor-android-workflow.md](references/capacitor-android-workflow.md) | Setup, build/sync/run, emulator/device, live reload, signing |
| WSL2 + Windows Emulator | [references/windows-wsl-emulator-workflow.md](references/windows-wsl-emulator-workflow.md) | Project is in WSL2/Linux, Windows Android Studio/Emulator owns the GUI/device, or WSL emulator controls are unreliable |
| Phaser mobile runtime | [references/phaser-mobile-runtime-patterns.md](references/phaser-mobile-runtime-patterns.md) | Phaser config, scene boot, asset paths, touch input, audio unlock, scale/orientation, pause/resume |
| Phaser 4 Android rendering | [references/phaser4-android-rendering.md](references/phaser4-android-rendering.md) | Confirmed Phaser 4, Phaser 3 to 4 migration, filters, lighting, shaders, render targets, GPU layers, or renderer performance |
| Gotchas | [references/gotchas.md](references/gotchas.md) | Browser works but Android fails, loader/audio/touch/scale/WebGL/Gradle/ADB issues |

## Quick Start Workflow

1. Inspect `package.json`, `vite.config.*`, `capacitor.config.*`, Phaser entry points, scenes, and asset folders.
2. Determine Phaser major/minor and Capacitor major version from local dependencies or vendored bundles.
3. Build the Phaser app with the project-native command, usually `npm run build`.
4. Configure Capacitor with `webDir` matching the build output, usually `"dist"`.
5. Add Android if missing: install `@capacitor/android`, then run `npx cap add android`.
6. For a native Linux/macOS/Windows project, use the deterministic loop:
   - `npm run build`
   - `npx cap sync android`
   - `npx cap run android` or `npx cap open android`

When possible, add project scripts so repeated commands cannot skip build or sync.

For WSL2 projects with Windows Android Studio or a Windows emulator, do not use the plain `cap run/open` loop as the default. First choose the device host deliberately:
- Install a WSL-built APK with Windows `adb.exe`: best for smoke-testing TypeScript, Phaser scenes, CSS, assets, Capacitor config, or Android output that already syncs.
- Open the Android project in Windows native Android Studio: best when editing native Gradle, manifest, plugin code, signing, Logcat, profilers, or resource editors.

Do not default to debugging a flaky WSL2 emulator GUI, WSL-side Android Studio, or Linux `adb` when the user's goal is an Android app smoke test. Use the Windows emulator/device host instead and convert WSL paths with `wslpath -w` when passing APKs or project paths to Windows tools.

## Implementation Guidelines

### 1) Project Shape

Prefer this shape:
- `index.html` and `src/*` for Phaser app code.
- `public/assets/...` for images, atlases, audio, tilemaps, JSON packs, and fonts that should be served as files.
- `capacitor.config.ts` with `webDir: "dist"` for Vite defaults.
- A small boot or preload scene that owns loading, progress, and loader error reporting.

Keep runtime loads compatible with both desktop browser and Android System WebView:
- Good: `this.load.image('player', '/assets/player.png')`
- Good: `this.load.tilemapTiledJSON('level-1', '/assets/maps/level-1.json')`
- Avoid: filesystem paths, `file://` assumptions, absolute dev-machine hostnames, or paths that only work with Vite dev server rewrites.

Android serves bundled web assets from a local WebView origin. Absolute `/assets/...` URLs usually resolve correctly under that origin for files in `public/assets`. Do not change Capacitor's Android scheme or use `server.url` without a routing or live-reload reason.

### 2) Phaser Runtime Contract

Inspect version and config before editing:
- Phaser 3 and Phaser 4 differ in renderer, filters, pipelines, texture behavior, and some APIs.
- Unknown Phaser version means stop API-sensitive edits until dependency, vendored bundle, script tag, or runtime `Phaser.VERSION` identifies the major/minor.
- For Phaser 3.x, use the matching installed minor version and avoid copying Phaser 4-only renderer/filter APIs into the project.
- For Phaser 4.x, prefer WebGL-aware patterns and read `references/phaser4-android-rendering.md` before changing filters, masks, lighting, shaders, render textures, GPU layers, custom pipelines, or renderer internals.
- For migration work, inventory renderer hotspots before changing gameplay logic.
- Preserve the existing scene model unless it is the source of the Android failure.
- Choose scale behavior deliberately: fixed virtual resolution with `FIT`, responsive canvas with `RESIZE`, or pixel-art integer scaling.
- Cap effective resolution for Android devices with very high DPR.
- Keep CSS and Phaser config aligned so the canvas fills the WebView without page scrolling.

For Phaser-specific implementation details, read `references/phaser-mobile-runtime-patterns.md`.

### 3) Assets, Scenes, and State

Use stable loader keys and one source of truth for asset dimensions:
- Load assets in `preload()` or a boot scene, not ad hoc in `create()`.
- Measure spritesheet frame width, height, spacing, and margin before adding animations.
- Create animations once per game lifecycle or guard with `this.anims.exists(key)`.
- Keep gameplay, UI, loading, and menus in scenes with clear ownership.
- Use scene data, registries, or typed state modules instead of global `window` state.
- Pool projectiles, enemies, particles, and frequently spawned objects.

For tilemaps, atlases, spritesheets, physics, and general Phaser gameplay, use the `phaser-gamedev` skill alongside this one.

### 4) Mobile Input, Audio, and Back Button

Set desktop and mobile input rules together:
- Map keyboard/mouse/gamepad for browser development.
- Map touch, virtual sticks/buttons, swipe, or tap zones for Android.
- Add enough active pointers for multi-touch controls.
- Set `touch-action: none` on the game container/canvas so WebView gestures do not scroll or zoom the page.

Plan for browser audio policy:
- Start or resume audio after the first user gesture.
- Pause or mute audio on Capacitor `pause`.
- Resume intentionally on `resume`.

Handle Android's hardware back button via `@capacitor/app` when there is in-app state to close, a route stack to pop, a menu to dismiss, or a pause screen to open. Letting default exit behavior stand is acceptable only when it is an explicit product decision.

### 5) Performance and Stability Guardrails

- Prefer atlases over many small images when draw calls or load churn matter.
- Cap effective render resolution on high-DPI Android screens.
- Measure `game.loop.actualFps`, active object counts, physics bodies, tweens, timers, particles, and loader/cache size before major performance rewrites.
- Fix object churn, collision-pair explosions, oversized textures, and culling issues before moving to specialized Phaser 4 GPU layers or custom rendering.
- Avoid creating sprites, text, graphics, tweens, or sounds every frame.
- Use object pools for repeat spawns.
- Stop timers, event listeners, and subscriptions on scene shutdown.
- Listen for Phaser loader errors and surface the failing key or URL.
- Pause simulation and audio on app backgrounding.
- Treat WebGL context loss as possible on Android, especially with custom pipelines, render textures, or large textures.
- Verify the app on a real device or emulator when touch, orientation, audio, or performance matters.

### 6) Capacitor Android Integration

Use the official Capacitor docs for the project's major version as the source of truth. Do not hardcode environment requirements from memory; confirm Node, Android Studio, Android SDK platform, Gradle JDK, and target SDK requirements for the local project.

Verify with:
- `node --version`
- `npm ls @capacitor/core @capacitor/cli @capacitor/android`
- `npx cap doctor`
- `adb devices`
- Android Studio Gradle sync when native files are involved

After native-side config changes, plugin changes, permissions, signing changes, or web asset changes, run `npx cap sync android` again.

For WSL2 projects where Windows owns Android Studio/Emulator:
- Prefer scripts such as `android:cloud:apk` or `android:debug:apk` that build in WSL with `npx cap sync android` plus `./gradlew assembleDebug`.
- Install and launch with Windows `adb.exe` using a Windows-converted APK path, for example `wslpath -w android/app/build/outputs/apk/debug/app-debug.apk`.
- If Android Studio is needed, explicitly launch Windows `studio64.exe` with a Windows-converted project path. Do not rely on `npx cap open android` from WSL unless the user explicitly wants the WSL/UNC workflow.
- Keep one ADB host per session. Mixing Linux `adb` and Windows `adb.exe` is a common source of missing, duplicate, or offline devices.

Live reload is development-only. If using `server.url`, use a reachable LAN/emulator host and `server.cleartext: true` only when required. Remove `server.url` before release builds.

Release builds need a project-owned keystore. Debug builds auto-sign.

## Anti-Patterns to Avoid

**Guessing Phaser version**

Why bad: Phaser 3 and 4 renderer, filter, texture, and API differences can turn a small fix into a regression.
Better: inspect dependencies, vendored banners, or runtime `Phaser.VERSION` before editing version-sensitive code.

**Treating Phaser 4 as a drop-in Phaser 3 upgrade**

Why bad: code can compile while filters, masks, tint, camera rounding, render targets, texture orientation, or custom pipelines change behavior.
Better: run a hotspot search, classify findings as mechanical, behavioral, or architectural, then verify visual output on browser and Android.

**Running Android without rebuilding web assets**

Why bad: device/emulator shows stale JS, CSS, and assets.
Better: use scripts that always build before `cap sync` and `cap run`.

**Using dev-server-only asset paths**

Why bad: Vite dev server may resolve paths that bundled Android WebView assets cannot.
Better: load public assets with stable `/assets/...` URLs or imported bundle URLs that survive production build.

**Loading or creating game objects in the wrong lifecycle**

Why bad: assets can be missing, animations duplicated, and scenes leak event handlers after restart.
Better: load in `preload()`, create in `create()`, update with delta time, and clean up on scene shutdown.

**Treating Android as a browser-only bug**

Why bad: Android adds WebView origin, lifecycle, audio policy, memory pressure, orientation, touch, and hardware back behavior.
Better: inspect WebView console, verify touch/audio/orientation on device, and test pause/resume.

**Shipping a development server config**

Why bad: `server.url` points the app at a dev machine or remote web bundle and changes release security/performance behavior.
Better: remove `server.url` for production and ship built assets unless the project has an intentional live-update architecture.

**Mixing ADB hosts in WSL2**

Why bad: Linux `adb` and Windows `adb.exe` may talk to different servers, so devices appear missing, offline, or inconsistent.
Better: choose the device host first. If Windows owns the emulator, run Windows `adb.exe` from WSL and convert APK paths with `wslpath -w`.

**Opening WSL-side Android Studio by accident**

Why bad: `npx cap open android` from WSL can open or target the wrong Android Studio/SDK/ADB path, leaving the real Windows emulator disconnected from the build workflow.
Better: for smoke tests, build the APK in WSL and install with Windows `adb.exe`; for native Android editing, explicitly launch Windows `studio64.exe` or work from a Windows filesystem clone.

**Starting with shaders, filters, or GPU layers**

Why bad: advanced renderer paths add render passes, fill-rate, WebGL-only behavior, and version-specific failure modes.
Better: use standard game objects, atlases, pooling, culling, and measured profiling until the requirement proves a specialized path is needed.

## Verification

Run the strongest project checks available without inventing unrelated tooling:

```bash
npm run typecheck
npm run lint
npm test
npm run build
```

For Android-facing changes, also verify:
- `npx cap sync android` runs after the latest build.
- Device/emulator launches the fresh bundle, not stale web assets.
- Canvas is nonblank, correctly sized, and free of WebView console loader errors.
- Boot, preload, scene transitions, pause/resume, restart, and UI overlays work.
- Touch controls, audio unlock, orientation, hardware back, and safe-area layout match the product rule.
- Movement uses delta time or physics velocity and remains stable at variable frame rates.
- Animations, atlases, tilemaps, collision bodies, camera bounds, and pixel-art rounding match visible art.
- For Phaser 4 renderer work, filters, lighting, render textures, GPU layers, and texture orientation render correctly and do not destroy FPS on target hardware.

If a check cannot run, state exactly why and what risk remains.

## Variation Guidance

Do not produce identical mobile wrappers by default. Adjust implementation to the game:
- Arcade/action game: responsive controls, low input latency, object pooling, pause behavior, and stable FPS matter most.
- Platformer: fixed virtual resolution, camera rounding, collision debug toggles, and virtual buttons need deliberate tuning.
- Pixel-art game: `pixelArt`, nearest-neighbor CSS, integer-friendly scale, and texture bleeding checks are critical.
- Tiled RPG or map-heavy game: tilemap paths, layer collisions, camera bounds, and asset pack structure are the fragile surface.
- Menu-heavy or visual novel game: safe areas, text layout, back-button rules, and audio focus matter more than physics.
- Asset QA tool: diagnostics overlay, loader error list, texture dimensions, FPS, and screenshot checks are useful.

Vary these dimensions intentionally:
- Scale mode and virtual resolution.
- Orientation policy and safe-area handling.
- Touch control layout and active pointer count.
- Audio unlock and background behavior.
- Scene boundaries, state persistence, and diagnostics visibility.

Avoid converging on a generic "canvas plus three buttons" output when the project context calls for platformer controls, tilemap inspection, menu navigation, or production packaging.

## Remember

Phaser + Capacitor Android succeeds when contracts are explicit and workflows are disciplined.
Verify the Phaser and Capacitor versions, make scene and asset boot deterministic, design touch/audio/lifecycle behavior for Android, align the Android toolchain, and keep build/sync/run repeatable.
