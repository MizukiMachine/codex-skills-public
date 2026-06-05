---
name: skill-creator
description: "Codexスキルを作成・更新するためのガイド。新規スキル、既存スキル、ワークフロー、ツール統合、メタデータ設計を整えるときに使う。"
metadata:
  short-description: スキルを作成・更新
---

# Skill Creator

このスキルは、実用的で効果的な Codex スキルを作成・更新するための指針を提供する。

## About Skills

スキルは、Codex の能力を拡張する自己完結したフォルダである。特定の領域やタスクに必要な専門知識、手順、ツール、再利用可能なリソースを提供し、汎用エージェントをタスクに特化したエージェントとして動けるようにする。

### What Skills Provide

スキルが提供するもの:

1. 専門的な workflow: 特定領域向けの複数ステップ手順。
2. tool integration: 特定の file format、API、ツールの扱い方。
3. domain expertise: company 固有の知識、schema、business logic。
4. bundled resources: 反復的・複雑な作業を支える scripts、references、assets。

## Core Principles

### Concise Is Key

context window は共有資源である。スキル本文は system prompt、会話履歴、他のスキル metadata、ユーザー依頼と同じ context を使う。

Codex は既にかなり賢いという前提で、Codex がまだ持っていない非自明な context だけを追加する。各説明について「この説明は本当に必要か」「token cost に見合うか」を確認する。長い説明より、短く具体的な例を優先する。

### Set Appropriate Degrees of Freedom

タスクの壊れやすさと可変性に合わせて、スキルが与える自由度を調整する。

- High freedom: 複数の approach が有効で、判断が context に依存し、heuristic が中心の場合。text instruction が向いている。
- Medium freedom: 推奨 pattern はあるが多少の variation が必要な場合。pseudocode や parameter 付き script が向いている。
- Low freedom: 操作が壊れやすく、順序や一貫性が重要な場合。具体的な script と少数 parameter が向いている。

Codex が経路を進む様子をイメージするとよい。崖に挟まれた狭い橋には specific な guardrail（low freedom）が要り、開けた野原なら多くの route を選べる（high freedom）。

### Protect Validation Integrity

subagent が使える環境では、現実的なタスクでスキルが機能するか、疑わしい問題が本当にあるかを検証するために subagent を使ってよい。目的は別エージェントが事前に漏れた答えを再構成できるかではなく、スキルが一般化するかを知ることである。

検証では、example prompt、output、diff、log、trace などの raw artifact を優先する。必要最小限の task-local context だけを渡し、検証に必要でない限り、意図した答え、疑っている bug、予定している fix、これまでの結論は渡さない。

## Anatomy of a Skill

すべてのスキルは必須の `SKILL.md` と任意の bundled resources で構成される。

```text
skill-name/
├── SKILL.md (required)
│   ├── YAML frontmatter metadata (required)
│   │   ├── name: (required)
│   │   └── description: (required)
│   └── Markdown instructions (required)
├── agents/ (recommended)
│   └── openai.yaml - skill list や chip 向け UI metadata
└── Bundled Resources (optional)
    ├── scripts/          - executable code (Python/Bash/etc.)
    ├── references/       - 必要時に context に読む documentation
    └── assets/           - templates, icons, fonts など output で使う file
```

#### SKILL.md (required)

`SKILL.md` は次で構成する。

- Frontmatter (YAML): `name` と `description` を含む。Codex がスキルを使うべきか判断するために読むのは基本的にこの field なので、何をするスキルか、いつ使うかを明確かつ包括的に書く。
- Body (Markdown): スキルが trigger された後にだけ読み込まれる手順と guidance。

#### Agents metadata (recommended)

`agents/openai.yaml` は skill list や chip に出る UI 向け metadata である。

- 値を生成する前に `references/openai_yaml.md` を読み、その field 説明と制約に従う。
- スキル本文を読んで、人間向けの `display_name`、`short_description`、`default_prompt` を作る。
- `scripts/generate_openai_yaml.py` または `scripts/init_skill.py` に `--interface key=value` として渡し、決定論的に生成する。
- 更新時は `agents/openai.yaml` が `SKILL.md` と一致しているか確認し、古ければ再生成する。
- icons や brand color など任意 field は、ユーザーが明示的に提供した場合だけ含める。

