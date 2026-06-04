---
name: threejs-capacitor-android
description: "Capacitor Android上のThree.jsアプリをViteとGradleで構築・出荷する。GLTF表示、操作UI、WebViewライフサイクル、ADB/エミュレータ連携の不具合調査で使う。"
metadata:
  short-description: "Three.js + Capacitor Android/ADB ワークフロー"
---

# Three.js Capacitor Android

browser で動く interactive Three.js app を Capacitor で Android native shell に出荷する。Vite build output、static asset paths、animation metadata、controls、Android WebView lifecycle、Gradle、sync/run、signing の境界で使う。

iOS target は `threejs-capacitor-ios` を使う。web / Three.js layer はほぼ共有だが、native shell、lifecycle、toolchain、store build workflow は異なる。

## 基本方針: Two Runtimes, One Contract

合意すべき systems:

- web renderer runtime: Three.js + Vite + browser APIs
- native runtime wrapper: Capacitor Android + Android System WebView + Gradle

development environment が split している場合は host boundary も contract とする。

- build host: Node/Vite/Capacitor build と Gradle assemble の場所
- device host: `adb`、Android Studio、emulator/device connection の場所
- path bridge: WSL2 -> Windows の `wslpath -w` など

build output、file paths、clip names、input mappings、lifecycle behavior、signing を explicit / testable にする。

**作業前に確認すること**

- exact Vite output directory と Capacitor `webDir`
- `public/` 配下の GLB/JSON と `https://localhost` で動く URL paths
- `assets_index.json` による animation contract。event handlers に hardcoded clip strings を置かない
- Node/Capacitor/Android Studio/SDK versions と project Capacitor major
- WSL2/Linux build + Windows emulator の場合、Windows `adb.exe` と explicit path conversion
- desktop mouse / mobile touch mappings
- WebGL context loss、pause/resume、hardware back behavior

**優先順位**

1. metadata-driven asset / animation selection
2. Android Studio、SDK、Gradle JDK、`adb` の toolchain-first verification
3. mouse/touch mappings を同時に定義
4. native run は fresh build + sync
5. missing assets、unresolved clips、WebGL failures の runtime checks

## 参照ファイル

| Topic | File | Use When |
| --- | --- | --- |
| Android workflow | [references/capacitor-android-workflow.md](references/capacitor-android-workflow.md) | setup、build/sync/run、emulator/device、live reload、signing |
| WSL2 + Windows Emulator | [references/windows-wsl-emulator-workflow.md](references/windows-wsl-emulator-workflow.md) | WSL2/Linux project、Windows Android Studio/Emulator、WSL emulator controls |
| Animation contract | [references/threejs-animation-index-pattern.md](references/threejs-animation-index-pattern.md) | GLTF/GLB animation UI、clip resolution、metadata-driven actions |
| Gotchas | [references/gotchas.md](references/gotchas.md) | browser works but Android fails、Gradle/JDK/SDK、touch/WebGL/back-button |

## Quick Start

1. `package.json`、`vite.config.*`、`capacitor.config.*`、`public/assets/**` を確認
2. project-native command で build。通常 `npm run build`
3. Capacitor `webDir` を output に合わせる。通常 `"dist"`
4. Android がなければ `npm install @capacitor/android` -> `npx cap add android`
5. deterministic loop:
   - `npm run build`
   - `npx cap sync android`
   - `npx cap run android` または `npx cap open android`

WSL2 + Windows emulator では、smoke test は WSL-built APK を Windows `adb.exe` で install、native Gradle/manifest/plugin work は Windows Android Studio を使う。

## 実装ガイド

### Project Shape

- app code: `index.html` と `src/*`
- GLBs、textures、JSON contracts: `public/assets/...`
- Vite default: `capacitor.config.ts` with `webDir: "dist"`

runtime fetches:

- Good: `fetch('/assets/assets_index.json')`
- Avoid: filesystem paths、`file://` assumptions、environment-specific hostnames

Android は bundled web assets を `https://localhost` で serve する。具体的な routing reason なしに `androidScheme` を変えない。

### `assets_index.json` Animation Contract

single source of truth:

- character skeleton URL
- animation source URL
- `animations[]`: app id、exact `sourceClipName`、loop mode、transition defaults

