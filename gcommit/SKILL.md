---
name: gcommit
description: "Git作業ツリーを確認し、新しいブランチを作成して安全にコミットする。コミット、git commit、ブランチ作成とコミット、コミットして、変更をコミット、ブランチ切ってコミットなどを求められたときに使う。変更ファイルが多い場合は意味のある単位に分けてコミットする。"
---

# Git Commit Skill

Create safe, intentional Git commits from the current working tree. Never stage broad file sets blindly.

## Workflow

1. Inspect changes.

   ```bash
   git status --short
   git diff --stat
   git diff --name-only
   git ls-files --others --exclude-standard
   ```

2. Review the diff before staging.
   - Inspect all changed tracked files.
   - Inspect untracked files that may be committed.
   - Preserve unrelated user changes. Do not revert files to clean the tree.

3. Run the safety check before staging.
   - Apply the allowlist in the Safety Check section before matching sensitive patterns.
   - Compare the remaining candidate files against the sensitive and discouraged file patterns below.
   - If any candidate matches, stop and ask the user whether to include it.
   - Exclude files the user rejects.

4. Create a branch.
   - Infer a short Conventional Commits type and scope from the whole change.
   - Use `<type>/<short-summary>`, for example `feat/skill-cleanup`, `fix/auth-validation`, or `chore/config-update`.
   - Keep branch names roughly 30 characters or less.
   - If already on an appropriate task branch, ask before creating another branch only when switching would be risky or surprising.

5. Group commits.
   - Use one commit when there are 10 or fewer candidate files and the change is one logical unit.
   - For 11 or more files, split by directory, change type, or logical feature.
   - Each commit message must use Conventional Commits:

   ```text
   <type>(<scope>): <summary>
   ```

6. Stage explicit paths only.

   ```bash
   git add <file1> <file2>
   git commit -m "<type>(<scope>): <summary>"
   ```

7. Verify and report.

   ```bash
   git log --oneline -<N>
   git status --short
   ```

   Since command output is not automatically visible to the user, summarize the branch name, commit hashes/messages, and final status in the final response.

## Safety Check

Ask before committing any matching file.

Apply this allowlist before path-based sensitive-file matching:

- Environment templates and schemas are not sensitive based on their path alone: `.env.example`, `.env.*.example`, `.env.template`, `.env.schema`, `.env.sample`, `.env.d.ts`.
- Do not flag allowlisted environment template/schema files only because they match `.env.*`.
- If an allowlisted file contains an actual secret value in the diff, treat that content as sensitive and ask before committing it.

Sensitive files:

| Pattern | Examples |
|---|---|
| Environment files | `.env`, `.env.*` except allowlisted templates/schemas, `.envrc` |
| Credentials | `credentials.json`, `*.pem`, `*.key`, `*.p12`, `id_rsa*`, `*.ppk` |
| Tokens/secrets | `*-token*`, `*-secret*`, `*-apikey*` |
| Cloud credentials | `service-account*.json`, `*.gpg`, `*.kubeconfig` |
| Terraform state | `*.tfstate`, `*.tfstate.backup` |

Usually discouraged files:

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
| `feat` | New feature or new capability |
| `fix` | Bug fix |
| `refactor` | Behavior-preserving code restructure |
| `docs` | Documentation only |
| `chore` | Config, metadata, cleanup, maintenance |
| `style` | Formatting, whitespace, naming-only changes |
| `test` | Tests only or test infrastructure |

## Prohibitions

- Do not use `git add .`.
- Do not use `git add -A`.
- Do not use `git commit --amend` unless the user explicitly asks for amend.
- Do not commit sensitive or discouraged files without explicit user approval.
- Do not push unless the user explicitly asks.
- Do not omit the final branch, commit list, and status report.
