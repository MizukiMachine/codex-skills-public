# Cross-Cutting Architecture

How the control layer sits inside a real application: the information boundary it
depends on, where the loop plugs into the app, the bounded-attempt contract, and
its relationship to a separate latency/orchestration runtime.

## Contents

- [Information boundary is a precondition](#information-boundary-is-a-precondition)
- [Where the loop plugs in](#where-the-loop-plugs-in)
- [Bounded attempts and the safe fallback](#bounded-attempts-and-the-safe-fallback)
- [Diagnostics as a first-class output](#diagnostics-as-a-first-class-output)
- [Relationship to a latency runtime](#relationship-to-a-latency-runtime)
- [Integration checklist](#integration-checklist)

## Information boundary is a precondition

The censor can only enforce grounding if each actor's context was *constructed*
from what that actor may know. Asking the model to "pretend you don't know X"
fails because X is in the context and leaks under pressure. The robust design is a
**per-viewer projection** of a single authoritative state, which doubles as the
source of the plan's `allowedFacts`: build the boundary first, and the fact
whitelist falls out of it. When auditing an app that "leaks", grep the **context
builder**, not the prompt text — the fix is usually that secret state reaches a
context it should never enter.

This is the design-time half of the skill, covered in full —
actor/scope mapping, the sensitivity lattice, the access matrix, output
contracts, prompt-injection defense, redaction-by-view, and the RAG/game
patterns — in [boundary-design.md](boundary-design.md). The rest of this file
assumes the boundary exists and focuses on where the run-time loop plugs into it.

## Where the loop plugs in

The control loop wraps the single unit of generation in your app's turn:

```
app turn
  └─ for each actor whose turn it is:
       build projected context (boundary)        ← precondition
       definePlan(state) → renderPlan             ← Direct
       runRevisionLoop(generate, validate, fallback)
            generate: callModel(prompt + hint)
            validate: runValidators(...)          ← Censor
            fallback: safe deterministic line      ← Correct
       commit accepted output to state
       extract structured signals (round-trip)    ← feeds later anti-repetition
```

Keep the loop synchronous *per generation*; parallelism across actors/turns is the
job of the latency runtime below, not the control layer.

## Bounded attempts and the safe fallback

The Correct layer must terminate. Two guarantees:

- **Bounded attempts** — a small `maxAttempts` (2–3). Each retry costs latency and
  tokens; diminishing returns set in fast.
- **Safe deterministic fallback** — when all attempts fail, return a dull but
  always-valid output. This is what lets you keep attempts low without risking a
  hang or a shipped fabrication. Design the fallback per channel: a neutral
  spoken line, or a rule-based default decision.

Never let correction be unbounded, and never ship the last (failing) candidate as
if it passed — return the fallback and record that you did.

## Diagnostics as a first-class output

Emit a record per attempt: which validators fired, whether it was accepted, the
attempt count, whether the fallback was used, and latency. These records are how
you:

- discover new failure modes to encode (cluster the violations over time);
- detect prompt regressions (a spike in a violation code after a prompt edit);
- tune `maxAttempts` (how often does attempt 2 actually save a turn?).

The harness exposes an `onAttempt` hook for exactly this. Treat bad output as a
measurable defect with a dashboard, not an anecdote.

## Relationship to a latency runtime

The control layer governs *correctness of one generation*. It is orthogonal to,
and composes with, a separate **latency/orchestration runtime** that governs
*throughput and tail latency* across many generations:

| Concern | Owner |
|---------|-------|
| Plan, grounding, validation, revision, fallback | control layer (this skill) |
| Concurrency cap, rate limiting, retry/backoff on transport errors | latency runtime |
| Hedged requests (same task ×N, fastest wins, abort losers) | latency runtime |
| Speculative concurrent candidates / prefetch during idle time | latency runtime |
| Abort propagation, provider portability, no-key fallback | latency runtime |

Keep them decoupled: the control layer's `generate` callback simply *calls* the
runtime. The runtime knows nothing about plans or validators; the control layer
knows nothing about queues or hedging. The dependency points one way — control
layer → runtime.

## Integration checklist

- [ ] A per-viewer context projection exists; secret state never enters the wrong
      context (verified by reading the context builder).
- [ ] `allowedFacts` is derived from the projection, not hand-written.
- [ ] The cold-context rule is applied via `definePlan`, not duplicated per call.
- [ ] Spoken and decision channels are validated separately.
- [ ] The revision loop is bounded and has a safe fallback per channel.
- [ ] Per-attempt diagnostics are emitted and inspected.
- [ ] Fixtures of known-good and known-bad outputs guard each validator.
