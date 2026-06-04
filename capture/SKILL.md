---
name: capture
description: "セッションの要約や学びを標準ディレクトリへ保存する。ユーザーにsave/capture/logや作業記録を頼まれたときに使う。"
---

# Capture

現在のセッションで生まれた会話上の成果物、つまりプロンプト、計画、学びを標準ディレクトリへ保存する。ワークフロー全体が後から追えるように、関連ファイル同士を必ず相互リンクする。

## 考え方

意味のあるセッションからは、主に3種類の記録が生まれる。

1. **Prompts**: ユーザーの意図、好み、確認事項、実際に使ったモデルプロンプトや呼び出し
2. **Plans**: ゴール、手順、検証方法など、決めた進め方
3. **Learnings**: 結果、意外だった点、品質メモ、次回に向けた判断

3つのファイルは、単なる一時的な会話ログではなく、整えられた作業記録として扱う。存在する兄弟ファイルには必ずリンクする。

## 保存するタイミング

- 計画フェーズで具体的な計画ができた後
- タスクが完了し、記録すべき結果があるとき
- ユーザーが保存、capture、log、作業記録を明示的に頼んだとき
- プロンプト、判断、学びが失われそうな自然な節目

毎回3ファイルすべてが必要とは限らない。

- 計画だけのセッション: prompts + plan
- 短い実験: prompts + learnings
- 一連の作業: prompts + plan + learnings

## ファイル名

すべてのファイルは同じタイムスタンプと slug を共有する。

```text
YYYY-MM-DD-HHMMSS-<slug>
```

- タイムスタンプはセッション開始時刻、または主要なユーザー依頼の時刻を使う
- slug は短く、ハイフン区切りで内容がわかるものにする
- ユーザーが `/capture <slug>` のように指定した場合はそれを使う
- 指定がない場合は会話の主題から作る

## 出力先

```text
prompts/<timestamp>-<slug>-prompts.md
plans/<timestamp>-<slug>-plan.md
learnings/<timestamp>-<slug>-learnings.md
```

## Prompts テンプレート

```markdown
# <Title> Prompts

Linked plan file: `plans/<timestamp>-<slug>-plan.md`
Linked learnings file: `learnings/<timestamp>-<slug>-learnings.md`

## User Verbatim

Author: `User`

Exact user message(s):

\```text
<ユーザーの正確な発言を、誤字や書式も含めて貼る>
\```

## User Preferences

Author: `User`

Preferences captured during the session:

\```text
<ユーザーが示した好み、制約、確認事項>
\```

## Assistant Summary

\```text
<アシスタントが理解した意図と範囲の簡潔な要約>
\```

## Docs Studied

Author: `Assistant`

\```text
<セッション中に読んだ URL やドキュメント。なければ省略>
\```

## Working Findings

Author: `Assistant`

\```text
<計画や実行中に見つけた重要な調査結果や技術メモ>
\```

## Model Prompts Used

### <Model Name> Prompt Sent

\```text
<送信した正確なプロンプト>
\```

### <Model Name> Exact Invocation

\```bash
<正確なコマンドまたは API 呼び出し>
\```

### Outcome

\```text
<結果、失敗、品質メモなど>
\```
```

該当しないセクションは省略する。ただし `User Verbatim` は必須。

## Plan テンプレート

```markdown
# <Title> Plan

Linked prompts file: `prompts/<timestamp>-<slug>-prompts.md`
Linked learnings file: `learnings/<timestamp>-<slug>-learnings.md`

## Goal

<ゴールを1段落で書く>

## Approach

<手順を番号付きで書く>

## Verification

<ビルド、視覚確認、テストなど、正しさの確認方法>
```

## Learnings テンプレート

```markdown
# <Title> Learnings

Related records:
- `plans/<timestamp>-<slug>-plan.md`
- `prompts/<timestamp>-<slug>-prompts.md`

## Context

<このセッションの背景>

## Initial Hypothesis

<当初の仮説。なければ省略>

## What Happened

<何が起きたか、何がうまくいったか、何がうまくいかなかったか>

## Result Quality

<成果物の品質評価。なければ省略>

## Decisions

<今回決めたこと、次回以降に残す判断>
```

`Context` と `What Happened` は必須。それ以外は必要なときだけ含める。

## 相互リンク

すべてのファイルは兄弟ファイルへリンクする。リンクはリポジトリルートからの相対パスで書く。

- prompts は plan と learnings へリンクする
- plan は prompts と learnings へリンクする
- learnings は plan と prompts へリンクする
- 2ファイルしか作らない場合は、存在する兄弟ファイルだけにリンクする

## 避けること

- **内容を捏造しない**: 実際に起きたことだけを記録する
- **ユーザー原文を要約しすぎない**: `User Verbatim` には正確な発言を貼る
- **別セッションを混ぜない**: 1つの capture は1タイムスタンプ、1 slug、1つのまとまった作業にする
- **相互リンクを省略しない**: リンクされた記録セットがこのスキルの要点
- **雑談的な往復をそのまま残さない**: 会話そのものではなく、判断と成果物を記録する
