---
name: threejs-capacitor-ios
description: "Vite と Swift Package Manager を使って、Capacitor iOS 上で Three.js アプリを構築・リリースする。GLTF読み込み、assets_index によるアニメーションUI、OrbitControls のマウス/タッチ対応、WKWebView ライフサイクル、iOS の sync/run/署名のトラブルシュートを扱う。"
metadata:
  short-description: "Three.js + Capacitor iOS ワークフロー"
---

# Three.js Capacitor iOS

ブラウザで動作し、Capacitor 経由で iOS ネイティブシェルに内包できるインタラクティブな Three.js アプリを構築・リリースするスキル。
ウェブビルド出力、アニメーションコントラクト、コントロール、WKWebView ライフサイクル、SPM/Xcode、ネイティブの sync/run/signing ワークフローなど、障害が最も発生しやすい統合境界に焦点を当てる。

Android ターゲットには `threejs-capacitor-android` スキルを使用する。ウェブ/Three.js レイヤーは両者でほぼ同一であり、異なるのはネイティブシェル・ライフサイクル・パッケージマネージャー・ストアビルドのワークフロー（SPM/Xcode vs Gradle/Android Studio）のみ。

## 哲学: 2つのランタイム、1つのコントラクト

プロジェクトを合意が必要な2つのシステムとして扱う:
- ウェブレンダラーランタイム（Three.js + Vite + ブラウザ API）
- ネイティブランタイムラッパー（Capacitor iOS + WKWebView + Xcode/SPM）

コントラクトが暗黙的な場合にほとんどの障害が発生する。
ファイルパス、アニメーション名、ビルド出力、入力マッピング、ライフサイクル挙動、iOS パッケージマネージャーと signing の選択を明示的かつテスト可能にすること。

**実装前に確認すること:**
- ウェブの出力ディレクトリ（`dist` または `www`）は何か、Capacitor の `webDir` と一致しているか?
- `public/` 配下の GLB/JSON は iOS WebView オリジンで動く絶対 URL（`/assets/...`）で読み込まれているか?
- アニメーション名はハードコードされた文字列ではなく、データ（`assets_index.json`）から読み込んでいるか?
- macOS、Node、Xcode、Command Line Tools は Capacitor の major version と一致しているか?
- iOS は SPM と CocoaPods のどちらを使っており、プラグインの依存関係はその選択と互換性があるか?
- デスクトップとタッチのコントロールは意図的にマッピングされているか、それともプロダクト UX と一致しないデフォルトのままか?

**コア原則:**
1. コントラクトファーストのデータフロー: UI とアニメーション再生は JSON メタデータから導出し、コード内のアドホックなクリップ名には依存しない。
2. SPM-first な iOS セットアップ: 特定のプラグインが CocoaPods を強制する場合を除き、モダンな Capacitor では Swift Package Manager をデフォルトとする。
3. 対称コントロール: マウスとタッチのマッピングを一緒に定義し、デスクトップとモバイルの動作を揃える。
4. ビルド・sync の規律: すべてのネイティブ実行は最新のウェブアセットと sync に依存する。
5. 高速診断: 深いデバッグの前に、パス・クリップ名・アクション解決・WebGL 失敗に対する小さなランタイムチェックを優先する。

## クイックスタートワークフロー

1. `package.json`、`vite.config.*`、`capacitor.config.*`、`public/assets/**`、既存の `ios/` を確認する。
2. Vite で Three.js アプリをビルドする（通常 `npm run build`）。
3. 静的アセットは `public/` 以下に置き、絶対 URL（`/assets/...`）で読み込む。
4. Capacitor の `webDir` を出力に合わせる（通常 `"dist"`）。
5. iOS がなければ追加する（`npm install @capacitor/ios` → `npx cap add ios --packagemanager SPM`）。
6. 決定論的なループを繰り返す:
   - `npm run build`
   - `npx cap sync ios`
   - `npx cap run ios` または `npx cap open ios`

可能なら build/sync を飛ばせないスクリプトを追加する。コマンドレベルの詳細は `references/capacitor-ios-spm-workflow.md` を参照。

## 参照ファイル

