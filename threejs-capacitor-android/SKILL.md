---
name: threejs-capacitor-android
description: "Vite と Gradle を使って、Capacitor Android 上で Three.js アプリを構築・リリースする。GLTF読み込み、assets_index によるアニメーションUI、OrbitControls のマウス/タッチ対応、Android の sync/run/署名、WSL2 + Windows エミュレータ/ADB のトラブルシュートを扱う。"
metadata:
  short-description: "Three.js + Capacitor Android/ADB ワークフロー"
---

# Three.js Capacitor Android

Capacitor を通じて Android ネイティブシェルで動作するインタラクティブな Three.js アプリを構築・リリースするスキル。
ウェブビルド出力、アニメーションコントラクト、コントロール、Android WebView ライフサイクル、ネイティブの sync/run/signing ワークフローなど、障害が最も発生しやすい統合境界に焦点を当てる。

iOS ターゲットには `threejs-capacitor-ios` スキルを使用する。ウェブ/Three.js レイヤーは両者でほぼ同一であり、異なるのはネイティブシェル・ライフサイクル・ツールチェーン・ストアビルドのワークフロー（Gradle/Android Studio vs SPM/Xcode）のみ。

## 哲学: 2つのランタイム、1つのコントラクト

プロジェクトを合意が必要な2つのシステムとして扱う:
- ウェブレンダラーランタイム（Three.js + Vite + ブラウザ API）
- ネイティブランタイムラッパー（Capacitor Android + Android System WebView + Gradle）

開発環境が分割されている場合は、ホスト境界もコントラクトとして扱う:
- ビルドホスト: Node/Vite/Capacitor のビルドと Gradle assemble を実行する場所
- デバイスホスト: `adb`、Android Studio、エミュレータ/実機接続が存在する場所
- パスブリッジ: WSL2 → Windows の `wslpath -w` など

ほとんどの障害はコントラクトが暗黙的な場合に発生する。
ファイルパス、アニメーション名、ビルド出力、入力マッピング、ライフサイクル挙動、Android のビルド/signing の選択を明示的かつテスト可能にする。

**実装前に確認すること:**
- ウェブ出力ディレクトリ（`dist` または `www`）は何か、Capacitor の `webDir` と一致しているか?
- `public/` 配下の GLB/JSON は `https://localhost` 上で動く絶対 URL（`/assets/...`）で読み込まれているか?
- アニメーション名はハードコードされた文字列ではなくデータ（`assets_index.json`）から読み込まれているか? イベントハンドラにクリップ名文字列を埋め込んでいないか?
- JDK は使用している Capacitor バージョンと一致しているか（Android Studio には互換 JDK が同梱されている。手動で設定する場合は Capacitor の環境セットアップドキュメントに従うこと — 例: Capacitor 8 → JDK 17+）、また `ANDROID_HOME`/SDK は設定済みか?
- WSL2/Linux でビルドし Windows のエミュレータを使う構成か? その場合は Windows `adb.exe` と明示的なパス変換が必要。
- デスクトップとタッチのコントロールは意図的にマッピングされているか、それとも製品 UX に合わない可能性のあるデフォルトに任せているか?

**コア原則:**
1. コントラクトファーストのデータフロー: UI とアニメーション再生はコード内のアドホックなクリップ名ではなく JSON メタデータから導出すること。
2. ツールチェーンファーストの Android セットアップ: アプリロジックのデバッグを始める前に Android Studio + SDK + Gradle JDK + `adb` を揃えること。
3. 対称コントロール: デスクトップとモバイルの動作が一致するよう、マウスとタッチのマッピングを一緒に定義すること。
4. ビルド・sync の規律: ネイティブの実行はすべて最新のウェブアセットと sync に依存する。
5. 高速診断: 深いデバッグに入る前に、パス・クリップ名・アクション解決・WebGL 失敗に対する小さなランタイムチェックを優先すること。

