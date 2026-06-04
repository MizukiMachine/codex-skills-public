---
name: skill-installer
description: "Codexスキルを公開リストやGitHubリポジトリパスからインストールする。インストール可能なスキル一覧、公開/非公開リポジトリのスキル追加で使う。"
metadata:
  short-description: openai/skillsなどのrepoからcurated skillsをインストール
---

# Skill Installer

スキルのインストールを支援する。既定では https://github.com/openai/skills/tree/main/skills/.curated から扱うが、ユーザーが別の場所を指定した場合はその場所を使う。実験的なスキルは https://github.com/openai/skills/tree/main/skills/.experimental にあり、同じ手順でインストールできる。

タスクに応じてヘルパースクリプトを使う。

- ユーザーが利用可能なスキルを聞いた場合、または何をするか指定せずにこのスキルを使った場合は、スキル一覧を表示する。既定の一覧は `.curated`。実験的スキルを聞かれた場合は `--path skills/.experimental` を渡す。
- ユーザーがスキル名を指定した場合は curated 一覧からインストールする。
- ユーザーが GitHub の repo/path を指定した場合は、その repo からインストールする。private repo も対象にする。

スキルのインストールにはヘルパースクリプトを使う。

## Communication

スキル一覧を表示するときは、ユーザーの文脈に合わせて概ね次の形で出力する。実験的スキルを求められた場合は `.curated` ではなく `.experimental` から一覧を出し、出典もそう表示する。

```text
Skills from {repo}:
1. skill-1
2. skill-2 (already installed)
3. ...
Which ones would you like installed?
```

スキルをインストールした後は、ユーザーに `Restart Codex to pick up new skills.` と伝える。

## Scripts

これらのスクリプトはいずれもネットワークを使う。サンドボックス環境で実行する場合は、実行時に必要な権限昇格を求める。

- `scripts/list-skills.py`: インストール済み注釈つきでスキル一覧を出力する。
- `scripts/list-skills.py --format json`
- 実験的スキル一覧の例: `scripts/list-skills.py --path skills/.experimental`
- `scripts/install-skill-from-github.py --repo <owner>/<repo> --path <path/to/skill> [<path/to/skill> ...]`
- `scripts/install-skill-from-github.py --url https://github.com/<owner>/<repo>/tree/<ref>/<path>`
- 実験的スキルの例: `scripts/install-skill-from-github.py --repo openai/skills --path skills/.experimental/<skill-name>`

## Behavior and Options

- public GitHub repo は既定で直接ダウンロードする。
- ダウンロードが認証・権限エラーで失敗した場合は、git sparse checkout にフォールバックする。
- インストール先のスキルディレクトリが既に存在する場合は中断する。
- `$CODEX_HOME/skills/<skill-name>` にインストールする。既定は `~/.codex/skills`。
- 複数の `--path` 値を渡すと、複数スキルを一度にインストールする。各スキル名は `--name` がない限り path basename から決まる。
- オプション: `--ref <ref>` (既定は `main`)、`--dest <path>`、`--method auto|download|git`。

## Notes

- curated 一覧は GitHub API 経由で `https://github.com/openai/skills/tree/main/skills/.curated` から取得する。利用できない場合はエラーを説明して終了する。
- private GitHub repo は既存の git 認証情報、または download 用の任意の `GITHUB_TOKEN` / `GH_TOKEN` でアクセスできる。
- git フォールバックは HTTPS を先に試し、その後 SSH を試す。
- https://github.com/openai/skills/tree/main/skills/.system のスキルは事前インストール済みなので、通常はユーザーにインストールを支援する必要はない。求められた場合はその旨を説明する。ユーザーが強く希望する場合はダウンロードして上書きしてよい。
- インストール済み注釈は `$CODEX_HOME/skills` から判定する。
