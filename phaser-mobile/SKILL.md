---
name: phaser-mobile
description: "Vite を使って、Capacitor の iOS / Android ネイティブシェル上で Phaser 3/4 ゲームを構築・出荷する。Vite ビルド出力、静的アセットパス、scene/asset boot、mobile scale/orientation、touch/audio、WKWebView/Android System WebView ライフサイクル、iOS の SPM/Xcode、Android の Gradle/ADB/WSL2 エミュレータ、sync/run/signing、Phaser 4 renderer 問題のトラブルシュートを扱う。"
metadata:
  short-description: "Phaser + Capacitor iOS/Android ワークフロー"
---

# Phaser Capacitor (iOS / Android)

browser で動く Phaser game を Capacitor 経由で iOS / Android の native shell に出荷するスキル。Vite build output、static asset paths、Phaser version differences、mobile scale/orientation、touch/audio、WebView lifecycle、native の sync/run/signing など、障害が最も発生しやすい統合境界に焦点を当てる。

browser-only gameplay は `phaser-gamedev` を使う。Phaser 4.x 確認済み、ユーザーが Phaser 4 を求めた、migration / renderer / filters / lighting / shaders / render textures / GPU layers / texture orientation に触れる場合は `phaser4-gamedev` も使う。

**重要: ウェブ/Phaser レイヤーは iOS と Android でほぼ同一**。異なるのはネイティブシェル・ライフサイクル・ツールチェーン・ストアビルドのワークフローだけ:

| | iOS | Android |
| --- | --- | --- |
| ネイティブシェル | WKWebView | Android System WebView (Chromium) |
| パッケージ/ビルド | Swift Package Manager + Xcode | Gradle + Android Studio |
| ホスト OS | macOS 必須 | Windows / Linux(WSL2 含む) / macOS |
| back navigation | 物理ボタンなし（in-game UI/gesture でモデル化） | ハードウェアバックボタン（`@capacitor/app`） |
| 主なハマりどころ | SPM/CocoaPods、signing、セーフエリア、silent-mode audio | JDK/SDK、ADB、WSL2↔Windows、ハードウェアバック |

両方をターゲットにする場合でも、ウェブ/Phaser 層は1度だけ書き、ネイティブ層だけプラットフォームごとに揃える。

## 基本方針: Two Runtimes, One Game Contract

project を合意すべき systems として扱う。

- web game runtime: Phaser + Vite + browser APIs
- native wrapper: Capacitor + WKWebView/Android System WebView + Xcode-SPM/Gradle

Android で開発環境が分割されている場合は、host boundary も contract として扱う:
- build host: Node/Vite/Capacitor build と Gradle assemble を実行する場所
- device host: `adb`、Android Studio、emulator/実機接続が存在する場所
- path bridge: WSL2 → Windows の `wslpath -w` など

失敗の多くは contract が implicit なときに起きる。build output、asset URLs、scene startup、scale mode、orientation、input、audio unlock、pause/resume、signing を explicit / testable にする。

作業前に確認すること（共通）:

- Phaser version
- exact Vite output directory と Capacitor `webDir`
- assets の配置と WebView origin で動く loader URLs（`/assets/...`）
- scale/orientation、pixel-art rules、DPR cap、orientation policy
- desktop と mobile の input plan
- first-gesture audio unlock、pause/resume
- WebView lifecycle、WebGL context loss、scene cleanup

作業前に確認すること（iOS）:

- macOS、Node、Xcode、Command Line Tools が Capacitor major version と一致
- SPM / CocoaPods の選択とプラグイン互換性
- safe-area placement、silent-mode expectations
- bundle id、Apple Developer team、capabilities、permission strings、archive/export

作業前に確認すること（Android）:

- Capacitor バージョンに対応した JDK（Android Studio 同梱の互換 JDK が通常使われる。手動設定時は Capacitor の環境セットアップドキュメントに従う — 例: Capacitor 8 → JDK 17+）、`ANDROID_HOME`/SDK 設定済みか
- WSL2/Linux build + Windows emulator 構成か（その場合 Windows `adb.exe` と明示的なパス変換が必要）
- hardware back button の product rule

優先順位:

1. scene list、loader keys、asset paths、scale behavior が安定した contract-first boot
2. ツールチェーンファースト: iOS は Xcode + SPM、Android は Android Studio + SDK + Gradle JDK + `adb` を先行検証
3. touch、audio unlock、orientation、(iOS) safe areas、resize を mobile-first に扱う
4. native run は fresh build + sync 済み assets を使う
5. missing assets、loader failures、blank canvas、WebGL failures、stale bundles、package/signing errors を小さな runtime checks で早期診断する

