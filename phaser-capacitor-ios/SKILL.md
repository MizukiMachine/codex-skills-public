---
name: phaser-capacitor-ios
description: "Capacitor iOS上のPhaser 3/4ゲームをVite、Xcode、Swift Package Managerで構築・出荷する。入力、音声、WebView、署名、Safariデバッグ、Phaser 4固有問題の調査で使う。"
metadata:
  short-description: "Phaser + Capacitor iOS ワークフロー"
---

# Phaser Capacitor iOS

browser で動く Phaser game を Capacitor 経由で iOS native shell に出荷する。Vite build output、static asset paths、Phaser version differences、mobile scale/orientation、safe-area touch controls、audio unlock、WKWebView lifecycle、SPM、Xcode、sync/run、signing、Safari WebView debugging の境界で使う。

browser-only gameplay は `phaser-gamedev` を使う。Phaser 4.x、migration、renderer internals、filters、lighting、shaders、render textures、GPU layers、texture orientation に触れる場合は `phaser4-gamedev` も使う。

## 基本方針: Two Runtimes, One Game Contract

project を合意すべき systems として扱う。

- web game runtime: Phaser + Vite + browser APIs
- native wrapper: Capacitor iOS + WKWebView + Xcode/SPM

build output、asset URLs、scene startup、scale mode、orientation、input、audio unlock、safe-area layout、pause/resume、package manager、signing を explicit / testable にする。

作業前に確認すること:

- Phaser version
- exact Vite output directory と Capacitor `webDir`
- WKWebView origin で動く assets / loader URLs
- scale/orientation、pixel-art rules、DPR cap、iOS orientation policy、safe-area placement
- desktop と iOS の input plan
- first-gesture audio unlock、silent-mode expectations、pause/resume
- WKWebView lifecycle、WebGL context loss、simulator/device debugging、scene cleanup
- macOS、Node、Xcode、Command Line Tools、Capacitor iOS version
- SPM / CocoaPods の選択
- bundle id、Apple Developer team、capabilities、permission strings、archive/export

優先順位:

1. scene list、loader keys、asset paths、scale behavior が安定した boot
2. modern Capacitor では plugin / existing project が強制しない限り SPM を優先
3. touch、audio unlock、safe areas、orientation、resize を iOS-first に扱う
4. native run は fresh build + sync 済み assets を使う
5. missing assets、loader failures、blank canvas、WebGL failures、stale bundles、package/signing errors を早期診断する

## 参照ファイル

| Topic | File | Use When |
| --- | --- | --- |
| iOS workflow | [references/capacitor-ios-spm-workflow.md](references/capacitor-ios-spm-workflow.md) | setup、build/sync/run、simulator/device、SPM/CocoaPods、signing |
| Phaser iOS runtime | [references/phaser-ios-runtime-patterns.md](references/phaser-ios-runtime-patterns.md) | Phaser config、scene boot、asset paths、safe areas、touch、audio unlock、orientation、pause/resume |
| Phaser 4 iOS rendering | [references/phaser4-ios-rendering.md](references/phaser4-ios-rendering.md) | confirmed Phaser 4、migration、filters、lighting、shaders、render targets、GPU layers |
| Gotchas | [references/gotchas.md](references/gotchas.md) | browser works but iOS fails、loader/audio/touch/scale/WebGL/Xcode/SPM/signing |

## Quick Start

1. `package.json`、`vite.config.*`、`capacitor.config.*`、Phaser entry points、scenes、asset folders、existing `ios/` を確認
2. local dependencies / vendored bundles から Phaser major/minor と Capacitor major を特定
3. project-native command で build。通常 `npm run build`
4. Capacitor `webDir` を output に合わせる。通常 `"dist"`
5. iOS がなければ `@capacitor/ios` を install し、project が CocoaPods を必要としない限り `npx cap add ios --packagemanager SPM`
6. deterministic loop:
   - `npm run build`
   - `npx cap sync ios`
   - `npx cap run ios` または `npx cap open ios`

可能なら build/sync を飛ばせない scripts を追加する。

## 実装ガイド

### Project Shape