| トピック | ファイル | 使う場面 |
| --- | --- | --- |
| iOS ワークフロー | [references/capacitor-ios-spm-workflow.md](references/capacitor-ios-spm-workflow.md) | セットアップ、build/sync/run、シミュレータ/実機、SPM 移行、signing |
| アニメーションコントラクト | [references/threejs-animation-index-pattern.md](references/threejs-animation-index-pattern.md) | GLTF/GLB アニメーション UI、クリップ解決、メタデータ駆動アクション |
| Gotchas | [references/gotchas.md](references/gotchas.md) | ブラウザでは動くが iOS で失敗、SPM/CocoaPods、WKWebView/タッチ/WebGL |

## 実装ガイドライン

### 1) プロジェクト構成

曖昧さを最小化するため、以下の構成を推奨:
- `index.html` と `src/*` にアプリコード
- `public/assets/...` に GLB、テクスチャ、JSON コントラクト
- `capacitor.config.ts` に `webDir: "dist"`
- `ios/App/` は Capacitor が生成したものを使用する

Vite を使う場合、すべてのランタイム fetch をブラウザと WKWebView の両方で動作するように保つこと:
- 推奨: `fetch('/assets/assets_index.json')`
- 非推奨: 意図的に設定していない限り、ファイルシステムパス、`file://` 前提、環境固有のベース URL。

iOS のバンドル済みアセットは WKWebView 内で配信される。ビルド出力にコピーされた `public/assets` には絶対パスの `/assets/...` が通常有効。

### 2) `assets_index.json` によるアニメーションコントラクト

単一の信頼できる情報源を使う:
- キャラクタースケルトンの URL
- アニメーションソースの URL
- 以下を含む `animations[]` エントリ:
  - 安定したアプリ id（`idle`・`walk`・`run`）
  - `sourceClipName`（`AnimationClip.name` の正確な値）
  - ループモードとトランジションのデフォルト値

ランタイムパターン:
1. インデックス JSON を読み込む
2. スケルトン GLB とアニメーション GLB を読み込む
3. 各 UI ボタンを `sourceClipName` でクリップに解決する
4. アプリ id をキーとした `AnimationAction` マップを構築する
5. インデックスのデフォルトアクションを再生する

`references/threejs-animation-index-pattern.md` を参照。

### 3) コントロールとセーフエリア

`OrbitControls` を使い、マッピングを明示的に設定する:
- マウス:
  - 左ボタン = 回転
  - ホイール = ドリー/ズーム
  - 右ボタン = パン
- タッチ:
  - 1本指 = 回転
  - 2本指 = ドリー + パン

WebView がジェスチャーをページスクロール/ズームとして横取りしないよう、`canvas.style.touchAction = 'none'` を設定する（アプリが意図的にドキュメントスクロールを混ぜる場合を除く）。
プロダクトが垂直方向のみのパンを必要とする場合、毎フレーム `controls.update()` の後に target/camera の移動を制限する。
この制限を追加するとき、rotate/zoom のセマンティクスを暗黙的に変更しないこと。

ノッチ、ホームインジケータ、角丸付近のオーバーレイには CSS の `env(safe-area-inset-*)` を使い、エッジのコントロールが切れたり隠れたりしないようにする。

### 4) パフォーマンスと安定性のガードレール

- ピクセル比を制限する: `Math.min(window.devicePixelRatio, 2)`。
- mixer/actions/materials は再利用し、クリックのたびに再生成しない。
- リサイズ/向きの変更時は必ず camera の aspect・projection・renderer のサイズを更新する。
- アニメーションの切り替えはメタデータのデフォルト値によるフェードトランジションで行う。
- `webglcontextlost`/`webglcontextrestored` を処理する — iOS はメモリ圧迫時に GL コンテキストを破棄することがある。
- `@capacitor/app` の `pause` でレンダリングループを一時停止し、`resume` で意図的に再開する。
- シーン置換やビュー離脱時は geometry、materials、textures、controls、renderer を dispose する。

### 5) Capacitor iOS インテグレーション

公式 Capacitor ドキュメントを真実の源とする。Capacitor 8 系では概ね Node 22+、macOS、Xcode 26+、Command Line Tools、iOS 15+、Swift Package Manager。