## クイックスタートワークフロー

1. `package.json`、`vite.config.*`、`capacitor.config.*`、`public/assets/**` を確認する。
2. Vite で Three.js アプリをビルドする（通常 `npm run build`）。
3. 静的アセットは `public/` 以下に置き、絶対 URL（`/assets/...`）で読み込む。
4. Capacitor の `webDir` を出力に合わせる（通常 `"dist"`）。
5. Android がなければ追加する（`npm install @capacitor/android` → `npx cap add android`）。
6. 決定論的なループを繰り返す:
   - `npm run build`
   - `npx cap sync android`
   - `npx cap run android` または `npx cap open android`

コマンドレベルの詳細は `references/capacitor-android-workflow.md` を参照。

**WSL2 プロジェクト + Windows エミュレータの場合**、まずどちらのパスが速いかを決める:
- WSL でビルドした APK を Windows `adb.exe` でインストールする: 既存のウェブ/ネイティブ出力をスモークテストするのに最適。
- Android プロジェクトを Windows の Android Studio で開く: ネイティブの Gradle/manifest/plugin コードを編集する場合や Studio のツールを使う場合に最適。

ユーザーのゴールが Android アプリのスモークテストのときに、不安定な WSL2 エミュレータ GUI のデバッグへデフォルトで突入しないこと。代わりに Windows のエミュレータ/デバイスホストを使う。手順は `references/windows-wsl-emulator-workflow.md`。

## 参照ファイル

| トピック | ファイル | 使う場面 |
| --- | --- | --- |
| Android ワークフロー | [references/capacitor-android-workflow.md](references/capacitor-android-workflow.md) | セットアップ、build/sync/run、エミュレータ/実機、ライブリロード、signing |
| WSL2 + Windows エミュレータ | [references/windows-wsl-emulator-workflow.md](references/windows-wsl-emulator-workflow.md) | WSL2/Linux プロジェクト、Windows の Android Studio/エミュレータ、WSL からのエミュレータ操作 |
| アニメーションコントラクト | [references/threejs-animation-index-pattern.md](references/threejs-animation-index-pattern.md) | GLTF/GLB アニメーション UI、クリップ解決、メタデータ駆動アクション |
| Gotchas | [references/gotchas.md](references/gotchas.md) | ブラウザでは動くが Android で失敗、Gradle/JDK/SDK、タッチ/WebGL/バックボタン |

## 実装ガイドライン

### 1) プロジェクト構成

曖昧さを最小化するために、次の構成を推奨する:
- アプリコードは `index.html` と `src/*`
- GLB、テクスチャ、JSON コントラクトは `public/assets/...`
- `capacitor.config.ts` に `webDir: "dist"`

Vite を使用する場合、すべてのランタイム fetch をブラウザと Android System WebView（Chromium）の両方に互換させること:
- 推奨: `fetch('/assets/assets_index.json')`
- 非推奨: ファイルシステムパス、`file://` 前提、環境依存のホスト名（ライブリロードを意図的に設定している場合を除く）。

スキームに関する注意: Android はデフォルトで `server.androidScheme` を通じて `https://localhost` からバンドル済みウェブアセットを配信する。絶対パスの `/assets/...` URL はこのオリジン下で正しく解決される。具体的なルーティング上の理由なしに `androidScheme` を `https`/`http` 以外に変えないこと。

### 2) `assets_index.json` によるアニメーションコントラクト

単一の信頼できるデータソースを使用する:
- キャラクタースケルトン URL
- アニメーションソース URL
- 以下を含む `animations[]` エントリ:
  - 安定したアプリ ID（`idle`、`walk`、`run`）
  - `sourceClipName`（`AnimationClip.name` と完全一致）
  - ループモードとトランジションのデフォルト値

