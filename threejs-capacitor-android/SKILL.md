---
name: threejs-capacitor-android
description: "Build and ship Three.js apps on Capacitor Android with Vite and Gradle: GLTF loading, assets_index animation UI, OrbitControls mouse/touch mappings, WebView lifecycle handling, and Android sync/run/signing troubleshooting."
metadata:
  short-description: "Three.js + Capacitor Android workflow"
---

# Three.js Capacitor Android

Build interactive Three.js apps that run in the browser and ship in an Android native shell via Capacitor.
Use this skill for the boundary where most breakage happens: Vite build output, static asset paths, animation metadata, controls, Android WebView lifecycle, Gradle setup, sync/run, and signing.

For the iOS target, use the `threejs-capacitor-ios` skill. The web/Three.js layer is mostly shared; the native shell, lifecycle, toolchain, and store build workflow differ.

## Operating Model: Two Runtimes, One Contract

Treat the project as two systems that must agree:
- A web renderer runtime: Three.js + Vite + browser APIs
- A native runtime wrapper: Capacitor Android + Android System WebView + Gradle

Most failures happen when their contract is implicit. Make build output, file paths, clip names, input mappings, lifecycle behavior, and signing choices explicit and testable.

Before implementing or debugging, establish:
- Web output: exact Vite output directory (`dist` or `www`) and matching Capacitor `webDir`.
- Assets: GLBs/JSON under `public/` and loaded with URL paths that work under `https://localhost`.
- Animation contract: UI derives from `assets_index.json`; no hardcoded clip strings in event handlers.
- Android toolchain: Node/Capacitor/Android Studio/SDK versions match the project's Capacitor major version; prefer Android Studio's bundled Gradle JDK unless the official docs for that version require otherwise.
- Input: desktop mouse and mobile touch mappings are both intentional.
- Lifecycle: WebGL context loss, app pause/resume, and hardware back button have defined behavior.

Core priorities:
1. Contract-first data flow: metadata drives asset and animation selection.
2. Toolchain-first Android setup: verify Android Studio, SDK, Gradle JDK, and `adb` before debugging app logic.
3. Symmetric controls: define mouse and touch mappings together.
4. Build-sync discipline: native runs use freshly built and synced web assets.
5. Fast diagnosis: add small runtime checks for missing assets, unresolved clips, and WebGL failures before deep native debugging.

## Reference Files

| Topic | File | Use When |
| --- | --- | --- |
| Android workflow | [references/capacitor-android-workflow.md](references/capacitor-android-workflow.md) | Setup, build/sync/run, emulator/device, live reload, signing |
| Animation contract | [references/threejs-animation-index-pattern.md](references/threejs-animation-index-pattern.md) | GLTF/GLB animation UI, clip resolution, metadata-driven actions |
| Gotchas | [references/gotchas.md](references/gotchas.md) | Browser works but Android fails, Gradle/JDK/SDK errors, touch/WebGL/back-button issues |

## Quick Start Workflow

1. Inspect `package.json`, `vite.config.*`, `capacitor.config.*`, and `public/assets/**`.
2. Build the Three.js app with the project-native command, usually `npm run build`.
3. Configure Capacitor with `webDir` matching the build output, usually `"dist"`.
4. Add Android if missing: `npm install @capacitor/android` then `npx cap add android`.
5. Use the deterministic loop:
   - `npm run build`
   - `npx cap sync android`
   - `npx cap run android` or `npx cap open android`

When possible, add project scripts so repeated commands cannot skip build or sync.

## Implementation Guidelines

### 1) Project Shape

Prefer this shape:
- `index.html` and `src/*` for app code
- `public/assets/...` for GLBs, textures, and JSON contracts
- `capacitor.config.ts` with `webDir: "dist"` for Vite defaults

Keep runtime fetches compatible with both desktop browser and Android System WebView:
- Good: `fetch('/assets/assets_index.json')`
- Avoid: filesystem paths, `file://` assumptions, or environment-specific hostnames unless live reload is intentionally configured.

Android serves bundled web assets from `https://localhost` by default through `server.androidScheme`. Absolute `/assets/...` URLs resolve correctly under that origin. Do not change `androidScheme` away from `https` or `http` without a specific routing reason.

### 2) Animation Contract via `assets_index.json`

Use one source of truth:
- Character skeleton URL
- Animation source URL
- `animations[]` entries with:
  - stable app id (`idle`, `walk`, `run`)
  - `sourceClipName` matching the exact `AnimationClip.name`
  - loop mode and transition defaults

