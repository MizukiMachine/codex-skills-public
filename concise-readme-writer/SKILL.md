---
name: concise-readme-writer
description: "Create or rewrite compact project README files focused on product purpose, user-facing behavior, and architecture. Use when the user asks for a shorter README, a README format like the Builder Agent Chain example, app/tool/game/site overview docs, README cleanup, or moving development/deployment details out of the README into separate docs."
---

# Concise README Writer

## Purpose

Create README files that explain what the project is, what it does, and how it is structured without becoming an operations manual.

## Operating Model

Treat the README as the reader's first product-and-system orientation, not as a setup checklist. Prioritize:

1. What the project is
2. What users can do
3. How the product behaves
4. How the code is organized
5. Where to find development and deployment details

Keep commands, environment variables, and deployment instructions out of the README unless the user explicitly asks to keep them there.

## Before Writing

- Inspect the existing README and project structure
- Identify the product surface: screens, commands, gameplay, workflows, domain terms, data sources, and key constraints
- Identify the architecture at a high level: frontend, backend, workers, engines, API boundaries, storage, deployment container
- Find existing docs for development and deployment details; create separate docs only when moving operational content out of the README is requested or necessary
- Preserve facts from the codebase; do not invent capabilities

Useful discovery commands:

```bash
sed -n '1,220p' README.md
rg --files -g 'package.json' -g 'Dockerfile' -g 'docs/**' -g 'src/**' -g 'frontend/**' -g 'backend/**'
rg "(route|router|api|health|command|cli|scene|game|worker|schedule|cache|config|Dockerfile)" -n
```

## Deliverables

- A concise `README.md` centered on product description, behavior, and structure
- Optional `docs/development.md` for setup, commands, tests, and local environment notes
- Optional `docs/deployment.md` for Docker, hosting, production environment variables, and health checks
- A brief final note listing changed docs and whether tests were skipped because the change was documentation-only

## README Shape

Use this section order by default:

````markdown
# Project Name

## プロジェクト概要

- ...

## プロジェクトの仕様と挙動

- ...

## 構成

- ...

```text
Browser -> Backend -> ...
```

## 関連ドキュメント

- 開発手順: [docs/development.md](docs/development.md)
- デプロイ手順: [docs/deployment.md](docs/deployment.md)
````

Choose heading names that match the project type and language. Examples:

| Project Type | Overview Heading | Behavior Heading |
|---|---|---|
| Web app or SaaS | `アプリ概要` | `アプリの仕様と挙動` |
| Website | `サイト概要` | `サイトの仕様と挙動` |
| CLI or developer tool | `ツール概要` | `ツールの仕様と挙動` |
| Game | `ゲーム概要` | `ゲームの仕様と挙動` |
| Library | `ライブラリ概要` | `ライブラリの仕様と挙動` |

Do not hard-code `サイト` unless the project is actually a website.

## Style Rules

- Prefer bullet lists over long paragraphs
- Do not end bullet items with Japanese or English sentence punctuation
- Keep the README short enough to scan in one pass
- Use concrete product language from the project rather than generic marketing copy
- Use backticks for screen names, routes, directories, env vars, and commands
- Use one compact architecture diagram only when it clarifies the structure
- Link to separate docs instead of embedding setup, command, and deployment details
- Keep all claims grounded in the codebase or existing docs

## Reference Files

| Topic | File | Use When |
|---|---|---|
| Few-shot README | `references/builder-agent-chain-readme.md` | You need an example of the preferred tone, section shape, and bullet style |

## Anti-Patterns

**README as operations manual**

Why bad: It buries the project's identity under setup commands and environment tables

Better: Move operations details to `docs/development.md` and `docs/deployment.md`, then link them from README

**Generic product pitch**

Why bad: It sounds polished but fails to explain the actual product behavior

Better: Describe the real screens, commands, gameplay, workflows, data sources, cache behavior, permissions, and architecture

**Over-detailed internals**

Why bad: It turns README into low-level implementation notes

Better: Keep implementation detail only when it changes how the reader understands behavior

**Punctuated bullet endings**

Why bad: The preferred format is clean, compact bullets without terminal punctuation

Better: Remove trailing `。`, `.`, and similar punctuation from bullet items

## Verification

- Read the final README top to bottom and confirm it contains no development or deployment procedure blocks except links to separate docs
- Check bullet endings for unwanted punctuation
- Check links to newly created docs
- Run tests only when code changes were made; for documentation-only edits, state that tests were not run
