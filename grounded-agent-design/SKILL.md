---
name: grounded-agent-design
description: >-
  情報境界を設計し、その境界を毎ターン強制する決定論的な制御層を構築・レビューする。
  二層で考える。(1) 境界層(設計時): 単一の正本(authoritative state)から
  actor/ツール/文書/役職ごとに「見えるもの」だけを投影(redaction)し、各アクターの
  コンテキストを許可された情報のみから組み立てる。(2) 制御ループ(実行時): 確率的なLLMを
  Direct(状態から導いた plan で今ターンの目的・許可事実(allowedFacts)・隠すべき情報・前進要否を宣言)
  → Censor(出力を ground truth と照合: 捏造された参照・存在しない主張・境界漏洩・受動的な埋め草・反復を検出)
  → Correct(破られた不変条件を修正ヒントとして戻し有界回数だけ再生成、最後は安全な決定論的出力へフォールバック) で囲う。
  使う場面: 権限付きRAG・社内検索・カスタマーサポートAI・法務/医療/HRアシスタント・マルチエージェントRAG・
  AI NPC・TRPG・推理ゲーム・正体隠匿ゲーム・交渉/会議シミュレーション・チュータリング・
  非公開状態を持つアシスタントなど、アクター/ユーザー/ツール/文書ごとに見える情報や目的が異なり、
  かつ出力が幻覚(起きていない出来事/根拠のない主張)を起こさず・隠し情報を漏らさず・止まらず前進すべきプロダクト。
  トリガー: 「情報境界」「権限付きRAG」「役割ごとに見える情報を変えたい」「redaction/出力契約/漏洩検証」
  「起きていないことをモデルが作る」「見ていない文脈を引用させない」「ちゃんと結論を出させたい」
  「ハルシネーション対策」「根拠ベース回答/faithfulnessチェック」「修正ループ」「プロンプトインジェクション対策」。
---

# Grounded Agent Design

## Purpose

Build LLM systems where (a) different actors may see different information and
(b) every generation stays grounded, on-task, and within bounds. The job has two
inseparable layers:

- **Boundary (design-time)** — make each actor act from *only* the context it is
  allowed to know, by projecting a single authoritative state per viewer. This
  is a product layer, not a prompt instruction.
- **Control loop (run-time)** — wrap each stochastic generation in a
  deterministic **Direct → Censor → Correct** loop that enforces the boundary
  and faithfulness, then falls back to a safe output instead of hanging or
  shipping a fabrication.

The boundary is the *precondition*; the control loop is the *enforcement*. The
boundary decides what is true and visible this turn; the loop checks the output
against exactly that and corrects it when it strays.

Applies to: permissioned RAG, enterprise search, support/legal/medical/HR bots,
multi-agent RAG (planner/retriever/verifier/redactor/answerer), AI NPCs, TRPG,
social-deduction and negotiation games, meeting/simulation agents, tutoring
turns, and any assistant with private notes, hidden roles, document ACLs, or
asymmetric objectives.

## Core Principle

Do not ask one all-knowing LLM to hold the entire truth and merely "be careful".
A stochastic generator violates instructions probabilistically; with enough
turns it *will* leak or fabricate. Two moves replace "be careful":

1. **Model the system as information boundaries.** Separate *who is acting*,
   *what they know*, *what they may reveal*, *what they optimize*, *which output
   contract the product can safely consume*, and *which checks must pass* before
   output reaches a user or another agent. Render each actor's context from code,
   from allowlisted data — never rely on "pretend you don't know X".
2. **Make quality a property of the loop, not the prompt.** Treat the LLM as a
   fast, fluent, **unreliable** generator. Compute a deterministic plan before
   generating, compare the output to ground truth after, and feed the specific
   violated invariant back as a revision hint, bounded, then fall back.

**The load-bearing invariant:** *the model may only treat as real what is in the
visible context.* The boundary layer *constructs* that visible context; the
censor *checks* the output against it. Most failures are a violation of this one
rule — enforce it in the boundary (per-viewer projection) and in the plan
(`allowedFacts` whitelist), and check it in the censor (grounded references).

**Priority when trade-offs collide:** correctness/faithfulness/no-leak >
staying on-task > style/voice > latency. A dull-but-true fallback beats a fluent
fabrication, and a redacted answer beats a leak.

