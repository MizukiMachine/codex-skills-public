---
name: diagram
description: "コードベース解析から、日本語メイン・英語補助のMermaid図を生成・更新する。アーキテクチャ図、構成図、シーケンス図、ER図、状態図、データフロー図、依存関係図、デプロイ図を求められたときに使う。図ラベル・選定理由・README・最終報告は必ず日本語を先に書き、英語は補助として併記する。"
---

# アーキテクチャ図生成

## 目的

リポジトリ内の実ファイルを根拠に、実態に合う Mermaid 図を作る。目的は「見栄えのよい一般図」ではなく、初見の開発者が構造・境界・主要フローを短時間で理解できる図を残すこと。

## 動作モデル

優先順位:

1. 正確性: repoに存在しないコンポーネント、DB、サービス、処理を描かない
2. 有用性: 浅い図を大量に作らず、読む価値のある少数の図を選ぶ
3. 日本語メイン: 人間が読む文言は日本語を先にし、英語は補助にする
4. 再生成性: Mermaid source、PNG、README indexを残し、レンダリング手順を明示する

判断の基本:

- AppやAPIの実行境界、データ所有、認証境界、外部依存、永続化、非同期処理、主要ユーザーフローを優先して描く
- 迷ったら大きな包括図1枚より、境界が明確な component / runtime flow / ER / deployment のいずれかを選ぶ
- ER図は実スキーマまたはモデル定義がある場合だけ作る。型定義やDTOだけならER図は省略する
- Deployment図はDocker、Kubernetes、Terraform、CI/CD、hosting設定などの根拠がある場合だけ作る

## 成果物

- `diagrams/*.mmd`: 図ごとの Mermaid source
- `diagrams/*.png`: 可能な場合にレンダリングした画像
- `diagrams/README.md`: 図のindex、選定理由、選ばなかった図、根拠ファイル
- 最終報告: 生成・更新したファイル、検証結果、未実施の作業

## 言語コントラクト

このスキルの出力は **日本語メイン** とする。人間が読む文言を英語だけで終わらせない。

- 図ラベル、subgraph名、edgeラベル、sequence participant/message、README、最終報告は必ず日本語を先に書く
- 英語は補助として併記する。基本形は `日本語 / English`、狭いノードでは `日本語<br/>English`
- コード識別子、ファイルパス、関数名、クラス名、API route、HTTP method、正式な製品名は原文のままでよい。ただし、その周囲に日本語の説明語を添える
- `[User]`、`[API]`、`[DB]` などのタグを使う場合も、日本語ラベルを同じノード内に置く
- READMEの見出し・表の列名・選定理由も日本語を先にする
- 英語のみの汎用ラベルは禁止。例: `Browser runtime` ではなく `ブラウザ実行環境 / Browser runtime`

## 開始前に確認すること

- 既存の `diagrams/` があれば、上書き前に内容と命名規則を読む
- `package.json`、`Cargo.toml`、`go.mod`、`pyproject.toml`、`tsconfig.json`、framework設定、Docker/Kubernetes/CI、OpenAPI、route、model/schema、job/queue、entry pointを確認する
- `rg --files` と `rg` で構造を集める。通常の探索に `find` や `ls -R` は使わない
- ユーザーが図種別を指定している場合でも、根拠が足りない図は理由を説明して省略または別図に置き換える

## 参照ファイル

| トピック / Topic | ファイル / File | 使用タイミング / Use When |
|---|---|---|
| Mermaid構文テンプレート / Mermaid syntax templates | `references/mermaid-patterns.md` | 図種別ごとの構文、色、レイアウト例が必要なとき |
| PNGレンダリング / PNG rendering | `scripts/render_diagrams.py` | `.mmd` をまとめて `.png` に変換するとき |

## ワークフロー

### 1. 構造を発見する

- repoファイルを唯一の情報源として扱う
- manifest、framework設定、route、handler、server action、controller、model、schema、migration、job、queue、外部API client、auth設定、deployment設定を読む
- ディレクトリ境界、import、route、コマンド、データモデル、インフラを突き合わせる
- ファイル数、主要ディレクトリ、route数、model/schema数、外部依存を軽く数える

### 2. プロジェクトを分類する

- 種類 / Type: backend API、full-stack app、microservices、CLI/library、desktop app、mobile app、infrastructure/tooling、mixed
- 規模 / Size: ファイル数、モジュール数、route、model、command、依存関係から見積もる
- 主要モジュール / Main modules: ディレクトリ境界、import、route、service、データ所有から導く
- リスク境界 / Risk boundaries: 認証、外部API、DB、queue、SSE/WebSocket、batch、deploymentなど

### 3. 図の選択基準を説明する

ユーザーに見せる説明は必ず日本語先頭で書く。