## クイックスタートワークフロー

1. `package.json`、`vite.config.*`、`capacitor.config.*`、Phaser entry points、scenes、asset folders、既存の `ios/`・`android/` を確認する。
2. local dependencies / vendored bundles から Phaser major/minor と Capacitor major を特定する。
3. project-native command で build する（通常 `npm run build`）。
4. 静的アセットは `public/assets/...` に置き、absolute URL（`/assets/...`）で読み込む。
5. Capacitor の `webDir` を build output に合わせる（通常 `"dist"`）。
6. ターゲットプラットフォームを追加する:
   - iOS: `npm install @capacitor/ios` → `npx cap add ios --packagemanager SPM`（project が CocoaPods を必要としない限り）
   - Android: `npm install @capacitor/android` → `npx cap add android`
7. 決定論的なループを繰り返す:
   - `npm run build`
   - `npx cap sync ios` / `npx cap sync android`
   - `npx cap run ios` / `npx cap run android`（または `npx cap open ...`）

可能なら build/sync を飛ばせないスクリプトを追加する。コマンドレベルの詳細はプラットフォーム別ワークフローリファレンスを参照。

**WSL2 プロジェクト + Windows エミュレータの場合（Android）**、まずどちらのパスが速いかを決める:
- WSL でビルドした APK を Windows `adb.exe` でインストールする: TypeScript、Phaser scenes、CSS、assets、Capacitor config の smoke test に最適。
- Android プロジェクトを Windows の Android Studio で開く: Gradle、manifest、plugin code、signing、Logcat、profilers を使う場合に最適。

ユーザーのゴールが Android アプリのスモークテストのときに、不安定な WSL2 エミュレータ GUI のデバッグへデフォルトで突入しないこと。代わりに Windows のエミュレータ/デバイスホストを使い、APK paths は `wslpath -w` で変換する。手順は `references/windows-wsl-emulator-workflow.md`。

## 参照ファイル

| トピック | ファイル | 使う場面 |
| --- | --- | --- |
| iOS ワークフロー | [references/capacitor-ios-spm-workflow.md](references/capacitor-ios-spm-workflow.md) | iOS のセットアップ、build/sync/run、simulator/実機、SPM/CocoaPods、signing |
| Android ワークフロー | [references/capacitor-android-workflow.md](references/capacitor-android-workflow.md) | Android のセットアップ、build/sync/run、emulator/実機、live reload、signing |
| WSL2 + Windows エミュレータ | [references/windows-wsl-emulator-workflow.md](references/windows-wsl-emulator-workflow.md) | WSL2/Linux プロジェクト、Windows の Android Studio/エミュレータ、WSL からのエミュレータ操作が不安定 |
| Phaser mobile runtime | [references/phaser-mobile-runtime-patterns.md](references/phaser-mobile-runtime-patterns.md) | Phaser config、scene boot、asset paths、touch、audio unlock、scale/orientation、safe areas、pause/resume、back button（iOS/Android 共通＋差分） |
| Phaser 4 rendering | [references/phaser4-rendering.md](references/phaser4-rendering.md) | confirmed Phaser 4、migration、filters、lighting、shaders、render targets、GPU layers、texture orientation |
| Gotchas | [references/gotchas.md](references/gotchas.md) | browser works but device fails、共通＋iOS（SPM/Xcode/signing/safe-area）＋Android（Gradle/JDK/SDK/ADB/back button） |

## 実装ガイド

### Project Shape

- Phaser code: `index.html` と `src/*`
- file として serve する images、atlases、audio、tilemaps、JSON packs、fonts: `public/assets/...`
- Vite 既定では `capacitor.config.ts` に `webDir: "dist"`
- ネイティブプロジェクト（`ios/App/`・`android/`）は Capacitor generated を使い、ad hoc に作り直さない
- loading、progress、loader error reporting は small boot/preload scene が所有する

runtime loads は desktop browser と両プラットフォームの WebView（WKWebView / Android System WebView=Chromium）の両方で動くようにする。

- Good: `this.load.image('player', '/assets/player.png')`
- Good: `this.load.tilemapTiledJSON('level-1', '/assets/maps/level-1.json')`
- Avoid: filesystem paths、`file://` assumptions、dev-machine hostnames、Vite dev server rewrites に依存する paths

**スキームに関する注意**: Android はデフォルトで `server.androidScheme` を通じて `https://localhost` から bundled web assets を配信する。absolute `/assets/...` URL はこの origin 下で正しく解決される。routing 上の具体的な理由なしに `androidScheme` を変えないこと。iOS でも bundled assets は WKWebView 内の origin で配信され、`/assets/...` が通常有効。