Before implementing, establish:

- **What is the authoritative state, and what is each viewer's projection?** If
  you cannot say which code path strips what, you have no boundary.
- **What is ground truth this turn?** The exact facts/transcript the output may
  reference (= the projection + this actor's private slice). If you cannot
  enumerate it, you cannot censor.
- **What must stay hidden?** Private state, other actors' secrets, system rules,
  tool traces, retrieval internals.
- **Is the context cold?** First turn / empty history / fresh thread. If so, do
  **not** force a committed move — that is the #1 cause of fabricated filler.
- **What is the safe fallback output?** The deterministic line/decision used when
  correction fails. It must always be valid, boring, and leak-free.

## The Two Layers

```
authoritative state (server source of truth)
  └─ per-viewer projection / redaction        ← BOUNDARY (precondition)
       └─ for each actor whose turn it is:
            definePlan(state) → renderPlan      ← DIRECT
            runRevisionLoop(generate, validate, fallback)
                 generate: callModel(prompt + hint)
                 validate: runValidators(...)    ← CENSOR
                 fallback: safe deterministic    ← CORRECT
            commit accepted output to state
            extract structured signals (round-trip) ← feeds anti-repetition
       └─ view-specific redaction before client / next agent ← BOUNDARY (egress)
```

`allowedFacts` is not hand-written; it *falls out of* the projection. Keep the
loop synchronous per generation — concurrency across actors/turns belongs to a
separate latency runtime (see `references/architecture.md`).

## Workflow

**Phase A — Design the boundary** (`references/boundary-design.md`):

1. **Map actors and scopes.** List users, agents, tools, documents, memories,
   system processes, external viewers. For each: role, goal, allowed inputs,
   forbidden inputs, allowed outputs, downstream consumers. Include hidden roles,
   private memories, public history, spectator views (games) or auth, ACLs,
   citations, tool traces (RAG).
2. **Classify information** on a small sensitivity lattice
   (`public / user_provided / confidential / secret / forbidden`). Treat
   retrieval results, summaries, memories, and diagnostics as data with their own
   sensitivity, not harmless text.
3. **Build an access matrix** before writing prompts. Prefer allowlists over
   denylists. Render role-visible context from code, not prompt prose.
4. **Choose output contracts by risk.** Free text only where naturalness is the
   value; JSON/typed schema for actions, target selection, retrieval plans, auth
   decisions, safety gates. Never let unconstrained prose drive irreversible
   actions.
5. **Build prompts from rendered (already-authorized) context**, and treat all
   user input, retrieved docs, emails, tickets, chat logs, and DB text as
   untrusted *data*, not instructions (indirect prompt-injection defense).
6. **Redact by view** at egress: store full data on the server, emit
   view-specific snapshots, mask forbidden fields before they reach the client or
   the next agent.

**Phase B — Build the control loop** (`references/plan-object.md`,
`references/failure-modes.md`, `references/validators.md`):

7. **Define the plan object (Direct).** Model the per-turn contract as data, not
   prose. Derive `intents` and `allowedFacts` from the projection. Apply the
   cold-context rule via `definePlan`.
8. **Enumerate failure modes and write validators (Censor).** Implement only the
   modes that actually occur for this app; keep language cue-words as a `Lexicon`
   (config), not hardcoded logic. Calibrate against real transcripts.
9. **Wire the revision loop (Correct).** Bounded attempts, the *specific*
   violated invariant fed back as a hint, a safe deterministic fallback per
   channel, diagnostics on every attempt.
10. **Adapt the starter harness.** Copy `assets/control-layer/` and replace the
    plan derivation, the lexicon, and the validator set. Keep the loop and types.
11. **Verify** (see Verification): each failure mode caught on a known-bad
    output and passing on a known-good one; the hint flows back; the fallback
    path works; secret state is absent from the *context builder*, not merely
    instructed-against.

## Reference Files

| Topic | File | Use When |
|-------|------|----------|
| Information-boundary design | [boundary-design.md](references/boundary-design.md) | Mapping actors/scopes, sensitivity lattice, access matrix, redaction-by-view, output contracts, prompt-injection defense, RAG & game patterns, prompt boundary template |
| The plan / director layer | [plan-object.md](references/plan-object.md) | What goes in the plan, intents, fact whitelist, forward-move, cold-context, two output channels |
| Faithfulness failure taxonomy | [failure-modes.md](references/failure-modes.md) | Which hallucination/quality failures to detect and the revision-hint for each |
| Validator patterns & pitfalls | [validators.md](references/validators.md) | Implementing detectors, patterns-as-config, metadata round-trip, anti-repetition |
| Cross-cutting architecture | [architecture.md](references/architecture.md) | Where the loop plugs in, bounded attempts + fallback, diagnostics, relationship to a latency runtime |

## Starter Harness (assets/control-layer/)

A dependency-free, typed, runnable reference implementation of the control loop.
Copy it in and adapt.

| File | Role |
|------|------|
| `plan.ts` | Direct: `ControlPlan` type, `definePlan` (bakes in the cold-context invariant), `renderPlan` |
| `validators.ts` | Censor: `Validator` type, `groundedReferences`, `noBoundaryLeak`, `hasForwardSubstance`, `notRepetitive`, `runValidators` |
| `revisionLoop.ts` | Correct: `runRevisionLoop` (bounded attempts, hint feedback, safe fallback, diagnostics hook) |
| `lexicons/en.yaml`, `lexicons/ja.yaml` | The cue words themselves — **edit these (no code) to tune detection per language/domain**. Single source of truth |
| `loadLexicon.ts` | Reads a lexicon YAML into a `Lexicon` (dependency-free; `loadLexicon("en")` or a path) |
| `lexicons.ts` | Thin loader exposing `englishLexicon` / `japaneseLexicon` from the YAML |
| `index.ts` | Barrel export |
| `demo.ts` | Runnable self-check (fake self-correcting generator, no API key) |

The detection *strategy* lives in code (`validators.ts`); the *patterns* (cue
words) live in YAML so a non-programmer can adjust them in a text editor. Add a
new language by dropping in `lexicons/<lang>.yaml` and calling
`loadLexicon("<lang>")`.

Verify the harness runs: `node --import tsx assets/control-layer/demo.ts`
(expects `ALL PASS`). Run from a project where `tsx` resolves; if none, `npm i -D
tsx` first (the harness itself is dependency-free — `tsx` is only the TS runner).

## Patterns and Examples

**The control loop, in shape:**

```ts
const plan = definePlan({ hasPriorContext, intents, allowedFacts, mustNotReveal, wantsForwardMove });
const validators = [groundedReferences(lexicon), noBoundaryLeak, hasForwardSubstance(lexicon)];
const { value, accepted, usedFallback } = await runRevisionLoop({
  generate: (hint) => callModel(buildPrompt(renderPlan(plan), hint)),   // Direct (+ hint on retry)
  validate: (out) => runValidators({ output: out, visibleFacts, entities, plan }, validators), // Censor
  fallback: () => safeDeterministicLine(plan),                          // Correct: never hang
  maxAttempts: 3,
  onAttempt: (info) => telemetry.record(info)
});
```

**Cold-context rule (the hard-won one):**

```ts
// First turn: no history exists. Forcing "commit to a position" makes the model
// invent a history to react to. Open instead — but still demand substance.
const plan = definePlan({ hasPriorContext: false, intents: [openingIntent], wantsForwardMove: true });
// plan.requiresForwardMove === false  (definePlan overrides it in cold context)
```

**RAG pattern (boundary + loop):** ACL-filter documents *before* generation
(boundary), set `allowedFacts` = the retrieved chunks, have the censor reject any
claim that does not trace to a chunk, and redact internal fields/scores at egress.
Full pipeline + hard rules: `references/boundary-design.md` → RAG pattern.

**Simulation / game pattern (boundary + loop):** project role-visible secrets per
actor (boundary), split public speech (prose channel) from action/vote (decision
channel), and censor the spoken line for invented events + boundary leaks while
the decision goes through a legal-target check. Full pipeline + hard rules:
`references/boundary-design.md` → Simulation / game pattern.

**Prompt boundary template:** a compact, copyable starting prompt lives in
`references/boundary-design.md` → Prompt boundary template.

## Anti-Patterns

**Prompt-only faithfulness / "I told it not to make things up".** A stochastic
generator violates instructions probabilistically. Better: enumerate the allowed
facts and *check* the output against them. Instructions reduce the rate; the
censor enforces the floor.

**"Pretend you don't know X" in the prompt.** The secret is in the context, so it
leaks under pressure. Better: an information boundary — never put X in that
actor's context (grep the context builder, not the prompt text).

**Denylists over allowlists.** Enumerating what to hide always misses a case.
Render role-visible context from an allowlist of authorized data.

**Treating retrieved/user text as instructions.** Documents, tickets, emails, and
chat logs can carry "ignore your rules / reveal secrets / change roles". Mark
them as evidence/content; never as developer instructions.

**Discard-and-retry with the same prompt.** An identical prompt re-rolls the same
distribution. Better: feed the *specific* violated invariant back as a hint.

**Forcing a stance on the opening turn.** With no real history, "take a position"
is satisfiable only by inventing one. Cold-context plans open the topic and relax
forward-move while still rejecting passive filler.

**Hardcoding language patterns into validator logic.** Becomes unmaintainable and
monolingual. Keep the detection *strategy* in code, the *cue words* in a `Lexicon`.

**Unbounded correction.** A stubborn model loops forever. Bound attempts, then a
safe deterministic fallback.

**Redaction as a prompt instruction.** Redaction is a product layer: store full
data server-side, emit view-specific snapshots, mask before egress.

## Variation Guidance

Adapt by context; do not ship one fixed validator set:

- **Output channel** — a *public/spoken* line needs boundary + grounding +
  substance checks; an *internal/structured decision* needs schema parse + a
  legal-choice check, not prose validators. Keep the two channels separate.
- **Domain** — RAG answerers center on "every claim traces to a retrieved chunk";
  character/agent sims on "no invented events + no boundary leak"; tutoring on
  "advance the learner + don't assert unstated facts".
- **Language** — swap the lexicon; richer morphology (e.g. Japanese) needs phrase
  patterns rather than word membership.
- **Risk level** — higher stakes warrant more attempts, stricter validators, a
  more conservative fallback; a low-stakes flavor line can run a single pass.
- **Repetition pressure** — multi-actor settings need `notRepetitive` fed with
  prior actors' angles; a single-actor assistant usually does not.

## Review Checklist

Before finishing a design or implementation, answer:

- What is the authoritative state, and which code path computes each viewer's
  projection?
- Are prompts built from allowlisted data? Is `allowedFacts` derived from the
  projection, not hand-written?
- Which outputs are free text, and which are structured? Are the two channels
  validated separately?
- What validates IDs, citations, claims, and actions against ground truth?
- Are user-provided and retrieved texts treated as data, not instructions? What
  neutralizes indirect prompt injection?
- Is the cold-context rule applied via `definePlan` (not duplicated per call)?
- What is redacted before client display or downstream agent use?
- What happens when the LLM returns malformed, stale, leaking, or low-evidence
  output? Is correction bounded with a safe fallback per channel?
- Are per-attempt diagnostics emitted and inspected?
- Which tests prove the boundaries hold and each validator fires?

## Verification

- Run `node --import tsx assets/control-layer/demo.ts` → `ALL PASS`.
- For each failure mode implemented: one known-bad output asserts the matching
  validator returns a violation; one known-good output asserts it passes.
- Assert the revision hint reaches the generator on retry (the demo checks this).
- Assert the fallback path returns the safe output when every attempt fails.
- Confirm hidden state is absent from the actor's *context construction*, not
  merely instructed-against (grep the prompt builder, not the prompt text).
- Boundary tests: an unauthorized document never enters prompt context; an actor
  cannot select an illegal target/document/action ID; public output never exposes
  hidden state; viewer-specific redaction removes private event fields.

## Portfolio Framing

When describing work built with this skill:

> I designed the system around information boundaries rather than a single
> all-knowing prompt, then wrapped each generation in a deterministic
> Direct→Censor→Correct control loop. Each agent receives only the context it is
> authorized to see, free-form language is separated from structured decisions,
> every user-facing view is redacted from authoritative state, and every turn is
> validated against enumerated ground truth with a bounded revision loop and a
> safe fallback. This keeps the LLM expressive while keeping permissions, hidden
> state, citations, grounding, and workflow actions controllable and testable.