- Phaser code: `index.html` と `src/*`
- file として serve する assets: `public/assets/...`
- Vite 既定では `capacitor.config.ts` に `webDir: "dist"`
- `ios/App/` は Capacitor generated を使い、ad hoc に作り直さない
- loading/progress/error reporting は boot/preload scene が持つ

runtime loads は desktop browser と WKWebView の両方で動くようにする。

- Good: `this.load.image('player', '/assets/player.png')`
- Good: `this.load.tilemapTiledJSON('level-1', '/assets/maps/level-1.json')`
- Avoid: filesystem paths、`file://` assumptions、dev-machine hostnames、Vite dev server rewrites 依存

iOS bundled assets は Capacitor の WKWebView 内で serve される。`public/assets` から built web output にコピーされた files には absolute `/assets/...` が通常有効。

### Phaser Runtime Contract

- Phaser 3/4 の renderer、filters、pipelines、texture behavior、APIs は違う
- version 不明なら API-sensitive edits を止める
- Phaser 4 では `references/phaser4-ios-rendering.md` を読んでから renderer-sensitive changes
- iOS failure の原因でない限り existing scene model を保つ
- fixed virtual resolution + `FIT`、responsive canvas + `RESIZE`、pixel-art integer scaling を意図して選ぶ
- high-DPI iPhones/iPads では effective resolution を cap
- CSS、viewport metadata、Phaser config を合わせ、WKWebView で scroll や home-indicator overlap を避ける

### Assets / Scenes / State

- assets は `preload()` または boot scene で load
- spritesheet frame width/height、spacing、margin を測定してから animations
- animations は once per lifecycle、または `this.anims.exists(key)` で guard
- gameplay、UI、loading、menus は ownership が明確な scenes に分ける
- scene data、registries、typed state modules を global `window` より優先
- projectiles、enemies、particles は pool
- simulator/device failures の debug 中は loader diagnostics を足す

### iOS Input / Audio / Safe Areas / Lifecycle

- desktop input と iOS touch/virtual controls を両方 map
- multi-touch controls には active pointers を追加
- container/canvas に `touch-action: none`、必要なら document scrolling を防ぐ
- notch、rounded corners、home indicator 付近では CSS `env(safe-area-inset-*)`
- audio は first user gesture 後に start/resume
- silent-mode behavior が重要なら real device で chosen strategy を確認
- Capacitor `pause` で pause/mute、`resume` で意図して復帰
- iOS には physical back button がない。back navigation は in-game UI、gesture、menu state、route history、native navigation policy で model 化する

### Performance / Stability

- draw calls / load churn が問題なら atlases
- high-DPI iOS では render resolution を cap
- major rewrite 前に FPS、active objects、physics bodies、tweens、timers、particles、cache size を測定
- object churn、collision explosions、oversized textures、culling を先に直す
- every frame の object/tween/sound creation を避ける
- repeat spawns には object pools を使う
- scene shutdown で timers/listeners/subscriptions を止める
- Phaser loader errors を listen し、失敗した key または URL を surface する
- backgrounding で simulation/audio を pause
- iOS では custom pipelines、render textures、large textures、filters、memory pressure による WebGL context loss を想定
- touch、safe area、orientation、audio、performance が重要な場合は simulator または real device で app を検証する

### Capacitor iOS Integration

project の Capacitor major version に合う official docs を source of truth にする。Node、Xcode、Command Line Tools、iOS deployment target、package manager、signing を local project で確認する。

確認:

- `node --version`
- `npm ls @capacitor/core @capacitor/cli @capacitor/ios`
- `xcode-select -p`
- `npx cap doctor`
- native files に触る場合は Xcode build / package resolution

native config、plugins、permissions、signing、web assets 変更後は `npx cap sync ios`。

live reload は development-only。`server.url` は reachable LAN host かつ development config のみにする。release builds 前に消す。

release builds には Apple Developer signing、bundle id、capabilities、permission usage strings、archive/export、App Store/TestFlight policy checks が必要。

## 避けること

**Phaser version を推測する**

