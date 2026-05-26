---
name: gmerge
description: "現在の作業元ブランチを `git merge --no-ff` で `develop` にマージする。ブランチのマージ、developへのマージ、git merge、マージして、developにマージ、ブランチをマージなどを求められたときに使う。mainまたはmasterへの直接マージはブロックする。"
---

# Git Merge Skill

Merge a source branch into `develop` with `--no-ff`, while blocking direct `main`/`master` merge targets and avoiding pushes.

## Workflow

1. Identify the source branch.

   ```bash
   git branch --show-current
   git status --short
   ```

   If the working tree has uncommitted changes, stop and ask the user whether to commit/stash first. Do not start a merge over unrelated uncommitted work.

2. Block unsafe source states.
   - If the current branch is `main` or `master`, stop with:

   ```text
   エラー: main/master からの直接マージ運用は禁止されています。release ブランチ等を経由してください。
   ```

   - If the current branch is `develop`, stop and ask which source branch should be merged.

3. Ensure `develop` exists.

   ```bash
   git branch --list develop
   ```

   If it does not exist, create it from the current branch:

   ```bash
   git branch develop
   ```

   Tell the user that `develop` was created.

4. Switch to `develop`.

   ```bash
   git checkout develop
   ```

5. Merge with `--no-ff`.

   ```bash
   git merge --no-ff <source-branch> -m "merge: <source-branch> into develop"
   ```

   If the user supplied a merge message, use that message instead.

6. Verify and report.

   ```bash
   git log --oneline -5
   git branch --show-current
   git status --short
   ```

   Since command output is not automatically visible to the user, summarize the current branch, merge commit, recent log entries, and final status.

## Conflict Handling

If conflicts occur, do not abort automatically. Report the conflicted files and leave the repository in the merge-conflict state for the user to resolve.

```text
マージコンフリクトが発生しました:
- <file>

解決後に git add と git commit で完了するか、git merge --abort で中止してください。
```

## Prohibitions

- Do not merge into `main` or `master`.
- Do not use `--ff` or `--ff-only`; always use `--no-ff`.
- Do not push unless the user explicitly asks.
- Do not abort a conflicted merge unless the user explicitly asks.
- Do not omit the final branch, recent log, and status report.
