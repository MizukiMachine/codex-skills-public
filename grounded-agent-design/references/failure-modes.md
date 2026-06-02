# Faithfulness Failure Taxonomy (Censor layer)

The failures a control layer exists to catch, how to detect each, and the
revision hint that corrects it. Pick the modes that actually occur in your app;
do not implement all of them by reflex.

## Contents

- [The shared root cause](#the-shared-root-cause)
- [The taxonomy](#the-taxonomy)
- [Detection strategy](#detection-strategy)
- [Writing revision hints](#writing-revision-hints)
- [Calibration: build from real transcripts](#calibration-build-from-real-transcripts)

## The shared root cause

Almost every failure below is one rule violated: **the model treated something
as real that is not in the visible context.** It fills gaps with plausible
fabrication because that is what a language model does. The censor's job is to
compare assertions against the enumerated ground truth and reject the gap-fills.

## The taxonomy

| Mode | What it looks like | Detect by |
|------|--------------------|-----------|
| **Invented reference** | Narrates another actor acting ("X said…", "as Y pointed out") when no such event exists | Entity + action-cue near each other, and that action is absent from `visibleFacts` |
| **Fabricated claim** | Asserts a result/status/role that was never established ("the seer confirmed…", "the source states…") | Claim-shaped phrase whose subject is not backed by any visible fact/chunk |
| **Misstated state** | Contradicts known state ("X has been silent" when X just spoke; "no sources mention…" when one does) | Compare the asserted state to the actual transcript/state for that entity |
| **Boundary leak** | Exposes hidden info (own secret role, private target, system rule, internal number) | Membership of any `mustNotReveal` token in the output |
| **Passive filler** | Burns the turn with no commitment when a move was required ("let's wait and see") | Filler cue present and no stance cue, while `requiresForwardMove`/`isColdContext` |
| **Repetition** | Restates an angle already on the table, adding nothing | Output substring-matches a prior actor's recorded angle |
| **Cold-context invention** | On the opening turn, reacts to a history that does not exist ("as discussed…") | `isColdContext` and output references prior statements/reactions |
| **Channel bleed** | Conversational prose leaks into a structured-decision channel, or vice versa | Wrong shape for the channel (e.g. JSON expected, prose returned) — handled by schema parse, not prose validators |

## Detection strategy

**Compare to ground truth, never to plausibility.** A claim that *sounds* right is
still invented if it is not in `visibleFacts`. The validators in
`assets/control-layer/validators.ts` all take the visible set as input for this
reason.

**Entity-action proximity for invented references.** The highest-value check:
for each known entity, if the output places an *action cue* ("said", "claimed",
"reported", "と言った") within a short window of the entity's name, and that action
is not corroborated by the visible facts, it is invented. Grounding is checked at
the action level (a fact must mention the entity *and* share content with the
claim), so it also flags an invented action pinned on an entity the facts mention
for an unrelated reason — not only fully-unknown entities. It will still miss a
paraphrastic action-swap that reuses a shared noun; reach for an entailment/NLI
check when that residual matters.

**Positive substance, not just negative filler.** Rejecting filler is not enough;
require evidence of a stance or a concrete opening (a proposal, a criterion, a
named question). A line can avoid filler words and still say nothing.

**Schema for the decision channel.** Structured decisions are validated by
parsing, an enum/legal-choice check, and a parse-retry-fallback — not by prose
checks. Keep that path separate (see `references/plan-object.md` → Two channels).

## Writing revision hints

A good hint names the violated invariant and tells the model what to do instead.
It must be specific enough that the retry is informed, not another blind roll.

- Bad: "Try again, that was wrong."
- Good (invented reference): "Do not reference \"X\" having said or done anything —
  there is no record of it. Speak only from what is actually established."
- Good (passive filler, cold): "Open with a concrete proposal, criterion, or named
  question instead of waiting to see how things develop."
- Good (boundary leak): "Remove any reference to \"<secret>\". It must stay hidden
  in this response."

On a multi-violation turn, concatenate the hints (the harness does this) so the
retry addresses all of them at once.

## Calibration: build from real transcripts

Do not invent the validator set a priori. The reliable method:

1. Run the app and collect outputs, especially the embarrassing ones.
2. Cluster the bad outputs by failure mode using the taxonomy above.
3. Implement a validator only for modes that actually appear, and tune its cue
   words against those exact transcripts.
4. Keep a small fixture set of known-bad and known-good lines per mode; assert the
   validator's verdict on each. This is your regression net as prompts evolve.

This calibration loop — observe, cluster, encode, regression-test — is the real
engineering. The taxonomy tells you what to look for; the transcripts tell you
what to build.