Runtime pattern:
1. Load index JSON.
2. Load skeleton GLB and animation GLB.
3. Resolve each UI control to a clip by `sourceClipName`.
4. Build an `AnimationAction` map keyed by app id.
5. Play the default action from the index.

See `references/threejs-animation-index-pattern.md`.

### 3) Controls: Desktop and Touch

Use `OrbitControls` and set mappings explicitly:
- Mouse:
  - left = rotate
  - wheel = dolly/zoom
  - right = pan
- Touch:
  - one-finger = rotate
  - two-finger = dolly + pan

Set `canvas.style.touchAction = 'none'` so the WebView does not hijack drag gestures for page scroll or zoom.

If the product requires vertical-only pan or other constrained motion, apply the constraint after `controls.update()` each frame. Do not silently change rotate/zoom semantics while adding the constraint.

Handle Android's hardware back button via `@capacitor/app` when there is in-app state to close, a route stack to pop, or a camera mode to reset. Letting the default exit behavior stand is acceptable only when it is an explicit product decision.

### 4) Performance and Stability Guardrails

- Cap pixel ratio: `Math.min(window.devicePixelRatio, 2)`; many Android screens are 3x-4x.
- Reuse mixers/actions/materials; do not recreate them per click.
- On resize, update camera aspect, projection matrix, and renderer size.
- Keep animation switching with fade transitions from metadata defaults.
- Handle `webglcontextlost` and `webglcontextrestored`; Android may lose GL context under memory pressure or backgrounding.
- Pause the render loop on Capacitor `pause`; resume intentionally on `resume`.
- Dispose geometry, materials, textures, controls, and renderers when replacing scenes or leaving a view.

### 5) Capacitor Android Integration

Use the official Capacitor docs for the project's major version as the source of truth. For current Capacitor 8-era projects, expect:
- Node 22+
- Android Studio plus Android SDK
- API 24+ Android platform support
- Android Studio's bundled JDK/Gradle JDK instead of a separately managed JDK in most local setups

Verify with:
- `node --version`
- `npx cap doctor`
- `adb devices`
- Android Studio Gradle sync

After native-side config changes, plugin changes, or web asset changes, run `npx cap sync android` again.

Live reload is development-only. If using `server.url`, use a reachable LAN/emulator host and `server.cleartext: true` only when required; remove `server.url` before release builds.

Release builds need a project-owned keystore. Debug builds auto-sign.

## Anti-Patterns to Avoid

**Hardcoding clip names in UI handlers**

Why bad: a renamed clip in a GLB silently breaks buttons.
Better: map buttons from `assets_index.json` and resolve clip names once at startup.

**Treating Android as a browser-only bug**

Why bad: Android adds WebView origin, lifecycle, memory, and input behavior that desktop Chrome may not expose.
Better: test bundled asset paths, touch behavior, context-loss handling, and WebView console logs on an emulator or device.

**Wrong JDK, missing SDK, or stale Gradle state**

Why bad: Gradle fails with misleading class-file, SDK-location, or plugin errors.
Better: use Android Studio's Gradle JDK, configure SDK paths, run `npx cap doctor`, then Gradle sync/clean only after the environment is sane.

**Running Android without rebuilding web assets**

Why bad: device/emulator shows stale JS/CSS and debugging becomes misleading.
Better: use scripts that always build before `cap sync` and `cap run`.

**Leaving control mappings implicit**

Why bad: desktop and mobile interaction diverge from UX requirements, and WebView may consume gestures.
Better: set `mouseButtons`, `touches`, and `touch-action: none` explicitly.

**Shipping a development server config**

Why bad: `server.url` points the app at a dev machine or remote web bundle and changes release security/performance behavior.
Better: remove `server.url` for production and ship built assets unless the project has an intentional live-update architecture.

## Variation Guidance

Do not produce identical viewers by default. Adjust implementation to the product intent:
- Character showcase: richer lighting, slower damping, polished default idle loop.
- Gameplay prototype: fast transitions, state-driven animation switching, minimal chrome.
- Asset QA tool: diagnostics overlay, clip length/track info, missing-clip warnings.
- Product configurator: constrained camera, touch-friendly hotspots, asset preloading and progress states.

Vary these dimensions intentionally:
- Lighting/background/floor treatment
- Input tuning and camera constraints
- Animation UX, shortcuts, and auto-play strategy
- Diagnostics visibility and error surface

Avoid converging on a generic "orbit camera plus three buttons" output when the project context calls for something more specific.

## Remember

Three.js + Capacitor Android succeeds when contracts are explicit and workflows are disciplined.
Build a metadata contract, map controls intentionally, align the Android toolchain, handle mobile WebView lifecycle, and keep build/sync/run deterministic.
