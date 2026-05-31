---
name: phaser-capacitor-ios
description: "Build and ship Phaser 3/4 games on Capacitor iOS with Vite, Xcode, and Swift Package Manager: Phaser config, scene lifecycle, asset loading, scale/orientation, safe-area touch controls, audio unlock, WKWebView pause/resume behavior, iOS sync/run/signing, Safari WebView debugging, and Phaser 4 renderer issues."
metadata:
  short-description: "Phaser + Capacitor iOS workflow"
---

# Phaser Capacitor iOS

Build Phaser games that run in the browser and ship in an iOS native shell via Capacitor.
Use this skill at the boundary where most breakage happens: Vite build output, static asset paths, Phaser version differences, mobile scale and orientation, safe-area touch controls, audio unlock, WKWebView lifecycle, Swift Package Manager, Xcode setup, sync/run, signing, and Safari WebView debugging.

Use the `phaser-gamedev` skill for browser-only Phaser gameplay work. Use `phaser4-gamedev` alongside this skill when the project is confirmed Phaser 4.x, the user asks for Phaser 4, or the task touches Phaser 3 to 4 migration, renderer internals, filters, lighting, shaders, render textures, GPU layers, or texture orientation.

Use this skill when iOS, Capacitor, WKWebView, Xcode, SPM, signing, simulator/device, TestFlight/App Store packaging, or iOS-specific touch/audio/safe-area behavior is part of the task.

## Operating Model: Two Runtimes, One Game Contract

Treat the project as systems that must agree:
- A web game runtime: Phaser + Vite + browser APIs.
- A native wrapper: Capacitor iOS + WKWebView + Xcode/SPM.

Most failures happen when the contract is implicit. Make build output, asset URLs, scene startup, scale mode, orientation, input, audio unlock, safe-area layout, pause/resume behavior, package manager choice, and signing choices explicit and testable.

Before implementing or debugging, establish:
- Phaser version: inspect the installed or vendored Phaser major/minor before using version-sensitive APIs.
- Web output: exact Vite output directory (`dist` or `www`) and matching Capacitor `webDir`.
- Assets: images, atlases, audio, tilemaps, and packs under `public/` or bundled imports, with loader URLs that work under the iOS WKWebView origin.
- Scale/orientation: chosen Phaser scale mode, fixed or responsive game size, pixel-art rules, DPR cap, iOS orientation policy, and safe-area placement.
- Input: desktop keyboard/mouse/gamepad and iOS touch or virtual controls are both intentional.
- Audio: first-gesture unlock, silent-mode expectations, and background pause/resume rules are defined.
- Lifecycle: WKWebView pause/resume, WebGL context loss, simulator/device debugging, and scene cleanup have product rules.
- iOS toolchain: macOS, Node, Xcode, Xcode Command Line Tools, and Capacitor iOS match the project's Capacitor major version.
- Package manager: SPM or CocoaPods is chosen intentionally; do not mix assumptions.
- Signing: bundle id, Apple Developer team, capabilities, permission strings, and archive/export path are explicit for device or release work.

Core priorities:
1. Contract-first game boot: scene list, loader keys, asset paths, and scale behavior are discoverable and stable.
2. SPM-first iOS setup: on modern Capacitor, prefer Swift Package Manager unless a plugin or existing project forces CocoaPods.
3. iOS ergonomics: touch, audio unlock, safe areas, orientation, and resize behavior are not afterthoughts.
4. Build-sync discipline: native runs use freshly built and synced web assets.
5. Fast diagnosis: add small runtime checks for missing assets, loader failures, blank canvas, WebGL failures, stale bundles, and package/signing errors before deep native debugging.

## Reference Files

