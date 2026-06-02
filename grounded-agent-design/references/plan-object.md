# The Plan Object (Direct layer)

How to design the deterministic object that steers each generation. The plan is
computed from application state *before* the prompt is built, and rendered into
it. It is the seam between deterministic game/app logic and the stochastic model.

## Contents

- [Why a plan object](#why-a-plan-object)
- [Fields and how to derive them](#fields-and-how-to-derive-them)
- [The cold-context rule](#the-cold-context-rule)
- [Two output channels](#two-output-channels)
- [Rendering the plan](#rendering-the-plan)
- [Worked derivations](#worked-derivations)

## Why a plan object

A single giant prompt couples two things that change for different reasons: *what
the turn must accomplish* (a function of app state — deterministic, testable) and
*how it is phrased* (the model's job — stochastic). Splitting them gives you:

- a place to enforce invariants once (e.g. cold-context, boundary) instead of in
  prose scattered across prompt templates;
- testable turn logic — you can unit-test "given this state, the plan requires a
  forward move and whitelists exactly these facts" with no model call;
- a stable target for the censor — the same plan that steered generation is what
  you validate against.

Think of it as a director handing an actor a beat sheet: objective, the facts
they're allowed to know, what to keep secret, and whether this beat must land a
decision.

## Fields and how to derive them

| Field | Meaning | Derive from |
|-------|---------|-------------|
| `intents` | Ordered objectives for this one turn | The phase/step of your app loop and what just happened (a new event to react to, a decision due, an opening) |
| `allowedFacts` | Whitelist the model may treat as established | The actor's *visible* slice of state: the public transcript + this actor's private knowledge. Nothing else. |
| `mustNotReveal` | Hidden info that must not surface | This actor's secrets and any state they should not expose in a public channel |
| `requiresForwardMove` | Must commit / advance, not stall | Whether the step needs a decision and context is warm (see cold rule) |
| `isColdContext` | No prior grounding exists yet | `!hasPriorContext` — first turn, empty history, fresh thread |

**Intents are small and concrete.** "Connect to the most recent event, then state
one committed read" beats "play well". Enumerate a handful of intent kinds for
your app and select among them by state; assign different opening intents to
different actors so a multi-actor scene does not converge on one shape.

**`allowedFacts` is the grounding contract.** Build it from exactly what the actor
can see. This is also the censor's ground truth, so be precise: if a fact is not
here, the model asserting it is, by definition, inventing.

## The cold-context rule

The single most important invariant. On the opening turn there is no transcript,
no prior decision, nothing to react to. If the plan still says "commit to a
position", the only way the model can satisfy that is to **invent a history to
react to** ("as we discussed…", "reacting to the earlier point…"). This is the
textbook source of circular, fabricated filler.

The fix, encoded in `definePlan`:

- when `hasPriorContext` is false, force `requiresForwardMove = false`;
- switch intents from *advance/commit* to *open/establish* (offer a criterion, a
  proposal, a named question);
- but **do not let it go passive** — still require positive substance, so the
  opening is not "let me see how this develops" (the censor's `hasForwardSubstance`
  check enforces this in cold context too).

Cold context relaxes *forcing a stance*, not *being substantive*.

## Two output channels

Most actors need two distinct generations with different contracts:

- **Public / spoken channel** — natural language shown to others. Validated for
  grounding, boundary, and substance. Free-form text out.
- **Internal / decision channel** — a structured choice (who to target, yes/no,
  which option). Validated by schema parse + "is this a legal choice", not by
  prose validators. JSON/enum out, with parse-retry-fallback.

Keep them separate: a spoken line should never be parsed as a decision, and a
decision prompt should not be checked for conversational substance. The plan can
carry both, but render and validate each channel on its own terms.

## Rendering the plan

Keep the rendered fragment terse — the plan steers, it does not narrate. Always
keep the grounding clause even when trimming for tokens:

> You may only treat the following as established fact. Anything not here is
> unknown — do not invent it, and do not reference events, statements, or results
> that are not present: …

When `allowedFacts` is empty (cold context), say so explicitly rather than
omitting it — "no established context yet; do not cite history" is a stronger
guardrail than silence. See `renderPlan` in `assets/control-layer/plan.ts`.

## Worked derivations

**Turn-based multi-actor sim, an actor speaks mid-scene (warm):**
`intents = [react to the latest event, then state one committed read]`,
`allowedFacts = public transcript + this actor's private knowledge`,
`mustNotReveal = this actor's secret role/state`, `wantsForwardMove = true` →
`requiresForwardMove = true`.

**Same sim, very first line of the scene (cold):**
`intents = [open with a concrete criterion or named question]`,
`allowedFacts = []`, `wantsForwardMove = true` but
`requiresForwardMove = false` (cold override), `isColdContext = true`.

**RAG answerer:** `intents = [answer the question]`, `allowedFacts = the
retrieved chunks (ids + text)`, `mustNotReveal = []`, `requiresForwardMove =
true` (commit to an answer or an explicit "not in the sources"). The censor then
checks every claim traces to a chunk.

**Tutoring turn:** `intents = [advance the learner one step from their last
answer]`, `allowedFacts = the lesson state + the learner's visible work`,
`requiresForwardMove = true`. The censor rejects asserting facts the lesson has
not introduced and rejects stalling.
