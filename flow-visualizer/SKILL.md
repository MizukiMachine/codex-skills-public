---
name: flow-visualizer
description: "システムやコードパスの流れをASCIIフロー図で説明する。仕組み、全体像、処理フロー、実行経路を知りたい依頼で使う。"
---

# Flow Visualizer

システムを縦方向の ASCII フローで説明する。処理ステップ、コード上の根拠、コマンド、ファイル、関数、終了コード、短い自然言語説明を含める。

## 出力スタイル

既定では次の形を使う。

```text
  Input or trigger
        |
        v
  +--------------------------------------------------------------+
  | Step 1: Process name                                         |
  | What happens, with file/function/command details.             |
  +--------------------------------------------------------------+
        |
        v
  +--------------------------------------------------------------+
  | Step 2: Process name                                         |
  | +----------------------------------------------------------+ |
  | | Sub-flow                                                  | |
  | | - Important internal operation                            | |
  | | - Programming-layer anchor                                | |
  | +----------------------------------------------------------+ |
  +--------------------------------------------------------------+
        |
        v
  Final output or observable result
```

ユーザーが Unicode 罫線を明示しない限り、箱と矢印には ASCII 文字を使う。

## 説明ルール

- ファイルパス、関数、クラス、コマンド、終了コード、環境変数、ルート、DB テーブル、キュー、ジョブ、設定ファイルなど、プログラム層の根拠を入れる
- 抽象度は処理単位に保つ。ユーザーが求めない限り、行単位の説明にしない
- 各ステップが何を達成し、なぜ存在するかを書く
- ステップ内部に意味のある処理がある場合は nested box を使う
- 各ステップは通常1-3行に収める
- リポジトリについて聞かれた場合は、関連ファイルを読んでから図を書く
- 推測した部分は inferred と明示する

## リポジトリでの進め方

1. エントリポイントを特定する: コマンド、ルート、handler、UI action、job、test runner、public API
2. `rg`、manifest、import、route 定義、config で次の呼び出しを追う
3. 主要パスを先に押さえ、validation failure、retry、error handling など重要な分岐を追加する
4. ASCII フローを出す
5. 仮定、省略した分岐、根拠ファイルの説明が必要なときだけ、図の後に短いメモを添える

## 例

```text
$ go test ./...
      |
      v
+--------------------------------------------------------------+
| 1. Discover packages and test files                           |
| `go` walks packages and finds `*_test.go` files.              |
+--------------------------------------------------------------+
      |
      v
+--------------------------------------------------------------+
| 2. Compile a temporary test binary                            |
| Test functions, package code, and generated test main compile.|
+--------------------------------------------------------------+
      |
      v
+--------------------------------------------------------------+
| 3. Execute tests and collect status                            |
| PASS exits 0. Failing tests return non-zero with diagnostics.  |
+--------------------------------------------------------------+
      |
      v
Result printed to stdout/stderr
```