ランタイムのパターン:
1. インデックス JSON を読み込む
2. スケルトン GLB とアニメーション GLB を読み込む
3. 各 UI ボタンを `sourceClipName` でクリップに対応付ける
4. アプリ ID をキーとする `AnimationAction` マップを構築する
5. インデックスのデフォルトアクションを再生する

`references/threejs-animation-index-pattern.md` を参照。

### 3) コントロール: デスクトップとタッチ

`OrbitControls` を使用し、マッピングを明示的に設定する:
- マウス:
  - 左 = 回転
  - ホイール = ドリー/ズーム
  - 右 = パン
- タッチ:
  - 1本指 = 回転
  - 2本指 = ドリー + パン

WebView がドラッグジェスチャーをページスクロール/ズームとして横取りしないよう、`canvas.style.touchAction = 'none'` を設定する。
製品が垂直方向のみのパンなどの制約付き移動を要求する場合は、毎フレーム `controls.update()` の後にカメラの移動量を制限する。
この制約を追加する際に rotate/zoom のセマンティクスを無言で変更しないこと。

Android の**ハードウェアバックボタン**は、閉じるべきアプリ内状態・pop すべきルートスタック・リセットすべきカメラモードがある場合に `@capacitor/app` で処理すること（`App.addListener('backButton', ...)`）。デフォルトの終了挙動をそのまま使ってよいのは、それが明示的な製品判断である場合だけ。

### 4) パフォーマンスと安定性のガードレール

- ピクセル比を制限する: `Math.min(window.devicePixelRatio, 2)`（多くの Android 画面は 3x〜4x）。
- mixer/actions/materials を再利用し、クリックごとに再生成しないこと。
- リサイズ時は常にカメラのアスペクト、プロジェクション、レンダラーサイズを更新する。
- アニメーションの切り替えはメタデータのデフォルトのフェードトランジションで行う。
- `webglcontextlost`/`webglcontextrestored` を処理する — Android はメモリ圧迫時やバックグラウンド移行時に GL コンテキストを積極的に破棄する。
- `@capacitor/app` の `pause` でレンダリングループを一時停止し、`resume` で意図的に再開する。
- シーン置換やビュー離脱時は geometry、materials、textures、controls、renderer を dispose する。

### 5) Capacitor Android インテグレーション

プロジェクトの major version に対応する公式 Capacitor ドキュメントを真実の源とする。現行の Capacitor 8 系では概ね Node 22+、Android Studio + Android SDK、API 24+ サポート、そして多くのローカル構成では別管理の JDK ではなく Android Studio 同梱の Gradle JDK。

ツールチェーンの要件:
- **Capacitor バージョンに対応した JDK** — 通常は別途インストール不要で、Android Studio に互換 JDK が同梱されている。`JAVA_HOME` を手動で設定する場合は Capacitor の環境セットアップドキュメントに従うこと（例: Capacitor 8 → JDK 17+）。
- **Android SDK + platform-tools**（`ANDROID_HOME` を設定し、`adb` を PATH に追加）。
- **Android Studio**（または CLI Gradle）— Windows、Linux（WSL2 含む）、macOS で動作。Mac は不要。

確認: `node --version` / `npx cap doctor` / `adb devices` / Android Studio の Gradle sync。

ネイティブ設定・プラグイン・ウェブアセットの変更後は `npx cap sync android` を再実行すること。ライブリロードは開発専用。`server.url` を使う場合は到達可能な LAN/エミュレータホストを指定し、必要なときだけ `server.cleartext: true` を設定する。リリースビルドの前には `server.url` を消すこと。リリースビルドには独自のキーストアが必要（デバッグビルドは自動署名される）。詳細はワークフローリファレンスを参照。

## 避けるべきアンチパターン

❌ **UI ハンドラにクリップ名をハードコードする**
問題: GLB でクリップ名が変更されると、ボタンが静かに壊れる。
改善策: `assets_index.json` からボタンをマッピングし、起動時に一度だけクリップ名を解決する。