問題: Phaser 3 と 4 の renderer、filter、texture、API 差分により、小さな修正が regression になり得る。
改善: version-sensitive code を編集する前に dependencies、vendored banners、script tags、runtime `Phaser.VERSION` を確認する。

**Phaser 4 を drop-in Phaser 3 upgrade として扱う**

問題: code が compile しても filters、masks、tint、camera rounding、render targets、texture orientation、custom pipelines の挙動が変わり得る。
改善: hotspot search を実行し、mechanical / behavioral / architectural に分類してから browser と iOS で visual output を検証する。

**SPM と CocoaPods assumptions を混ぜる**

問題: dependency drift と壊れた Xcode project expectations を生む。
改善: project ごとに package manager を1つ選ぶ。modern setup では plugin または existing project が CocoaPods を強制しない限り SPM を優先する。

**web assets を rebuild せず iOS を run する**

問題: simulator/device が stale JS、CSS、assets を表示する。
改善: `cap sync` と `cap run` の前に必ず build する scripts を使う。

**dev-server-only asset paths を使う**

問題: Vite dev server では解決できても、bundled WKWebView assets では解決できない path がある。
改善: production build 後も生きる stable `/assets/...` URLs または imported bundle URLs で public assets を load する。

**wrong lifecycle で load/create する**

問題: assets missing、animations duplicated、scene restart 後の event handler leaks を起こす。
改善: `preload()` で load、`create()` で create、delta time で update し、scene shutdown で cleanup する。

**iOS を desktop Safari と同一視する**

問題: WKWebView は lifecycle、memory pressure、safe-area、audio policy、remote debugging、packaging behavior が異なる。
改善: simulator または device で test し、Safari Develop tools で WebView を inspect し、pause/resume/context loss を扱う。

**development `server.url` を ship する**

問題: `server.url` は app を dev machine または remote web bundle に向け、release の security / performance behavior を変える。
改善: intentional live-update architecture がない限り、production では `server.url` を削除して built assets を ship する。

**requirement が証明される前に shaders / filters / GPU layers から始める**

問題: advanced renderer paths は render passes、fill-rate、WebGL-only behavior、version-specific failure modes を増やす。
改善: requirement が specialized path を証明するまで standard game objects、atlases、pooling、culling、measured profiling を使う。

## 検証

```bash
npm run typecheck
npm run lint
npm test
npm run build
```

iOS-facing changes では次を確認する。

- latest build 後に `npx cap sync ios`
- simulator/device が fresh bundle を起動
- canvas が nonblank、size 正常、Safari Web Inspector console loader errors なし
- boot、preload、scene transitions、pause/resume、restart、UI overlays
- touch controls、audio unlock、orientation、safe-area layout、home-indicator spacing
- delta/physics movement、animations、atlases、tilemaps、collision bodies、camera bounds、pixel-art rounding
- Phaser 4 renderer work の filters、lighting、render textures、GPU layers、texture orientation、FPS
- device/release scope では Xcode signing、bundle id、capabilities、permission strings

実行できない check は理由と remaining risk を伝える。

## Variation Guidance

デフォルトで同一の mobile wrappers を作らない。game に合わせて実装を調整する:

- arcade/action: responsive controls、low latency、pooling、pause、stable FPS
- platformer: fixed virtual resolution、camera rounding、collision debug、virtual buttons、home-indicator spacing
- pixel art: `pixelArt`、nearest-neighbor CSS、integer-friendly scale、texture bleeding
- Tiled RPG/map-heavy: tilemap paths、layer collisions、camera bounds、asset pack structure
- menu/visual novel: safe areas、text layout、gesture policy、audio focus
- asset QA: diagnostics overlay、loader error list、texture dimensions、FPS、simulator/device screenshots

scale mode、orientation、safe-area layout、touch layout、audio behavior、scene boundaries、Xcode/SPM/signing workflow は target に合わせて変える。

## 覚えておくこと

Phaser + Capacitor iOS は explicit contracts と disciplined workflow で成功する。Phaser/Capacitor versions を確認し、scene/asset boot を deterministic にし、iOS touch/audio/safe-area/lifecycle behavior を設計し、Xcode/SPM toolchain と build/sync/run を repeatable にする。
