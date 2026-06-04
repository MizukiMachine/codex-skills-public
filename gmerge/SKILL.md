---
name: gmerge
description: "現在の作業ブランチをdevelopへ --no-ff でマージする。gm、$gm、ブランチのマージ、developへのマージを頼まれたときに使う。main/masterへの直接マージは止める。"
---

# Git Merge Skill

source branch を `develop` へ `--no-ff` で merge する。`main` / `master` への直接 merge は止め、push は行わない。

## ワークフロー

1. source branch を確認する。

   ```bash
   git branch --show-current
   git status --short
   ```

   working tree に未 commit 変更がある場合は止まり、commit/stash するかユーザーに確認する。無関係な未 commit 変更の上で merge を始めない。

2. 危険な source 状態を止める。
   - current branch が `main` または `master` の場合は、次のエラーで止まる

   ```text
   エラー: main/master からの直接マージ運用は禁止されています。release ブランチ等を経由してください。
   ```

   - current branch が `develop` の場合は、どの source branch を merge するか確認する

3. `develop` が存在するか確認する。

   ```bash
   git branch --list develop
   ```

   存在しない場合は current branch から作成する。

   ```bash
   git branch develop
   ```

   `develop` を作成したことをユーザーに伝える。

4. `develop` へ切り替える。

   ```bash
   git checkout develop
   ```

5. `--no-ff` で merge する。

   ```bash
   git merge --no-ff <source-branch> -m "merge: <source-branch> into develop"
   ```

   ユーザーが merge message を指定した場合はそれを使う。

6. 検証して報告する。

   ```bash
   git log --oneline -5
   git branch --show-current
   git status --short
   ```

   コマンド出力はユーザーに自動表示されないため、current branch、merge commit、recent log entries、final status を要約する。

## Conflict Handling

conflict が起きた場合、自動で abort しない。conflicted files を報告し、リポジトリは merge-conflict 状態のまま残す。

```text
マージコンフリクトが発生しました:
- <file>

解決後に git add と git commit で完了するか、git merge --abort で中止してください。
```

## 禁止事項

- `main` または `master` へ merge しない
- `--ff` や `--ff-only` を使わない。常に `--no-ff`
- ユーザーが明示しない限り push しない
- ユーザーが明示しない限り conflicted merge を abort しない
- final branch、recent log、status report を省略しない
