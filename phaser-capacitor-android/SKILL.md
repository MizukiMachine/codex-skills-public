---
name: phaser-capacitor-android
description: "Capacitor Android上のPhaser 3/4ゲームをViteとGradleで構築・出荷する。入力、音声、WebView、戻るボタン、Android同期・署名、ADB/エミュレータ連携の調査で使う。"
metadata:
  short-description: "Phaser + Capacitor Android/ADB ワークフロー"
---

# Phaser Capacitor Android

browser で動く Phaser game を Capacitor 経由で Android native shell に出荷する。Vite build output、static asset paths、Phaser version differences、mobile scale/orientation、touch/audio、Android WebView lifecycle、Gradle、sync/run、signing、WSL2 emulator / ADB workflow の境界で使う。

browser-only gameplay は `phaser-gamedev` を使う。Phaser 4.x 確認済み、ユーザーが Phaser 4 を求めた、migration / renderer / filters / lighting / shaders / render textures / GPU layers / texture orientation に触れる場合は `phaser4-gamedev` も使う。

## 基本方針: Two Runtimes, One Game Contract

project を合意すべき systems として扱う。

- web game runtime: Phaser + Vite + browser APIs
- native wrapper: Capacitor Android + Android System WebView + Gradle
- host boundary: Linux/WSL builds、Windows Android Studio/emulator、ADB device ownership

失敗の多くは contract が implicit なときに起きる。build output、asset URLs、scene startup、scale mode、orientation、input、audio unlock、pause/resume、signing を explicit / testable にする。

作業前に確認すること:

- Phaser version
- exact Vite output directory と Capacitor `webDir`
- assets の配置と Android WebView origin で動く loader URLs
- scale/orientation、pixel-art rules、DPR cap、Android orientation policy
- desktop と mobile の input plan
- first-gesture audio unlock、pause/resume
- WebView pause/resume、WebGL context loss、hardware back button、scene cleanup
- Capacitor、Android Studio、SDK、Gradle JDK、`adb`
- WSL2/Linux と Windows device host の分離

優先順位:

1. scene list、loader keys、asset paths、scale behavior が安定した contract-first boot
2. Android toolchain の先行検証
3. touch、audio unlock、orientation、safe areas、resize を mobile-first に扱う
4. native run は fresh build + sync 済み assets を使う
5. missing assets、loader failures、blank canvas、WebGL failures、stale bundles を小さな runtime checks で早期診断する

## 参照ファイル

| Topic | File | Use When |
| --- | --- | --- |
| Android workflow | [references/capacitor-android-workflow.md](references/capacitor-android-workflow.md) | setup、build/sync/run、emulator/device、live reload、signing |
| WSL2 + Windows Emulator | [references/windows-wsl-emulator-workflow.md](references/windows-wsl-emulator-workflow.md) | WSL2/Linux project、Windows Android Studio/Emulator、WSL emulator controls が不安定 |
| Phaser mobile runtime | [references/phaser-mobile-runtime-patterns.md](references/phaser-mobile-runtime-patterns.md) | Phaser config、scene boot、asset paths、touch、audio unlock、scale/orientation、pause/resume |
| Phaser 4 Android rendering | [references/phaser4-android-rendering.md](references/phaser4-android-rendering.md) | confirmed Phaser 4、migration、filters、lighting、shaders、render targets、GPU layers |
| Gotchas | [references/gotchas.md](references/gotchas.md) | browser works but Android fails、loader/audio/touch/scale/WebGL/Gradle/ADB |

## Quick Start

1. `package.json`、`vite.config.*`、`capacitor.config.*`、Phaser entry points、scenes、asset folders を確認
2. local dependencies / vendored bundles から Phaser major/minor と Capacitor major を特定
3. project-native command で build。通常 `npm run build`
4. Capacitor `webDir` を build output に合わせる。通常 `"dist"`
5. Android がなければ `@capacitor/android` を install し `npx cap add android`
6. 通常 loop:
   - `npm run build`
   - `npx cap sync android`
   - `npx cap run android` または `npx cap open android`

可能なら build/sync を飛ばせない project scripts を追加する。

WSL2 + Windows Android Studio / emulator では plain `cap run/open` を既定にしない。device host を先に決める。

- WSL-built APK を Windows `adb.exe` で install: TypeScript、Phaser scenes、CSS、assets、Capacitor config の smoke test に向く
- Windows native Android Studio で開く: Gradle、manifest、plugin code、signing、Logcat、profilers、resource editors に向く