❌ **Android をブラウザ専用のバグとして扱う**
問題: Android には WebView オリジン、ライフサイクル、メモリ、入力挙動があり、デスクトップ Chrome では露出しない。
改善策: バンドルされたアセットパス、タッチ挙動、コンテキストロス処理、WebView コンソールログをエミュレータまたは実機で確認する。

❌ **不一致な JDK / 未設定の SDK / 古い Gradle 状態**
問題: Gradle が "unsupported class file" / "SDK location not found" などの不可解なエラーで失敗する。
改善策: Android Studio に同梱されている Gradle JDK（または Capacitor ドキュメントが指定するバージョン）を使用し、`ANDROID_HOME`/`local.properties` を設定し、`npx cap doctor` を実行してから Gradle sync / clean する。

❌ **ウェブアセットを再ビルドせずに Android を実行する**
問題: デバイス/エミュレーターに古い JS/CSS が表示され、デバッグが誤解を招く。
改善策: `cap sync`/`cap run` の前に必ずビルドを行うスクリプトを使用する。

❌ **WSL2 で ADB ホストを混在させる**
問題: Linux `adb` と Windows `adb.exe` が別サーバーと通信し、デバイスが missing/offline/不整合に見える。
改善策: デバイスホストを先に1つ選ぶ。Windows がエミュレータを所有する場合は WSL から Windows `adb.exe` を実行し、APK パスは `wslpath -w` で変換する。

❌ **コントロールマッピングを暗黙的なままにする**
問題: デスクトップとモバイルの操作が UX 要件から乖離し、WebView がタッチジェスチャーを横取りする。
改善策: `mouseButtons`/`touches` を明示的に設定し、canvas に `touch-action: none` を指定する。

❌ **開発用 `server.url` を出荷する**
問題: `server.url` はアプリを開発マシンやリモートのウェブバンドルに向け、リリースのセキュリティ/パフォーマンス挙動を変える。
改善策: 意図的なライブ更新アーキテクチャがない限り、本番では `server.url` を削除してビルド済みアセットを出荷する。

❌ **ウェブコントラクトのエラーをネイティブから先にデバッグする**
問題: 問題の多くは JSON キーの欠落・不正なパス・未解決のクリップにあるにもかかわらず、Android Studio で時間を無駄にする。
改善策: インデックスの構造とクリップ解決に関する起動時のアサーション/ログを追加し、`chrome://inspect` で WebView のエラーを確認する。

## バリエーションガイダンス

**重要**: デフォルトで同一のビューワーを生成しないこと。
製品の意図に合わせて実装を調整する:
- キャラクターショーケース: 豊かなライティング、ゆっくりしたカメラダンピング、洗練されたアイドルループを重視。
- ゲームプレイプロトタイプ: 高速トランジション、状態駆動のアニメーション切り替え、最小限の UI。
- アセット QA ツール: 診断オーバーレイ、クリップの長さ/トラック情報、欠落クリップの警告を明確に表示。
- プロダクトコンフィギュレータ: 制約付きカメラ、タッチフレンドリーなホットスポット、アセットのプリロードと進捗表示。

少なくとも以下のディメンションを意図的に変化させること:
- ビジュアルスタイル（ライティング/背景/床の処理）
- 入力チューニング（ダンピング/ズーム/パン速度、カメラ制約）
- アニメーション UX（ボタン、キーボードショートカット、自動再生戦略）
- 診断の可視性とエラー表面

文脈がより多くを要求しているにもかかわらず、汎用的な「orbit + 3ボタン」の出力に収束しないようにする。

## まとめ

Three.js + Capacitor Android は、コントラクトが明示的でワークフローが規律正しい場合に成功する。
明確なメタデータコントラクトを構築し、コントロールを意図的にマッピングし、Android ツールチェーンとモバイル WebView ライフサイクルを揃え、build/sync/run を決定論的に保つこと。
