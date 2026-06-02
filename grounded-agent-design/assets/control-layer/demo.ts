// Runnable self-check for the control-layer harness. It uses a fake generator
// (no API key needed) that hallucinates on attempt 1 and self-corrects once it
// receives the revision hint, proving Direct -> Censor -> Correct end to end.
//
// Run from a project that has tsx available:
//   node --import tsx assets/control-layer/demo.ts
// Exits non-zero if any assertion fails.

import { definePlan, renderPlan } from "./plan";
import { groundedReferences, hasForwardSubstance, noBoundaryLeak, runValidators, type ValidationContext } from "./validators";
import { runRevisionLoop } from "./revisionLoop";
import { englishLexicon } from "./lexicons";

let failures = 0;
function assert(cond: boolean, label: string): void {
  if (cond) {
    console.log(`  ok  - ${label}`);
  } else {
    failures += 1;
    console.error(`  FAIL - ${label}`);
  }
}

// --- 1. Direct: build + render a plan (warm context, forward move wanted) ---
const plan = definePlan({
  hasPriorContext: true,
  intents: [{ id: "commit_pick", instruction: "Name one candidate and commit to it." }],
  allowedFacts: ["Alice proposed option B.", "Bob asked for the budget."],
  mustNotReveal: ["the internal margin target"],
  wantsForwardMove: true
});
assert(plan.requiresForwardMove === true, "warm context keeps forward move on");
assert(plan.isColdContext === false, "warm context is not cold");
const rendered = renderPlan(plan);
assert(rendered.includes("You may only treat"), "render emits the grounding clause");

// --- cold-context invariant ---
const coldPlan = definePlan({ hasPriorContext: false, intents: [{ id: "open", instruction: "Open the topic." }], wantsForwardMove: true });
assert(coldPlan.requiresForwardMove === false, "cold context relaxes forced forward move");
assert(coldPlan.isColdContext === true, "cold context flagged");

// --- 2 + 3. Censor + Correct loop with a self-correcting fake generator ---
const validators = [
  groundedReferences(englishLexicon),
  noBoundaryLeak,
  hasForwardSubstance(englishLexicon)
];
const ctxFor = (output: string): ValidationContext => ({
  output,
  visibleFacts: plan.allowedFacts,
  entities: ["Alice", "Bob", "Carol"],
  plan
});

async function main(): Promise<void> {
  // Attempt 1: invents Carol acting + leaks the secret + filler. Attempt 2+: clean.
  const attemptOutputs = [
    "As Carol said earlier, we should wait and see; also the internal margin target is tight.",
    "I think option B is the pick — Alice already proposed it and it answers Bob's budget question."
  ];
  let seenHintOnRetry = false;

  const result = await runRevisionLoop<string>({
    maxAttempts: 3,
    generate: async (hint, attempt) => {
      if (attempt > 1 && hint && hint.length > 0) seenHintOnRetry = true;
      return attemptOutputs[Math.min(attempt - 1, attemptOutputs.length - 1)];
    },
    validate: (candidate) => runValidators(ctxFor(candidate), validators),
    fallback: () => "I'll hold for now.",
    onAttempt: ({ attempt, accepted, violations }) =>
      console.log(`  · attempt ${attempt}: accepted=${accepted} violations=[${violations.map((v) => v.code).join(",")}]`)
  });

  assert(runValidators(ctxFor(attemptOutputs[0]), validators).length >= 2, "attempt 1 is caught (invented ref + leak/filler)");
  assert(seenHintOnRetry, "revision hint is fed back on retry");
  assert(result.accepted === true, "loop accepts the corrected output");
  assert(result.usedFallback === false, "fallback not needed when correction succeeds");
  assert(result.attempts === 2, "accepted on the second attempt");

  // --- fallback path: a generator that never satisfies the plan ---
  const stubborn = await runRevisionLoop<string>({
    maxAttempts: 2,
    generate: async () => "As Carol said, wait and see.",
    validate: (candidate) => runValidators(ctxFor(candidate), validators),
    fallback: () => "SAFE_DEFAULT"
  });
  assert(stubborn.usedFallback === true, "stubborn generator falls back");
  assert(stubborn.value === "SAFE_DEFAULT", "fallback value returned");

  // --- regression: Medium 2 — invented action by a KNOWN entity is caught ---
  // "Alice" appears in the facts (proposed option B) but never "claimed the
  // budget is approved" — action-level grounding must still flag it.
  const inventedKnown = runValidators(ctxFor("Alice claimed the budget is already approved."), validators);
  assert(inventedKnown.some((v) => v.code === "invented_reference"), "invented action by a known entity is flagged");
  const legitRef = runValidators(ctxFor("Alice already proposed option B, so I trust it."), validators);
  assert(legitRef.length === 0, "a grounded reference to a known entity passes");

  // --- regression: Medium 1 — cold opening with no positive content is caught ---
  const ctxCold = (output: string): ValidationContext => ({
    output,
    visibleFacts: [],
    entities: ["Alice", "Bob", "Carol"],
    plan: coldPlan
  });
  assert(
    runValidators(ctxCold("The weather is pleasant today."), validators).some((v) => v.code === "passive_filler"),
    "content-free non-filler opening is rejected in cold context"
  );
  assert(
    runValidators(ctxCold("I propose we set a vote criterion first."), validators).length === 0,
    "a substantive opening passes in cold context"
  );

  console.log(failures === 0 ? "\nALL PASS" : `\n${failures} FAILURE(S)`);
  process.exit(failures === 0 ? 0 : 1);
}

void main();
