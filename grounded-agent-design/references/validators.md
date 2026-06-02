# Validator Patterns & Pitfalls

How to implement the censor's checks so they stay maintainable, multilingual, and
honest. Pairs with `assets/control-layer/validators.ts`.

## Contents

- [Validator contract](#validator-contract)
- [Patterns are configuration](#patterns-are-configuration)
- [The catalog](#the-catalog)
- [Metadata round-trip](#metadata-round-trip)
- [Anti-repetition](#anti-repetition)
- [Pitfalls](#pitfalls)

## Validator contract

A validator takes the output, the ground-truth set, the known entities, and the
plan, and returns either `null` (clean) or a `Violation` carrying a `code`, a
`message`, and a `revisionHint`. Validators are pure functions — no model calls,
no I/O — so they are fast and unit-testable. Compose them with `runValidators`,
which returns *all* violations so the revision hint can address everything at
once.

## Patterns are configuration

The biggest maintainability lesson: **keep language/domain patterns out of the
detection logic.** A validator encodes a *strategy* ("entity near an action cue
that isn't in the facts"); the *cue words* live in a `Lexicon` passed in. This:

- makes the same validator work across languages by swapping the lexicon;
- lets you tune detection against transcripts without touching code;
- keeps the logic readable instead of a wall of inlined regex.

Expect morphologically rich languages (e.g. Japanese) to need *phrase* cues and
sometimes small regex fragments rather than plain word membership. That is fine —
put the richer patterns in the lexicon, keep the strategy generic.

The cue words ship as **YAML** so they can be edited without touching code:
`assets/control-layer/lexicons/en.yaml` and `ja.yaml` are the single source of
truth; `loadLexicon("en"|"ja"|"<path>")` reads them into a `Lexicon`, and
`lexicons.ts` re-exports `englishLexicon` / `japaneseLexicon`. Add a language by
dropping in `lexicons/<lang>.yaml`. The reader is a small dependency-free one for
the constrained `key:` / `- value` shape — swap in a real YAML library if you
outgrow it. Tune the lists against your own failure transcripts.

## The catalog

| Validator | Catches | Needs |
|-----------|---------|-------|
| `groundedReferences(lexicon)` | Invented references (action-level) | `entities`, `visibleFacts`, `actionCues` |
| `noBoundaryLeak` | Boundary leaks | `plan.mustNotReveal` |
| `hasForwardSubstance(lexicon)` | Missing positive content | `stanceCues`, `fillerCues`, `substanceCues` |
| `notRepetitive(priorAngles)` | Repetition | prior actors' recorded angles |

`hasForwardSubstance` requires *positive* content (a stance or a substantive move),
not merely the absence of filler — otherwise a content-free non-filler line ("nice
weather today") slips through a forced opening. It is scoped: a **cold** opening
must carry a stance OR a `substanceCue` (proposal/criterion/named question); a
**warm** forward-move only rejects the clear stall (filler with no such content),
to avoid over-rejecting ordinary lines.

`groundedReferences` checks grounding at the **action** level: it flags an action
attributed to an entity that the facts do not corroborate, including a known
entity the facts mention only for an unrelated reason — not just fully-unknown
entities. Residual limitation: it cannot catch a paraphrastic action-swap that
reuses a shared noun ("Bob reported X approved" vs the fact "Bob asked about X").
Add an entailment/NLI check in production when that matters.

Add domain-specific validators in the same shape. Common additions:

- **claim-traces-to-source** (RAG): every factual sentence must overlap a
  retrieved chunk id/text; reject otherwise.
- **legal-target** (decision channel): the chosen id is in the allowed set.
- **misstated-silence**: the output says an entity has not acted, but the
  transcript shows it has.

## Metadata round-trip

A powerful pattern: after the model speaks in natural language, **extract
structured signals back out** of the text (who it suspected/trusted, what option
it leaned toward, which entity it addressed). Feed those signals into:

- downstream app logic (tally, scoring, state transitions);
- the **anti-repetition** validator on later turns (you now know what angles are
  already on the table);
- diagnostics (what the population is converging on).

The round-trip — structured plan in, free text out, structured signal back in —
lets the rest of the system reason over conversational output without forcing the
model to emit rigid JSON in its spoken channel.

## Anti-repetition

In multi-actor settings, independent generations converge: everyone suspects the
same target for the same reason. Counter it by feeding each actor a compact digest
of the angles already used (from the metadata round-trip) and running
`notRepetitive`. The revision hint should push toward a *distinct* contribution
(a new consequence, a counterpoint, an alternate candidate) rather than silence.
In single-actor assistants this check is usually unnecessary — skip it.

## Pitfalls

- **Over-detecting.** A trigger-happy validator rejects valid outputs and burns
  retries. Calibrate against known-good fixtures, not just known-bad ones.
- **Checking plausibility instead of ground truth.** If a validator does not
  consult `visibleFacts`, it is guessing. Every grounding check must compare.
- **One mega-regex.** Splitting by failure mode keeps each check debuggable and
  lets you attach a precise revision hint per mode.
- **Validating the wrong channel.** Do not run prose validators on a structured
  decision; do not run a schema parse on a spoken line.
- **Silent truncation.** If you cap entities/facts scanned for performance, log
  it — a validator that quietly skips inputs reads as "clean" when it is blind.