| Topic | File | Use When |
| --- | --- | --- |
| iOS workflow | [references/capacitor-ios-spm-workflow.md](references/capacitor-ios-spm-workflow.md) | Setup, build/sync/run, simulator/device, SPM/CocoaPods choice, signing |
| Phaser iOS runtime | [references/phaser-ios-runtime-patterns.md](references/phaser-ios-runtime-patterns.md) | Phaser config, scene boot, asset paths, safe areas, touch input, audio unlock, orientation, pause/resume |
| Phaser 4 iOS rendering | [references/phaser4-ios-rendering.md](references/phaser4-ios-rendering.md) | Confirmed Phaser 4, Phaser 3 to 4 migration, filters, lighting, shaders, render targets, GPU layers, or renderer performance |
| Gotchas | [references/gotchas.md](references/gotchas.md) | Browser works but iOS fails, loader/audio/touch/scale/WebGL/Xcode/SPM/signing issues |

## Quick Start Workflow

1. Inspect `package.json`, `vite.config.*`, `capacitor.config.*`, Phaser entry points, scenes, asset folders, and existing `ios/` project shape.
2. Determine Phaser major/minor and Capacitor major version from local dependencies or vendored bundles.
3. Build the Phaser app with the project-native command, usually `npm run build`.
4. Configure Capacitor with `webDir` matching the build output, usually `"dist"`.
5. Add iOS if missing: install `@capacitor/ios`, then run `npx cap add ios --packagemanager SPM` unless the project requires CocoaPods.
6. Use the deterministic loop:
   - `npm run build`
   - `npx cap sync ios`
   - `npx cap run ios` or `npx cap open ios`

When possible, add project scripts so repeated commands cannot skip build or sync.

## Implementation Guidelines

### 1) Project Shape

Prefer this shape:
- `index.html` and `src/*` for Phaser app code.
- `public/assets/...` for images, atlases, audio, tilemaps, JSON packs, and fonts that should be served as files.
- `capacitor.config.ts` with `webDir: "dist"` for Vite defaults.
- `ios/App/` generated by Capacitor, not hand-recreated ad hoc.
- A small boot or preload scene that owns loading, progress, and loader error reporting.

Keep runtime loads compatible with both desktop browser and WKWebView:
- Good: `this.load.image('player', '/assets/player.png')`
- Good: `this.load.tilemapTiledJSON('level-1', '/assets/maps/level-1.json')`
- Avoid: filesystem paths, `file://` assumptions, absolute dev-machine hostnames, or paths that only work with Vite dev server rewrites.

iOS bundled assets are served inside WKWebView by Capacitor. Absolute `/assets/...` URLs usually resolve correctly for files copied from `public/assets` into the built web output.

### 2) Phaser Runtime Contract

Inspect version and config before editing:
- Phaser 3 and Phaser 4 differ in renderer, filters, pipelines, texture behavior, and some APIs.
- Unknown Phaser version means stop API-sensitive edits until dependency, vendored bundle, script tag, or runtime `Phaser.VERSION` identifies the major/minor.
- For Phaser 3.x, use the matching installed minor version and avoid copying Phaser 4-only renderer/filter APIs into the project.
- For Phaser 4.x, prefer WebGL-aware patterns and read `references/phaser4-ios-rendering.md` before changing filters, masks, lighting, shaders, render textures, GPU layers, custom pipelines, or renderer internals.
- For migration work, inventory renderer hotspots before changing gameplay logic.
- Preserve the existing scene model unless it is the source of the iOS failure.
- Choose scale behavior deliberately: fixed virtual resolution with `FIT`, responsive canvas with `RESIZE`, or pixel-art integer scaling.
- Cap effective resolution for high-DPI iPhones and iPads.
- Keep CSS, viewport metadata, and Phaser config aligned so the canvas fills WKWebView without page scrolling or home-indicator overlap.

For Phaser-specific implementation details, read `references/phaser-ios-runtime-patterns.md`.

### 3) Assets, Scenes, and State