### Phaser Runtime Contract

- Phaser 3/4 の renderer、filters、pipelines、texture behavior、APIs は違う
- version 不明なら API-sensitive edits を止める
- Phaser 4 では `references/phaser4-rendering.md` を読んでから renderer-sensitive changes
- scene model は device failure の原因でない限り保つ
- fixed virtual resolution + `FIT`、responsive canvas + `RESIZE`、pixel-art integer scaling を意図して選ぶ
- high-DPI な端末では effective resolution を cap する
- CSS、viewport metadata、Phaser config を合わせ、WebView 内で canvas が scroll/zoom したり home-indicator(iOS) と重ならないようにする

### Assets / Scenes / State

- assets は `preload()` または boot scene で load
- spritesheet frame width/height、spacing、margin を測定してから animations
- animations は once per lifecycle、または `this.anims.exists(key)` で guard
- gameplay、UI、loading、menus は clear ownership の scenes に分ける
- global `window` state より scene data、registries、typed state modules
- projectiles、enemies、particles などは pool
- simulator/emulator/device failures の debug 中は loader diagnostics を足す

tilemaps、atlases、spritesheets、physics、general gameplay は `phaser-gamedev` も使う。

### Mobile Input / Audio / Lifecycle / Back

- desktop keyboard/mouse/gamepad と mobile touch/virtual controls を両方設計する
- multi-touch controls には active pointers を増やす
- canvas/container に `touch-action: none` を設定し、WebView gestures に scroll/zoom されないようにする
- **(iOS)** notch、rounded corners、home indicator 付近では CSS `env(safe-area-inset-*)`
- audio は first user gesture 後に start/resume。Capacitor `pause` で pause/mute、`resume` で意図して復帰。**(iOS)** silent-mode behavior が重要なら real device で確認
- **(Android)** hardware back button は `@capacitor/app` で扱う。閉じる state、route stack、menu、pause screen があるなら product rule を定義する
- **(iOS)** physical back button はない。back navigation は in-game UI、gesture、menu state、route history で model 化する

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
- mobile では custom pipelines、render textures、large textures、filters、memory pressure による WebGL context loss を想定する
- touch、orientation、audio、(iOS) safe area、performance が重要な場合は real device または emulator/simulator で app を検証する

### Capacitor Native Integration

project の Capacitor major version に合う official docs を source of truth にする。現行の Capacitor 8 系では概ね Node 22+。native config、plugins、permissions、signing、web assets を変えた後は `npx cap sync ios`/`npx cap sync android` を再実行する。

**iOS:**
- macOS、Xcode、Command Line Tools、iOS deployment target、Swift Package Manager。
- 確認: `node --version` / `npm ls @capacitor/core @capacitor/cli @capacitor/ios` / `xcode-select -p` / `npx cap doctor` / Xcode のビルドとパッケージ解決。
- Capacitor 8+ ではデフォルトで SPM。既存の CocoaPods プロジェクトは意図的に移行する（移行アシスタントまたは iOS プラットフォームの再作成）。生成された `CapApp-SPM` の内部を手で編集しない。
- release builds には Apple Developer signing、bundle id、capabilities、permission usage strings、archive/export が必要。

**Android:**
- Capacitor バージョンに対応した JDK（通常は Android Studio に互換 JDK が同梱。`JAVA_HOME` を手動設定する場合は Capacitor docs に従う — 例: Capacitor 8 → JDK 17+）。
- Android SDK + platform-tools（`ANDROID_HOME` を設定し、`adb` を PATH に）。
- Android Studio（または CLI Gradle）— Windows、Linux（WSL2 含む）、macOS で動作。Mac は不要。
- 確認: `node --version` / `npm ls @capacitor/core @capacitor/cli @capacitor/android` / `npx cap doctor` / `adb devices` / Android Studio の Gradle sync。
- release builds には独自の keystore が必要（debug builds は自動署名）。
- WSL2 で Windows が emulator を所有する場合: WSL で `npx cap sync android` + `./gradlew assembleDebug` して Windows `adb.exe` で install/launch。APK path は `wslpath -w`。1 session では ADB host を1つにする。

live reload は development-only。`server.url` を使う場合は reachable host を指定し（Android で必要なときだけ `server.cleartext: true`）、release builds 前に必ず消すこと。詳細はプラットフォーム別ワークフローリファレンスを参照。

## 避けること

**Phaser version を推測する**
問題: Phaser 3 と 4 の renderer、filter、texture、API 差分により、小さな修正が regression になり得る。
改善: version-sensitive code を編集する前に dependencies、vendored banners、script tags、runtime `Phaser.VERSION` を確認する。

