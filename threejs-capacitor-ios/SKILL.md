---
name: threejs-capacitor-ios
description: "Capacitor iOS上のThree.jsアプリをViteとSwift Package Managerで構築・出荷する。GLTF表示、操作UI、WKWebView、iOS同期・署名まわりの不具合調査で使う。"
metadata:
  short-description: "Three.js + Capacitor iOS ワークフロー"
---

# Three.js Capacitor iOS

browser で動く interactive Three.js app を Capacitor で iOS native shell に出荷する。Vite build output、static asset paths、animation metadata、controls、WKWebView lifecycle、SPM、Xcode、sync/run、signing の境界で使う。

Android target は `threejs-capacitor-android` を使う。web / Three.js layer はほぼ共有だが、native shell、lifecycle、package manager、store build workflow は異なる。

## 基本方針: Two Runtimes, One Contract

合意すべき systems:

- web renderer runtime: Three.js + Vite + browser APIs
- native runtime wrapper: Capacitor iOS + WKWebView + Xcode/SPM

build output、file paths、clip names、input mappings、lifecycle behavior、package manager、signing を explicit / testable にする。

作業前に確認すること:

- exact Vite output directory と Capacitor `webDir`
- `public/` 配下の GLB/JSON と iOS WebView origin で動く URL paths
- `assets_index.json` による animation contract
- macOS、Node、Xcode、Command Line Tools と Capacitor major
- SPM / CocoaPods の選択
- desktop mouse / mobile touch mappings
- WebGL context loss、pause/resume、safe-area layout、device/simulator debugging

優先順位:

1. metadata-driven asset / animation selection
2. modern Capacitor では SPM-first
3. mouse/touch mappings を同時に定義
4. native run は fresh build + sync
5. missing assets、unresolved clips、WebGL failures の runtime checks

## 参照ファイル

| Topic | File | Use When |
| --- | --- | --- |
| iOS workflow | [references/capacitor-ios-spm-workflow.md](references/capacitor-ios-spm-workflow.md) | setup、build/sync/run、simulator/device、SPM migration、signing |
| Animation contract | [references/threejs-animation-index-pattern.md](references/threejs-animation-index-pattern.md) | GLTF/GLB animation UI、clip resolution、metadata-driven actions |
| Gotchas | [references/gotchas.md](references/gotchas.md) | browser works but iOS fails、SPM/CocoaPods、WKWebView/touch/WebGL |

## Quick Start

1. `package.json`、`vite.config.*`、`capacitor.config.*`、`public/assets/**`、existing `ios/` を確認
2. project-native command で build。通常 `npm run build`
3. Capacitor `webDir` を output に合わせる。通常 `"dist"`
4. iOS がなければ `npm install @capacitor/ios` -> `npx cap add ios --packagemanager SPM`
5. deterministic loop:
   - `npm run build`
   - `npx cap sync ios`
   - `npx cap run ios` または `npx cap open ios`

可能なら build/sync を飛ばせない scripts を追加する。

## 実装ガイド

### Project Shape

- app code: `index.html` と `src/*`
- GLBs、textures、JSON contracts: `public/assets/...`
- Vite default: `capacitor.config.ts` with `webDir: "dist"`
- `ios/App/` は Capacitor generated を使う

runtime fetches:

- Good: `fetch('/assets/assets_index.json')`
- Avoid: filesystem paths、`file://` assumptions、environment-specific hostnames

iOS bundled assets は WKWebView 内で serve される。built output にコピーされた `public/assets` には absolute `/assets/...` が通常有効。

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

### Controls / Safe Areas

`OrbitControls` mappings を明示する。

- Mouse: left rotate、wheel dolly/zoom、right pan
- Touch: one-finger rotate、two-finger dolly + pan

`canvas.style.touchAction = 'none'` を設定し、app が意図的に document scrolling を混ぜない限り canvas 背後で page scroll しないようにする。notch、home indicator、rounded corners 付近の overlays には CSS `env(safe-area-inset-*)` を使う。

### Performance / Stability

- pixel ratio は `Math.min(window.devicePixelRatio, 2)` に cap
- mixers/actions/materials を reuse
- resize / orientation change で camera aspect、projection matrix、renderer size を更新
- animation switching は metadata defaults から fade transitions
- `webglcontextlost` / `webglcontextrestored` を扱う
- Capacitor `pause` で render loop を pause、`resume` で意図して再開
- scene replacement / view leave で geometry、materials、textures、controls、renderer を dispose

### Capacitor iOS

official Capacitor docs を source of truth にする。Capacitor 8-era では概ね Node 22+、macOS、Xcode 26+、Command Line Tools、iOS 15+、Swift Package Manager。

確認:

- `node --version`
- `xcode-select -p`
- `npx cap doctor`
- Xcode build and package resolution

native config、plugins、web assets 変更後は `npx cap sync ios`。live reload は development-only。release 前に `server.url` を消す。release builds には Apple Developer signing、bundle id、capabilities、archive/export choices が必要。

## 避けること

**UI handlers に clip names を hardcode**

問題: GLB 内の clip name が変わると buttons が黙って壊れる。
改善: `assets_index.json` から buttons を map し、startup 時に clip names を一度だけ resolve する。

**SPM と CocoaPods assumptions を混ぜる**

問題: dependency drift と壊れた Xcode project expectations を生む。
改善: project ごとに package manager を1つ選ぶ。modern setup では plugin が CocoaPods を強制しない限り SPM を優先する。

**web assets rebuild なしで iOS run**

問題: simulator/device が stale JS/CSS を表示し、debug が誤誘導される。
改善: `cap sync` と `cap run` の前に必ず build する scripts を使う。

**iOS を desktop Safari と同一視する**

問題: WKWebView は lifecycle、memory pressure、safe-area、remote debugging behavior が異なる。
改善: simulator または device で test し、WebView を inspect し、pause/resume/context loss を扱う。

**control mappings を implicit にする**

問題: desktop と mobile の interaction が UX requirements から diverge し、iOS が gestures を page behavior と解釈することがある。
改善: `mouseButtons`、`touches`、`touch-action: none` を明示する。

**development `server.url` を ship**

問題: `server.url` は app を dev machine または remote web bundle に向け、release の security / performance behavior を変える。
改善: intentional live-update architecture がない限り、production では `server.url` を削除して built assets を ship する。

## Variation Guidance

- character showcase: lighting、slow damping、polished idle loop
- gameplay prototype: fast transitions、state-driven animation switching、minimal chrome
- asset QA: diagnostics overlay、clip info、missing-clip warnings
- product configurator: constrained camera、touch hotspots、preloading/progress

lighting/background/floor、input tuning、camera constraints、animation UX、diagnostics visibility、safe-area-aware placement を product intent に合わせて変える。

## 覚えておくこと

Three.js + Capacitor iOS は explicit contracts と disciplined workflow で成功する。metadata contract を作り、controls を明示し、Xcode/SPM toolchain と mobile WKWebView lifecycle を揃え、build/sync/run を deterministic にする。