WSL 側 emulator GUI / Linux `adb` が不安定な場合は Windows emulator/device host を使い、APK paths は `wslpath -w` で変換する。

## 実装ガイド

### Project Shape

- Phaser code: `index.html` と `src/*`
- file として serve する images、atlases、audio、tilemaps、JSON packs、fonts: `public/assets/...`
- Vite 既定では `capacitor.config.ts` に `webDir: "dist"`
- loading、progress、loader error reporting は small boot/preload scene が所有する

runtime loads は desktop browser と Android System WebView の両方で動くようにする。

- Good: `this.load.image('player', '/assets/player.png')`
- Good: `this.load.tilemapTiledJSON('level-1', '/assets/maps/level-1.json')`
- Avoid: filesystem paths、`file://` assumptions、dev-machine hostnames、Vite dev server rewrites に依存する paths

Android bundled assets は local WebView origin で serve される。`public/assets` の files には absolute `/assets/...` URLs が通常有効。routing/live-reload 理由なしに Android scheme や `server.url` を変えない。

### Phaser Runtime Contract

- Phaser 3/4 の renderer、filters、pipelines、texture behavior、APIs は違う
- version 不明なら API-sensitive edits を止める
- Phaser 4 では `references/phaser4-android-rendering.md` を読んでから renderer-sensitive changes
- scene model は Android failure の原因でない限り保つ
- fixed virtual resolution + `FIT`、responsive canvas + `RESIZE`、pixel-art integer scaling を意図して選ぶ
- high-DPI Android では effective resolution を cap する
- CSS と Phaser config を合わせ、WebView 内で canvas が scroll/zoom しないようにする

### Assets / Scenes / State

- assets は `preload()` または boot scene で load
- spritesheet frame width/height、spacing、margin を測定してから animations
- animations は once per lifecycle、または `this.anims.exists(key)` で guard
- gameplay、UI、loading、menus は clear ownership の scenes に分ける
- global `window` state より scene data、registries、typed state modules
- projectiles、enemies、particles などは pool

tilemaps、atlases、spritesheets、physics、general gameplay は `phaser-gamedev` も使う。

### Mobile Input / Audio / Back Button

- desktop keyboard/mouse/gamepad と Android touch/virtual controls を両方設計する
- multi-touch controls には active pointers を増やす
- canvas/container に `touch-action: none` を設定し、WebView gestures に scroll/zoom されないようにする
- audio は first user gesture 後に start/resume。Capacitor `pause` で pause/mute、`resume` で意図して復帰
- hardware back button は `@capacitor/app` で扱う。閉じる state、route stack、menu、pause screen があるなら product rule を定義する

### Performance / Stability

- draw calls / load churn が問題なら atlases
- high-DPI screens で effective render resolution を cap
- major rewrite 前に `game.loop.actualFps`、active objects、physics bodies、tweens、timers、particles、loader/cache size を測定
- object churn、collision explosions、oversized textures、culling を先に直す
- every frame で sprites/text/graphics/tweens/sounds を作らない
- repeat spawns には object pools を使う
- scene shutdown で timers、listeners、subscriptions を止める
- Phaser loader errors を listen し、失敗した key または URL を surface する
- app backgrounding で simulation/audio を pause
- Android では WebGL context loss を想定する。特に custom pipelines、render textures、large textures で起きやすい
- touch、orientation、audio、performance が重要な場合は real device または emulator で app を検証する

### Capacitor Android Integration

project の Capacitor major version に合う official docs を source of truth にする。Node、Android Studio、Android SDK platform、Gradle JDK、target SDK を local project で確認する。

確認:

- `node --version`
- `npm ls @capacitor/core @capacitor/cli @capacitor/android`
- `npx cap doctor`
- `adb devices`
- native files に触る場合は Android Studio Gradle sync

native config、plugins、permissions、signing、web assets を変えた後は `npx cap sync android`。

WSL2 で Windows が Android Studio/Emulator を所有する場合:

- WSL で `npx cap sync android` + `./gradlew assembleDebug`
- Windows `adb.exe` で install / launch。APK path は `wslpath -w android/app/build/outputs/apk/debug/app-debug.apk`
- Android Studio が必要なら Windows `studio64.exe` に Windows-converted project path を渡す
- 1 session では ADB host を1つにする。Linux `adb` と Windows `adb.exe` を混ぜない