#### Bundled Resources (optional)

##### Scripts (`scripts/`)

決定論的な信頼性が必要な処理、または毎回同じ code を書き直しがちな処理を入れる。

- 例: PDF 回転用の `scripts/rotate_pdf.py`。
- 利点: token efficient、決定論的、context に読み込まず実行できる。
- script は patch や環境差分対応のために Codex が読む場合がある。

##### References (`references/`)

Codex が作業中に必要に応じて読む documentation や reference material を入れる。

- 例: database schema、API documentation、domain knowledge、company policy、detailed workflow guide。
- 大きい file（10k words 超）は `SKILL.md` に grep 検索 pattern を含める。
- 情報は `SKILL.md` か references のどちらか一方に置く。重複を避ける。
- `SKILL.md` には core workflow と essential instruction を残し、詳細な schema や例は references に移す。

##### Assets (`assets/`)

context に読むためではなく、Codex が output を作るときに使う file を入れる。

- 例: `assets/logo.png`、PowerPoint template、HTML/React boilerplate、font file。
- template、image、icon、boilerplate code、sample document など、コピーまたは変更して成果物に使うものに向いている。

#### What to Not Include in a Skill

スキルには、その機能を直接支える必須 file だけを含める。次のような補助 document は作らない。

- `README.md`
- `INSTALLATION_GUIDE.md`
- `QUICK_REFERENCE.md`
- `CHANGELOG.md`

スキルは AI agent が仕事をするために必要な情報だけを含める。作成過程、setup/test 手順、user-facing documentation などを余分に置くと混乱と clutter が増える。

### Progressive Disclosure Design Principle

スキルは context を効率的に使うため、3段階で読み込む。

1. Metadata (`name` + `description`): 常に context にある（約100 words）。
2. `SKILL.md` body: スキルが trigger されたときに読む（5k words 未満）。
3. Bundled resources: Codex が必要と判断したときだけ読む。script は context に読み込まず実行できるため上限なし。

#### Progressive Disclosure Patterns

`SKILL.md` body は essentials に絞り、context bloat を避けるため500行未満にする。上限に近づいたら別 file に分ける。分割した file は `SKILL.md` から直接参照し、いつ読むべきかを明確に書く。読み手がその存在と使いどころを把握できるようにすることが重要。

**Key principle:** 複数の variation、framework、option を扱うスキルでは、core workflow と selection guidance だけを `SKILL.md` に残し、variant-specific detail（patterns、examples、configuration）は reference file に移す。

**Pattern 1: references を持つ high-level guide**

```markdown
# PDF Processing

## Quick start

Extract text with pdfplumber:
[code example]

## Advanced features

- **Form filling**: See [FORMS.md](FORMS.md) for complete guide
- **API reference**: See [REFERENCE.md](REFERENCE.md) for all methods
- **Examples**: See [EXAMPLES.md](EXAMPLES.md) for common patterns
```

Codex は必要なときだけ FORMS.md、REFERENCE.md、EXAMPLES.md を読む。

**Pattern 2: domain ごとの構成**

複数 domain を持つスキルでは、無関係な context を読まないよう domain ごとに整理する:

```text
bigquery-skill/
├── SKILL.md (overview and navigation)
└── reference/
    ├── finance.md (revenue, billing metrics)
    ├── sales.md (opportunities, pipeline)
    ├── product.md (API usage, features)
    └── marketing.md (campaigns, attribution)
```

user が sales metrics を聞いたら、Codex は sales.md だけを読む。

同様に、複数の framework や variant を扱うスキルは variant ごとに整理する:

```text
cloud-deploy/
├── SKILL.md (workflow + provider selection)
└── references/
    ├── aws.md (AWS deployment patterns)
    ├── gcp.md (GCP deployment patterns)
    └── azure.md (Azure deployment patterns)
```

user が AWS を選んだら、Codex は aws.md だけを読む。