確認: `node --version` / `xcode-select -p` / `npx cap doctor` / Xcode のビルドとパッケージ解決。

Capacitor 8+ ではデフォルトで SPM を使う。既存の CocoaPods プロジェクトは意図的に移行すること（移行アシスタントまたは iOS プラットフォームの再作成）。生成された `CapApp-SPM` の内部を手で編集しないこと。

ネイティブ設定・プラグイン・ウェブアセットの変更後は `npx cap sync ios` を再実行する。ライブリロードは開発専用。リリース前に `server.url` を消すこと。リリースビルドには Apple Developer signing、bundle id、capabilities、archive/export の選択が必要。

## 避けるべきアンチパターン

❌ **UI ハンドラーにクリップ名をハードコードする**
問題: GLB 内のクリップをリネームするとボタンが静かに壊れる。
改善策: `assets_index.json` からボタンをマッピングし、起動時に一度だけクリップ名を解決する。

❌ **SPM と CocoaPods の前提を混在させる**
問題: 依存関係のずれと Xcode プロジェクトの期待値の破損。
改善策: プロジェクトごとにパッケージマネージャーを1つに決める。モダンなセットアップでは、プラグインが CocoaPods を強制しない限り SPM を優先。

❌ **ウェブアセットを再ビルドせずに iOS を実行する**
問題: シミュレーター/実機に古い JS/CSS が表示され、デバッグが誤った方向に進む。
改善策: `cap sync`/`cap run` の前に必ずビルドを行うスクリプトを使う。

❌ **iOS をデスクトップ Safari と同一視する**
問題: WKWebView はライフサイクル、メモリ圧迫、セーフエリア、リモートデバッグ挙動が異なる。
改善策: シミュレーターまたは実機でテストし、WebView を inspect し、pause/resume/コンテキストロスを処理する。

❌ **コントロールマッピングを暗黙的なままにする**
問題: デスクトップとモバイルの操作感が UX 要件から乖離し、iOS がジェスチャーをページ挙動と解釈する。
改善策: `mouseButtons` と `touches`、`touch-action: none` をコード内で明示的に設定する。

❌ **開発用 `server.url` を出荷する**
問題: `server.url` はアプリを開発マシンやリモートのウェブバンドルに向け、リリースのセキュリティ/パフォーマンス挙動を変える。
改善策: 意図的なライブ更新アーキテクチャがない限り、本番では `server.url` を削除してビルド済みアセットを出荷する。

❌ **ウェブコントラクトのエラーをネイティブから先にデバッグする**
問題: 問題の原因が通常は JSON キーの欠落・パスの誤り・未解決のクリップであるのに、Xcode で時間を無駄にする。
改善策: インデックスの構造とクリップ解決に対して起動時のアサーション/ログを追加する。

## バリエーションガイダンス

**重要**: デフォルトで同一の viewer を生成しないこと。
プロダクトの意図に合わせて実装を調整する:
- キャラクターショーケース: より豊かなライティング、遅いカメラダンピング、idle ループの強調。
- ゲームプレイプロトタイプ: 素早いトランジション、状態駆動のアニメーション切り替え、最小限の UI クローム。
- アセット QA ツール: 診断オーバーレイ、クリップ長/トラック情報、missing-clip 警告を明確に表示。
- プロダクトコンフィギュレータ: 制約付きカメラ、タッチフレンドリーなホットスポット、プリロード/進捗表示。

意図的に以下のディメンションを変化させる:
- ビジュアルスタイル（ライティング/背景/床の処理）
- 入力チューニング（ダンピング/ズーム/パン速度、カメラ制約）
- アニメーション UX（ボタン・キーボードショートカット・自動再生戦略）
- 診断の可視性とセーフエリアを考慮した配置

文脈がより多くを求めているときに、汎用的な「orbit + 3ボタン」の出力に収束することを避ける。

## まとめ

Three.js + Capacitor iOS は、コントラクトを明示的にし、ワークフローを規律立てることで成功する。
明確なメタデータコントラクトを構築し、コントロールを意図的にマッピングし、Xcode/SPM ツールチェーンとモバイル WKWebView ライフサイクルを揃え、build/sync/run を決定論的に保つこと。