Use stable loader keys and one source of truth for asset dimensions:
- Load assets in `preload()` or a boot scene, not ad hoc in `create()`.
- Measure spritesheet frame width, height, spacing, and margin before adding animations.
- Create animations once per game lifecycle or guard with `this.anims.exists(key)`.
- Keep gameplay, UI, loading, and menus in scenes with clear ownership.
- Use scene data, registries, or typed state modules instead of global `window` state.
- Pool projectiles, enemies, particles, and frequently spawned objects.
- Add loader diagnostics while debugging simulator/device failures.

For tilemaps, atlases, spritesheets, physics, and general Phaser gameplay, use the `phaser-gamedev` skill alongside this one.

### 4) iOS Input, Audio, Safe Areas, and Lifecycle

Set desktop and iOS input rules together:
- Map keyboard/mouse/gamepad for browser development.
- Map touch, virtual sticks/buttons, swipe, or tap zones for iOS.
- Add enough active pointers for multi-touch controls.
- Set `touch-action: none` on the game container/canvas and prevent document scrolling unless the app intentionally mixes game and document UI.
- Account for notch, rounded corners, and home indicator with CSS `env(safe-area-inset-*)` when controls or HUD sit near edges.

Plan for iOS audio policy:
- Start or resume audio after the first user gesture.
- Decide whether silent-mode behavior matters; if it does, verify the chosen web/native audio strategy on real devices.
- Pause or mute audio on Capacitor `pause`.
- Resume intentionally on `resume`.

iOS has no physical back button. If the game has back navigation, model it as in-game UI, gesture, menu state, route history, or native navigation policy.

### 5) Performance and Stability Guardrails

- Prefer atlases over many small images when draw calls or load churn matter.
- Cap effective render resolution on high-DPI iOS screens.
- Measure `game.loop.actualFps`, active object counts, physics bodies, tweens, timers, particles, and loader/cache size before major performance rewrites.
- Fix object churn, collision-pair explosions, oversized textures, and culling issues before moving to specialized Phaser 4 GPU layers or custom rendering.
- Avoid creating sprites, text, graphics, tweens, or sounds every frame.
- Use object pools for repeat spawns.
- Stop timers, event listeners, and subscriptions on scene shutdown.
- Listen for Phaser loader errors and surface the failing key or URL.
- Pause simulation and audio on app backgrounding.
- Treat WebGL context loss as possible on iOS, especially with custom pipelines, render textures, large textures, filters, or memory pressure.
- Verify the app on simulator or real device when touch, safe area, orientation, audio, or performance matters.

### 6) Capacitor iOS Integration

Use the official Capacitor docs for the project's major version as the source of truth. Do not hardcode environment requirements from memory; confirm Node, Xcode, Command Line Tools, iOS deployment target, package manager, and signing requirements for the local project.

Verify with:
- `node --version`
- `npm ls @capacitor/core @capacitor/cli @capacitor/ios`
- `xcode-select -p`
- `npx cap doctor`
- Xcode build and package resolution when native files are involved

After native-side config changes, plugin changes, permissions, signing changes, or web asset changes, run `npx cap sync ios` again.

Live reload is development-only. If using `server.url`, use a reachable LAN host and keep it in development config only. Remove `server.url` before release builds.

Release builds require Apple Developer signing, bundle id, capabilities, permission usage strings, archive/export choices, and App Store/TestFlight policy checks in Xcode or CI.

## Anti-Patterns to Avoid

**Guessing Phaser version**

Why bad: Phaser 3 and 4 renderer, filter, texture, and API differences can turn a small fix into a regression.
Better: inspect dependencies, vendored banners, script tags, or runtime `Phaser.VERSION` before editing version-sensitive code.

**Treating Phaser 4 as a drop-in Phaser 3 upgrade**

Why bad: code can compile while filters, masks, tint, camera rounding, render targets, texture orientation, or custom pipelines change behavior.
Better: run a hotspot search, classify findings as mechanical, behavioral, or architectural, then verify visual output on browser and iOS.