**Pattern 3: conditional details**

basic content を見せ、advanced content へ link する:

```markdown
# DOCX Processing

## Creating documents

Use docx-js for new documents. See [DOCX-JS.md](DOCX-JS.md).

## Editing documents

For simple edits, modify the XML directly.

**For tracked changes**: See [REDLINING.md](REDLINING.md)
**For OOXML details**: See [OOXML.md](OOXML.md)
```

Codex は user がその機能を必要とするときだけ REDLINING.md や OOXML.md を読む。

**guideline:**

- **深い参照の入れ子を避ける**: reference file は `SKILL.md` から1階層に保ち、すべて `SKILL.md` から直接 link する。
- **長い reference file は構造化する**: 100行を超える file には、preview 時に全体像が分かるよう冒頭に目次を置く。

## Skill Creation Process

スキル作成は次の順序で進める。明確な理由がある場合だけ step を skip する。

1. 具体例でスキルを理解する。
2. 再利用可能な内容を計画する。
3. スキルを初期化する。
4. スキルを編集し、resources を実装する。
5. スキルを検証する。
6. 実利用や forward-test から反復する。

### Skill Naming

- lowercase letters、digits、hyphens のみを使う。ユーザー提供 title は hyphen-case に正規化する。例: `Plan Mode` -> `plan-mode`。
- 生成名は64文字未満にする。
- action を表す短い verb-led phrase を優先する。
- triggering の明瞭さが上がる場合は tool 名で namespace する。例: `gh-address-comments`、`linear-address-issue`。
- skill folder 名は skill name と完全に同じにする。

### Step 1: Concrete Examples

使用 pattern が既に明確な場合だけ skip する。既存スキルの更新でも、この step は有用なことが多い。

スキルがどう使われるかを、ユーザーの例またはユーザー feedback で検証した仮例から把握する。質問は一度に多くしすぎず、最重要のものから始める。

例:

- どの機能を支援すべきか。
- どんな依頼文で使われる想定か。
- 何が trigger になり、何は trigger にならないか。
- どこに作成するか。指定がなければ `$CODEX_HOME/skills`、未設定なら `~/.codex/skills` を既定にして Codex が自動発見できるようにする。

機能範囲が明確になったらこの step を終える。

### Step 2: Plan Reusable Contents

各具体例について次を分析する。

1. その例を scratch から実行するには何が必要か。
2. 反復実行時に役立つ scripts、references、assets は何か。

例:

- `pdf-editor`: PDF 回転で同じ code を毎回書き直すため、`scripts/rotate_pdf.py` が有用。
- `frontend-webapp-builder`: boilerplate を毎回作るため、`assets/hello-world/` template が有用。
- `big-query`: schema と relationship を毎回再発見するため、`references/schema.md` が有用。

### Step 3: Initialize the Skill

新規作成では、必ず `init_skill.py` を実行する。既存スキルを更新する場合だけこの step を skip する。

`init_skill.py` 実行前に作成先を確認する。指定がなければ `$CODEX_HOME/skills`、未設定なら `~/.codex/skills` を使う。

```bash
scripts/init_skill.py <skill-name> --path <output-directory> [--resources scripts,references,assets] [--examples]
```

例:

```bash
scripts/init_skill.py my-skill --path "${CODEX_HOME:-$HOME/.codex}/skills"
scripts/init_skill.py my-skill --path "${CODEX_HOME:-$HOME/.codex}/skills" --resources scripts,references
scripts/init_skill.py my-skill --path ~/work/skills --resources scripts --examples
```

script は次を作成する。

- 指定 path 配下の skill directory。
- proper frontmatter と TODO placeholder を含む `SKILL.md` template。
- `--interface key=value` で渡された `display_name`、`short_description`、`default_prompt` を使う `agents/openai.yaml`。
- `--resources` に応じた resource directory。
- `--examples` がある場合の example file。

初期化後、`SKILL.md` を具体化し、必要な resources を追加する。`--examples` を使った場合は placeholder file を置き換えるか削除する。