**Phaser 4 を drop-in Phaser 3 upgrade として扱う**
問題: code が compile しても filters、masks、tint、camera rounding、render targets、texture orientation、custom pipelines の挙動が変わり得る。
改善: hotspot search を実行し、mechanical / behavioral / architectural に分類してから browser と device で visual output を検証する。

**モバイルをデスクトップブラウザと同一視する**
問題: WKWebView / Android System WebView には独自の origin、lifecycle、memory pressure、audio policy、input 挙動（iOS のセーフエリア、Android のバックボタン）があり、desktop Chrome/Safari では露出しない。
改善: simulator/emulator または実機で、bundled asset paths、touch 挙動、context loss 処理、WebView console を確認する。

**web assets を rebuild せず native を run する**
問題: device/emulator/simulator が stale JS、CSS、assets を表示する。
改善: `cap sync` と `cap run` の前に必ず build する scripts を使う。

**dev-server-only asset paths を使う**
問題: Vite dev server では解決できても、bundled WebView assets では解決できない path がある。
改善: production build 後も生きる stable `/assets/...` URLs または imported bundle URLs で public assets を load する。

**wrong lifecycle で load/create する**
問題: assets missing、animations duplicated、scene restart 後の event handler leaks を起こす。
改善: `preload()` で load、`create()` で create、delta time で update し、scene shutdown で cleanup する。

**SPM と CocoaPods assumptions を混ぜる（iOS）**
問題: dependency drift と壊れた Xcode project expectations を生む。
改善: project ごとに package manager を1つ選ぶ。modern setup では plugin が CocoaPods を強制しない限り SPM を優先。

**不一致な JDK / 未設定の SDK / 古い Gradle 状態（Android）**
問題: Gradle が "unsupported class file" / "SDK location not found" などで失敗する。
改善: Android Studio 同梱の Gradle JDK（または Capacitor docs 指定のバージョン）を使い、`ANDROID_HOME`/`local.properties` を設定し、`npx cap doctor` を実行してから Gradle sync / clean する。

**WSL2 で ADB hosts を混ぜる（Android）**
問題: Linux `adb` と Windows `adb.exe` が別 server と話し、devices が missing/offline/inconsistent に見える。
改善: device host を先に1つ選ぶ。Windows が emulator を所有する場合は WSL から Windows `adb.exe` を実行し、APK path は `wslpath -w` で変換する。

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

device-facing changes では次を確認する。

- latest build 後に `npx cap sync ios` / `npx cap sync android`
- simulator/emulator/device が fresh bundle を起動
- canvas が nonblank、size 正常、WebView console（Safari Web Inspector / `chrome://inspect`）に loader errors なし
- boot、preload、scene transitions、pause/resume、restart、UI overlays
- touch controls、audio unlock、orientation、(iOS) safe-area layout / home-indicator spacing、(Android) hardware back
- delta/physics movement、animations、atlases、tilemaps、collision bodies、camera bounds、pixel-art rounding
- Phaser 4 renderer work の filters、lighting、render textures、GPU layers、texture orientation、FPS
- device/release scope では署名情報（iOS: Xcode signing、bundle id、capabilities、permission strings / Android: keystore）

実行できない check は理由と remaining risk を伝える。

## Variation Guidance

デフォルトで同一の mobile wrappers を作らない。game に合わせて実装を調整する:

- arcade/action: responsive controls、low latency、pooling、pause、stable FPS
- platformer: fixed virtual resolution、camera rounding、collision debug、virtual buttons、(iOS) home-indicator spacing
- pixel art: `pixelArt`、nearest-neighbor CSS、integer-friendly scale、texture bleeding checks
- Tiled RPG/map-heavy: tilemap paths、layer collisions、camera bounds、asset pack structure
- menu/visual novel: safe areas、text layout、back-button rules(Android)/gesture policy(iOS)、audio focus
- asset QA: diagnostics overlay、loader error list、texture dimensions、FPS、screenshots

scale mode、orientation、(iOS) safe-area layout、touch layout、audio behavior、scene boundaries、diagnostics visibility、native build/signing workflow を意図して target に合わせて変える。汎用的な mobile wrapper に収束しないこと。

## 覚えておくこと

Phaser + Capacitor（iOS / Android）は explicit contracts と disciplined workflow で成功する。Phaser/Capacitor versions を確認し、scene/asset boot を deterministic にし、mobile touch/audio/lifecycle behavior（iOS の safe-area、Android の back button）を設計し、ターゲットの native toolchain（iOS: Xcode/SPM、Android: Android Studio/Gradle）と build/sync/run を repeatable にする。ウェブ/Phaser 層は1度書き、ネイティブ層だけプラットフォームごとに揃える。