**Mixing SPM and CocoaPods assumptions**

Why bad: dependency drift and broken Xcode project expectations.
Better: choose one package manager per project; for modern setups prefer SPM unless a plugin or existing project forces CocoaPods.

**Running iOS without rebuilding web assets**

Why bad: simulator/device shows stale JS, CSS, and assets.
Better: use scripts that always build before `cap sync` and `cap run`.

**Using dev-server-only asset paths**

Why bad: Vite dev server may resolve paths that bundled WKWebView assets cannot.
Better: load public assets with stable `/assets/...` URLs or imported bundle URLs that survive production build.

**Loading or creating game objects in the wrong lifecycle**

Why bad: assets can be missing, animations duplicated, and scenes leak event handlers after restart.
Better: load in `preload()`, create in `create()`, update with delta time, and clean up on scene shutdown.

**Treating iOS as desktop Safari**

Why bad: WKWebView has different lifecycle, memory pressure, safe-area, audio policy, remote debugging, and packaging behavior.
Better: test on simulator or device, inspect the WebView with Safari Develop tools, and handle pause/resume/context loss.

**Shipping a development server config**

Why bad: `server.url` points the app at a dev machine or remote web bundle and changes release security/performance behavior.
Better: remove `server.url` for production and ship built assets unless the project has an intentional live-update architecture.

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

For iOS-facing changes, also verify:
- `npx cap sync ios` runs after the latest build.
- Simulator/device launches the fresh bundle, not stale web assets.
- Canvas is nonblank, correctly sized, and free of Safari Web Inspector console loader errors.
- Boot, preload, scene transitions, pause/resume, restart, and UI overlays work.
- Touch controls, audio unlock, orientation, safe-area layout, and home-indicator spacing match the product rule.
- Movement uses delta time or physics velocity and remains stable at variable frame rates.
- Animations, atlases, tilemaps, collision bodies, camera bounds, and pixel-art rounding match visible art.
- For Phaser 4 renderer work, filters, lighting, render textures, GPU layers, and texture orientation render correctly and do not destroy FPS on target hardware.
- Xcode signing, bundle id, capabilities, and permission strings are correct when device or release work is in scope.

If a check cannot run, state exactly why and what risk remains.

## Variation Guidance

Do not produce identical mobile wrappers by default. Adjust implementation to the game:
- Arcade/action game: responsive controls, low input latency, object pooling, pause behavior, and stable FPS matter most.
- Platformer: fixed virtual resolution, camera rounding, collision debug toggles, virtual buttons, and home-indicator spacing need deliberate tuning.
- Pixel-art game: `pixelArt`, nearest-neighbor CSS, integer-friendly scale, and texture bleeding checks are critical.
- Tiled RPG or map-heavy game: tilemap paths, layer collisions, camera bounds, and asset pack structure are the fragile surface.
- Menu-heavy or visual novel game: safe areas, text layout, gesture policy, and audio focus matter more than physics.
- Asset QA tool: diagnostics overlay, loader error list, texture dimensions, FPS, and simulator/device screenshot checks are useful.

Vary these dimensions intentionally:
- Scale mode and virtual resolution.
- Orientation policy and safe-area layout.
- Touch control layout and active pointer count.
- Audio unlock and background behavior.
- Scene boundaries, state persistence, and diagnostics visibility.
- Xcode/SPM/signing workflow depending on whether the target is simulator, device, TestFlight, or App Store.

Avoid converging on a generic "canvas plus three buttons" output when the project context calls for platformer controls, tilemap inspection, menu navigation, or production packaging.

## Remember

Phaser + Capacitor iOS succeeds when contracts are explicit and workflows are disciplined.
Verify the Phaser and Capacitor versions, make scene and asset boot deterministic, design touch/audio/safe-area/lifecycle behavior for iOS, align the Xcode/SPM toolchain, and keep build/sync/run repeatable.