`display_name`、`short_description`、`default_prompt` はスキルを読んで生成し、`init_skill.py` に `--interface key=value` で渡す。後から再生成する場合:

```bash
scripts/generate_openai_yaml.py <path/to/skill-folder> --interface key=value
```

任意の interface field は、ユーザーが明示した場合だけ含める。field 説明と例は `references/openai_yaml.md` を参照する。

### Step 4: Edit the Skill

スキルは別の Codex instance が使うためのものとして書く。Codex にとって有益で非自明な procedural knowledge、domain-specific detail、reusable asset を含める。

大きな revision の後、またはスキルが難しい場合は、現実的な task や artifact で subagent に forward-test させる。検証では診断結果ではなく artifact を渡し、成功が hidden ground truth ではなく transferable reasoning に依存するようにする。

#### Start with Reusable Skill Contents

先に計画した `scripts/`、`references/`、`assets/` から実装する。brand guideline などでは、ユーザーから asset や documentation を受け取る必要がある場合がある。

追加した script は実際に実行して bug がなく期待 output と一致することを確認する。類似 script が多い場合は代表的な sample の検証でよい。

`--examples` を使った場合、不要な placeholder file は削除する。resource directory は本当に必要なものだけ作る。

#### Update SKILL.md

writing は命令形・不定詞的な形を使う。

##### Frontmatter

- YAML frontmatter には `name` と `description` を書く。
- `name`: skill name。
- `description`: スキルの primary triggering mechanism。Codex がいつスキルを使うべきか理解する助けになる。
  - 「Skill が何をするか」と「いつ使うか（具体的な trigger/context）」の両方を含める。
  - 「いつ使うか」はすべて `description` に入れる。body は trigger 後にしか読まれないため、body の "When to Use This Skill" section は trigger には役立たない。
  - `docx` skill の description 例: "Comprehensive document creation, editing, and analysis with support for tracked changes, comments, formatting preservation, and text extraction. Use when Codex needs to work with professional documents (.docx files) for: (1) Creating new documents, (2) Modifying or editing content, (3) Working with tracked changes, (4) Adding comments, or any other document tasks"
- YAML frontmatter に他の field を含めない。

##### Body

- スキルと bundled resources の使い方を書く。
- すべてを本文に詰め込まず、詳細は references や scripts に分ける。
- path、command、制約、検証手順は具体的に書く。

### Step 5: Validate

開発完了後、basic issue を早期に見つけるため skill folder を検証する。

```bash
scripts/quick_validate.py <path/to/skill-folder>
```

validation script は YAML frontmatter format、required fields、naming rules を確認する。失敗したら報告内容を修正し、再実行する。

### Step 6: Iterate

実利用後、または user feedback 後に次の流れで反復する。

1. スキルを現実の task に使う。
2. つまずきや非効率を観察する。
3. `SKILL.md` または bundled resources の更新点を特定する。
4. 変更を実装して再テストする。
5. 妥当であれば forward-test する。

## Forward-Testing

forward-test では、subagent を新しい task を受けた agent として扱う。subagent に「スキルをレビューして」と言うのではなく、ユーザーが依頼するのと近い形で task を渡す。

良い prompt の形:

```text
Use $skill-x at /path/to/skill-x to solve problem y
```

避ける prompt:

```text
Review the skill at /path/to/skill-x; pretend a user asks you to...
```

decision rule:

- 迷う場合は forward-testing 寄りにする。
- 長時間かかる、追加 approval が必要、live production system を変更する可能性がある場合は、ユーザーに proposed prompt を示し、yes/no と修正案を確認する。

注意:

- independent pass には fresh thread を使う。
- skill と request を、実際のユーザー依頼に近い形で渡す。
- conclusion ではなく raw artifact を渡す。
- expected answer、intended fix、事前診断を見せない。
- 各 iteration 後に source artifact から context を再構築する。
- subagent の output、reasoning、emitted artifact を確認する。
- iteration 間で subagent の artifact が残り、次の検証を汚染しないよう cleanup する。

subagent が leaked context を見たときだけ成功するなら、その結果を信用する前にスキルまたは forward-testing setup を修正する。
