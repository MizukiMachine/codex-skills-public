---
name: gcommit
description: "Git作業ツリーを確認し、新しいブランチを切って安全にコミットする。gc、$gc、コミット、ブランチ作成とコミットを頼まれたときに使う。"
---

# Git Commit Skill

現在の作業ツリーから、安全で意図のはっきりした Git commit を作る。広い file set を不用意に stage しない。

## ワークフロー

1. 変更を確認する。

   ```bash
   git status --short
   git diff --stat
   git diff --name-only
   git ls-files --others --exclude-standard
   ```

2. stage 前に diff を読む。
   - 変更済み tracked files をすべて確認する
   - commit 対象になりそうな untracked files を確認する
   - 無関係なユーザー変更は保持する。tree をきれいにする目的で戻さない

3. stage 前に safety check を実行する。
   - path-based sensitive pattern に照合する前に allowlist を適用する
   - 残った candidate files を sensitive / discouraged patterns と照合する
   - 該当 file があれば止まり、含めるかユーザーに確認する
   - ユーザーが拒否した file は除外する

4. branch を作る。
   - 変更全体から短い Conventional Commits の type と scope を推測する
   - `<type>/<short-summary>` を使う。例: `feat/skill-cleanup`, `fix/auth-validation`, `chore/config-update`
   - branch name はおおむね30文字以内にする
   - すでに適切な task branch にいる場合、切り替えが危険または意外なときだけ確認する

5. commit を分ける。
   - candidate files が10個以下で1つの論理単位なら1 commit にする
   - 11個以上なら directory、change type、logical feature で分ける
   - commit message は Conventional Commits にする

   ```text
   <type>(<scope>): <summary>
   ```

6. 明示 path だけを stage する。

   ```bash
   git add <file1> <file2>
   git commit -m "<type>(<scope>): <summary>"
   ```

7. 検証して報告する。

   ```bash
   git log --oneline -<N>
   git status --short
   ```

   コマンド出力はユーザーに自動表示されないため、最終回答では branch name、commit hash/message、最終 status を要約する。

## Safety Check

次に該当する file は commit 前に必ず確認する。

path-based sensitive-file matching の前に、この allowlist を適用する。

- 環境変数テンプレートと schema は path だけでは sensitive とみなさない: `.env.example`, `.env.*.example`, `.env.template`, `.env.schema`, `.env.sample`, `.env.d.ts`
- allowlisted environment template/schema files は `.env.*` に一致するだけでは flag しない
- allowlisted file の diff に実 secret value が含まれる場合、その内容は sensitive として扱い、確認する

Sensitive files:

| Pattern | Examples |
|---|---|
| Environment files | `.env`, `.env.*` except allowlisted templates/schemas, `.envrc` |
| Credentials | `credentials.json`, `*.pem`, `*.key`, `*.p12`, `id_rsa*`, `*.ppk` |
| Tokens/secrets | `*-token*`, `*-secret*`, `*-apikey*` |
| Cloud credentials | `service-account*.json`, `*.gpg`, `*.kubeconfig` |
| Terraform state | `*.tfstate`, `*.tfstate.backup` |

通常は避ける files:

| Pattern | Examples |
|---|---|
| Large binaries | `*.exe`, `*.dll`, `*.so`, `*.dylib`, `*.zip`, `*.tar.gz` |
| Build output | `dist/`, `build/`, `target/`, `node_modules/` |
| Local editor settings | `.idea/`, `.vscode/settings.json` unless intentionally shared |
| OS files | `.DS_Store`, `Thumbs.db`, `desktop.ini` |
| Logs | `*.log`, `npm-debug.log*` |

## Commit Types

| Type | Use |
|---|---|
| `feat` | 新機能または新しい capability |
| `fix` | バグ修正 |
| `refactor` | 挙動を変えないコード整理 |
| `docs` | ドキュメントのみ |
| `chore` | 設定、metadata、cleanup、maintenance |
| `style` | formatting、whitespace、naming-only changes |
| `test` | tests only または test infrastructure |

## 禁止事項

- `git add .` を使わない
- `git add -A` を使わない
- ユーザーが明示しない限り `git commit --amend` しない
- explicit approval なしに sensitive または discouraged files を commit しない
- ユーザーが明示しない限り push しない
- 最終 branch、commit list、status report を省略しない