live reload は development-only。`server.url` を使う場合は reachable LAN/emulator host を使い、必要な場合だけ `server.cleartext: true` を設定する。release builds 前に `server.url` を消す。release には project-owned keystore が必要。debug builds は auto-sign。

## 避けること

**Phaser version を推測する**

問題: Phaser 3 と 4 の renderer、filter、texture、API 差分により、小さな修正が regression になり得る。
改善: version-sensitive code を編集する前に dependencies、vendored banners、runtime `Phaser.VERSION` を確認する。

**Phaser 4 を drop-in Phaser 3 upgrade として扱う**

問題: code が compile しても filters、masks、tint、camera rounding、render targets、texture orientation、custom pipelines の挙動が変わり得る。
改善: hotspot search を実行し、mechanical / behavioral / architectural に分類してから browser と Android で visual output を検証する。

**web assets を rebuild せず Android を run する**

問題: device/emulator が stale JS、CSS、assets を表示する。
改善: `cap sync` と `cap run` の前に必ず build する scripts を使う。

**dev-server-only asset paths を使う**

問題: Vite dev server では解決できても、bundled Android WebView assets では解決できない path がある。
改善: production build 後も生きる stable `/assets/...` URLs または imported bundle URLs で public assets を load する。

**wrong lifecycle で load/create する**

問題: assets missing、animations duplicated、scene restart 後の event handler leaks を起こす。
改善: `preload()` で load、`create()` で create、delta time で update し、scene shutdown で cleanup する。

**Android を browser-only bug として扱う**

問題: Android には WebView origin、lifecycle、audio policy、memory pressure、orientation、touch、hardware back behavior がある。
改善: WebView console を inspect し、device で touch/audio/orientation を検証し、pause/resume を test する。

**development `server.url` を ship する**

問題: `server.url` は app を dev machine または remote web bundle に向け、release の security / performance behavior を変える。
改善: intentional live-update architecture がない限り、production では `server.url` を削除して built assets を ship する。

**WSL2 で ADB hosts を混ぜる**

問題: Linux `adb` と Windows `adb.exe` が別 server と話し、devices が missing、offline、inconsistent に見える。
改善: device host を先に選ぶ。Windows が emulator を所有する場合は WSL から Windows `adb.exe` を実行し、APK path は `wslpath -w` で変換する。

**WSL 側 Android Studio を意図せず開く**

問題: WSL から `npx cap open android` すると wrong Android Studio/SDK/ADB path を開く、または target し、実際の Windows emulator が build workflow から切り離されることがある。
改善: smoke tests では WSL で APK を build し Windows `adb.exe` で install する。native Android editing では Windows `studio64.exe` を明示的に起動するか、Windows filesystem clone で作業する。

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

Android-facing changes では次を確認する。

- latest build 後に `npx cap sync android`
- device/emulator が fresh bundle を起動
- canvas が nonblank、size 正常、WebView console loader errors なし
- boot、preload、scene transitions、pause/resume、restart、UI overlays
- touch controls、audio unlock、orientation、hardware back、safe-area layout
- delta/physics movement、animations、atlases、tilemaps、collision bodies、camera bounds、pixel-art rounding
- Phaser 4 renderer work の filters、lighting、render textures、GPU layers、texture orientation、FPS

実行できない check は理由と remaining risk を伝える。

## Variation Guidance

game context で変える。

- arcade/action: responsive controls、low latency、pooling、pause、stable FPS
- platformer: fixed virtual resolution、camera rounding、collision debug、virtual buttons
- pixel art: `pixelArt`、nearest-neighbor CSS、integer-friendly scale、texture bleeding checks
- Tiled RPG/map-heavy: tilemap paths、layer collisions、camera bounds、asset pack structure
- menu/visual novel: safe areas、text layout、back-button rules、audio focus
- asset QA: diagnostics overlay、loader error list、texture dimensions、FPS、screenshots

scale mode、orientation、touch layout、audio behavior、scene boundaries、diagnostics visibility を意図して変える。

## 覚えておくこと

Phaser + Capacitor Android は explicit contracts と disciplined workflow で成功する。Phaser/Capacitor versions を確認し、scene/asset boot を deterministic にし、Android touch/audio/lifecycle behavior を設計し、toolchain と build/sync/run を repeatable にする。