runtime pattern:

1. index JSON を load
2. skeleton GLB と animation GLB を load
3. UI control を `sourceClipName` で clip に解決
4. app id keyed `AnimationAction` map を作る
5. index の default action を play

詳細は `references/threejs-animation-index-pattern.md`。

### Controls

`OrbitControls` mappings を明示する。

- Mouse: left rotate、wheel dolly/zoom、right pan
- Touch: one-finger rotate、two-finger dolly + pan

`canvas.style.touchAction = 'none'` を設定し、WebView に drag gesture を scroll/zoom として奪わせない。constrained pan は `controls.update()` 後に適用し、rotate/zoom semantics を黙って変えない。

Android hardware back button は closeable state、route stack、camera mode reset がある場合 `@capacitor/app` で扱う。

### Performance / Stability

- pixel ratio は `Math.min(window.devicePixelRatio, 2)` に cap
- mixers/actions/materials を reuse
- resize 時は camera aspect、projection matrix、renderer size を更新
- animation switching は metadata defaults から fade transitions
- `webglcontextlost` / `webglcontextrestored` を扱う
- Capacitor `pause` で render loop を pause、`resume` で意図して再開
- scene replacement / view leave で geometry、materials、textures、controls、renderer を dispose

### Capacitor Android

official Capacitor docs を source of truth にする。Capacitor 8-era では概ね Node 22+、Android Studio + SDK、API 24+、Android Studio bundled JDK/Gradle JDK。

確認:

- `node --version`
- `npx cap doctor`
- `adb devices`
- Android Studio Gradle sync

native config、plugins、web assets 変更後は `npx cap sync android`。live reload は development-only。`server.url` を使う場合は reachable LAN/emulator host を使い、必要な場合だけ `server.cleartext: true` を設定する。release 前に `server.url` を消す。release builds には keystore が必要。

## 避けること

**UI handlers に clip names を hardcode**

問題: GLB 内の clip name が変わると buttons が黙って壊れる。
改善: `assets_index.json` から buttons を map し、startup 時に clip names を一度だけ resolve する。

**Android を browser-only bug として扱う**

問題: Android には WebView origin、lifecycle、memory、input behavior があり、desktop Chrome では露出しない。
改善: bundled asset paths、touch behavior、context-loss handling、WebView console logs を emulator または device で確認する。

**wrong JDK、missing SDK、stale Gradle state**

問題: Gradle は class-file、SDK location、plugin errors など誤解しやすい失敗を返す。
改善: Android Studio の Gradle JDK を使い、SDK paths を設定し、`npx cap doctor` を実行してから Gradle sync / clean する。

**web assets rebuild なしで Android run**

問題: device/emulator が stale JS/CSS を表示し、debug が誤誘導される。
改善: `cap sync` と `cap run` の前に必ず build する scripts を使う。

**WSL2 で ADB hosts を混ぜる**

問題: Linux `adb` と Windows `adb.exe` が別 server と話し、devices が missing、offline、inconsistent に見える。
改善: device host を先に選ぶ。Windows が emulator を所有する場合は WSL から Windows `adb.exe` を実行し、APK path は `wslpath -w` で変換する。

**control mappings を implicit にする**

問題: desktop と mobile の interaction が UX requirements から diverge し、WebView が gestures を消費することがある。
改善: `mouseButtons`、`touches`、`touch-action: none` を明示する。

**development `server.url` を ship**

問題: `server.url` は app を dev machine または remote web bundle に向け、release の security / performance behavior を変える。
改善: intentional live-update architecture がない限り、production では `server.url` を削除して built assets を ship する。

## Variation Guidance

- character showcase: lighting、slow damping、polished idle loop
- gameplay prototype: fast transitions、state-driven animation switching、minimal chrome
- asset QA: diagnostics overlay、clip info、missing-clip warnings
- product configurator: constrained camera、touch hotspots、preloading/progress

lighting/background/floor、input tuning、camera constraints、animation UX、diagnostics visibility を product intent に合わせて変える。

## 覚えておくこと

Three.js + Capacitor Android は explicit contracts と disciplined workflow で成功する。metadata contract を作り、controls を明示し、Android toolchain と mobile WebView lifecycle を揃え、build/sync/run を deterministic にする。