```markdown
## 図の選択基準 / Diagram Selection

**プロジェクト分析結果 / Project Analysis**
- タイプ / Type: ...
- サイズ / Size: ...
- 主要モジュール / Main Modules: ...
- 重要な境界 / Important Boundaries: ...

**選択した図 / Selected Diagrams**
| 図 / Diagram | 選択理由 / Reason |
|---|---|
| ... | ... |

**選ばなかった図 / Not Selected**
| 図 / Diagram | 理由 / Reason |
|---|---|
| ... | ... |
```

### 4. 図を選ぶ

| プロジェクト種別 / Project Type | 優先する図 / Prioritize | 作らない判断 / Skip When |
|---|---|---|
| Backend API | system context、container、component、sequence、ER、deployment | DB schemaやdeployment設定がない場合はER/deploymentを省略 |
| Full-stack | system context、container、component、data flow、sequence、ER、deployment | frontendだけで永続化定義がない場合はERを省略 |
| Microservices | container、component、data flow、sequence、deployment、dependency | service境界や通信が確認できない場合は推定と明記 |
| CLI/Library | component、dependency、data flow、sequence | user-facing runtimeが薄い場合はsystem contextを省略 |
| Desktop/Mobile | system context、component、data flow、state | 状態遷移が明示されていない場合はstateを省略 |
| Infrastructure/tooling | deployment、dependency、data flow | app codeがない場合はcomponentを浅くしすぎない |

### 5. Mermaid sourceを作る

- 出力先は既定で `diagrams/`
- 図ごとに1つの `.mmd` ファイルを作る
- ファイル名は `component-architecture.mmd`、`authenticated-runtime-flow.mmd` のような kebab-case にする
- Mermaid node id は ASCII で安定させる
- 人間向けラベルは必ず「日本語先頭 + 英語補助」にする
- 実際のモジュール、関数、クラス、route、table、service名を使う
- 論理境界は `subgraph` で表す
- emoji は使わない。代わりに `[CLI]`、`[API]`、`[DB]`、`[User]`、`[Service]` などのタグを使う
- 読みやすいパステル色と文字色を使う
- 構文に迷う場合だけ `references/mermaid-patterns.md` を読む

### 6. README indexを作る

`diagrams/README.md` は生成図のindexとしてだけ使う。

- 図の選択基準 / Diagram Selection
- プロジェクト分析結果 / Project Analysis
- 選択した図 / Selected Diagrams
- 選ばなかった図 / Not Selected
- 生成ファイル / Files
- レンダリング手順 / Render

### 7. セルフレビューする

- `.mmd` と `diagrams/README.md` を読み返し、英語だけの人間向けラベルが残っていないか確認する
- 英語のみが許されるのは、コード識別子・ファイルパス・HTTP method・公式名などの固有表記だけ
- 図の選定理由と「選ばなかった図」の理由が日本語先頭で書かれていることを確認する
- 存在しないコンポーネント、推測だけのDB、未確認の外部サービスを描いていないことを確認する
- Mermaid構文としてレンダリング可能か確認する

### 8. 可能ならPNGをレンダリングする

```bash
python3 /path/to/diagram/scripts/render_diagrams.py diagrams --scale 4
```

スキルディレクトリから実行する場合:

```bash
python3 scripts/render_diagrams.py <output_dir> --scale 4
```

`python` がない場合は `python3` を使う。`mmdc` がない場合やレンダリングに失敗した場合は、`.mmd` を残し、PNG未生成の理由を報告する。

## アンチパターン

- **英語だけの図ラベル**: ユーザーの期待から外れる。日本語を先に置き、英語は補助にする
- **READMEだけ英語**: indexも成果物なので、日本語先頭の表記にする
- **存在しないDBやサービスの追加**: repo根拠がない場合は描かない。必要なら `推定 / inferred` と明記する
- **浅い図を大量生成**: 価値の薄い図を増やさず、実態を説明する少数の図に絞る
- **routeやhandler未確認のsequence**: sequence/data-flowは実際のroute、handler、command、job、処理トレースで照合する
- **正式名だけのノード**: `NextAuth` のような正式名だけで役割が伝わりにくい場合、`認証Route / NextAuth route` のように役割を添える
- **既存diagramの無確認上書き**: 既存の図がある場合は、意図と命名を読んでから更新する

## 検証

- スキル自体を更新した場合:

  ```bash
  python3 /home/mizuki2/.codex/skills/skill-builder/scripts/quick_validate.py /home/mizuki2/.codex/skills/diagram
  ```

- 図を生成した場合:

  ```bash
  python3 /home/mizuki2/.codex/skills/diagram/scripts/render_diagrams.py diagrams --scale 4
  ```

- 言語チェックでは、少なくとも以下を確認する:
  - subgraph名、node label、sequence participant/messageが日本語先頭
  - READMEの見出し・表列名・理由文が日本語先頭
  - `Browser runtime`、`External Systems`、`Client<br/>` のような英語先頭テンプレート残りがない

## 最終報告

最終報告は短く、以下を日本語で伝える。

- 生成・更新したファイル
- レンダリングや検証の結果
- 省略した図がある場合はその理由
- 未実施の検証がある場合はその理由
