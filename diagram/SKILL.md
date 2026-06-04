---
name: diagram
description: "コードベース解析からMermaidの図を作る。アーキテクチャ図、構成図、シーケンス図、ER図、状態図、データフロー図を求められたときに使う。"
---

# アーキテクチャ図生成

リポジトリ分析に基づいて、正確な Mermaid 図を作る。実際のファイル、manifest、ルート、モデル、依存関係、設定、実行エントリポイントを根拠にする。

## ワークフロー

1. 構造を集める。
   - ワークスペースを直接読み、リポジトリファイルを唯一の情報源として扱う
   - `package.json`、`Cargo.toml`、`go.mod`、`pyproject.toml`、`tsconfig.json`、フレームワーク設定、Docker/Kubernetes、OpenAPI、ルート、モデル、スキーマを読む
   - ディレクトリ境界、import、ルート、コマンド、ジョブ、データモデル、インフラを突き合わせる

2. 描く前にプロジェクトを分類する。
   - 種類: backend API、full-stack app、microservices、CLI/library、desktop app、mobile app、infrastructure/tooling、mixed
   - 規模: ファイル数、モジュール数、ルート、モデル、コマンド、依存関係から見積もる
   - 主要モジュール: ディレクトリ境界、import、ルート、サービス、データ所有から導く

3. 図の選択基準をユーザーへ説明する。

   ```markdown
   ## 図の選択基準

   **プロジェクト分析結果:**
   - タイプ: ...
   - サイズ: ...
   - 主要モジュール: ...

   **選択した図:**
   | 図 | 選択理由 |
   |---|---|
   | ... | ... |

   **選ばなかった図:**
   | 図 | 理由 |
   |---|---|
   | ... | ... |
   ```

4. 適合する図を選ぶ。

   | プロジェクト種別 | 推奨図 |
   |---|---|
   | Backend API | System Context, Container, Component, Sequence, ER, Deployment |
   | Full-stack | System Context, Container, Component, Data Flow, Sequence, ER, Deployment |
   | Microservices | Container, Component, Data Flow, Sequence, Deployment, Dependency |
   | CLI/Library | Component, Dependency, Data Flow, Sequence |
   | Desktop/Mobile | System Context, Component, Data Flow, State |
   | Infrastructure/tooling | Deployment, Dependency, Data Flow |

5. Mermaid ファイルを生成する。
   - 既定の出力先はワークスペース内の `diagrams/`
   - 図ごとに1つの `.mmd` ファイルを作る
   - 必要なら日本語 / English の併記ラベルにする
   - 実際のモジュール、関数、クラス、ルート、テーブル、サービス名を使う
   - 論理境界は subgraph で表す
   - emoji は使わず、`[CLI]`、`[API]`、`[DB]`、`[User]`、`[Service]` のようなタグを使う
   - Mermaid の node id は ASCII で安定させる
   - 読みやすいパステル色と文字色を使う
   - 構文テンプレートが必要なら `references/mermaid-patterns.md` を読む

6. 可能なら PNG をレンダリングする。

   ```bash
   python scripts/render_diagrams.py <output_dir> --scale 4
   ```

   スクリプトはこのスキルディレクトリから実行するか、明示パスで使う。`@mermaid-js/mermaid-cli` の `mmdc` が必要。使えない場合は `.mmd` を残し、PNG は未生成と報告する。

7. 生成物の index を作る。
   - `diagrams/README.md` は生成図の index としてのみ追加する
   - 各図のファイル名、何を示すか、どのソース根拠に基づくかを書く

## 正確性ルール

- 見栄えのために存在しないコンポーネントを作らない
- 不確かな部分は図ラベルまたは説明で inferred と明示する
- 浅い図を大量に作るより、少数の正確な図を優先する
- sequence と data-flow は実際の route、handler、command、job、処理トレースで照合する
- ER 図は実スキーマまたはモデル定義に基づける。永続データモデルがない場合は省略し、理由を説明する

## リソース

- `scripts/render_diagrams.py`: Mermaid CLI で `.mmd` を PNG にまとめてレンダリングする
- `references/mermaid-patterns.md`: C4、layered、component、data-flow、sequence、ER、state、deployment、dependency のテンプレート
