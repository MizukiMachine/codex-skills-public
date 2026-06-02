// Direct layer — the deterministic "plan object".
//
// A control layer never sends a raw prompt straight to the model. It first
// computes, from application state, a small deterministic object that declares
// what this single generation must achieve and what it is allowed to treat as
// real. That object is rendered into the prompt. This separates "what the system
// needs this turn to accomplish" (deterministic) from "how the model phrases it"
// (stochastic).
//
// Nothing here is domain-specific. You derive `intents`, `allowedFacts`, and
// `mustNotReveal` from YOUR state; the shape and the cold-context invariant are
// the reusable parts.

/** One concrete objective the output must satisfy this turn. */
export interface Intent {
  /** Stable id, useful for diagnostics and tests. */
  id: string;
  /** Imperative instruction rendered into the prompt. */
  instruction: string;
}

export interface ControlPlan {
  /** Ordered objectives for this single generation. */
  intents: Intent[];
  /**
   * Whitelist of facts the model may treat as established. The censor layer
   * uses this as ground truth: anything asserted as real that is not derivable
   * from here is, by definition, invented.
   */
  allowedFacts: string[];
  /** Hidden information that must not surface in this (public) output. */
  mustNotReveal: string[];
  /**
   * When true, the output must commit to a position / advance the task, not
   * stall with a question or "let me think". Turned OFF for cold context.
   */
  requiresForwardMove: boolean;
  /**
   * True when there is no prior grounding yet (first turn, empty history,
   * fresh thread). Forcing a forward move here is the single most common cause
   * of fabricated filler ("as we discussed…" when nothing was discussed). In
   * cold context, switch intents from "advance/commit" to "open/establish" and
   * relax forward-move — but still demand positive substance (see validators).
   */
  isColdContext: boolean;
}

export interface PlanInputs {
  /** Does any prior grounded context exist for the model to build on? */
  hasPriorContext: boolean;
  /** Objectives derived from your application state. */
  intents: Intent[];
  allowedFacts?: string[];
  mustNotReveal?: string[];
  /**
   * Whether, in principle, this turn should force a committed move. The cold
   * context rule below can still override this to false.
   */
  wantsForwardMove?: boolean;
}

/**
 * Build a plan while enforcing the cold-context invariant in one place, so
 * every call site gets the same hard-won default instead of re-discovering it.
 */
export function definePlan(inputs: PlanInputs): ControlPlan {
  const isColdContext = !inputs.hasPriorContext;
  return {
    intents: inputs.intents,
    allowedFacts: inputs.allowedFacts ?? [],
    mustNotReveal: inputs.mustNotReveal ?? [],
    // Never force a forward move in cold context.
    requiresForwardMove: Boolean(inputs.wantsForwardMove) && !isColdContext,
    isColdContext
  };
}

/**
 * Render the plan into a prompt fragment. Keep it terse: the plan steers, it
 * does not narrate. The "may only treat as real" line is the load-bearing
 * grounding instruction — keep it even when trimming.
 */
export function renderPlan(plan: ControlPlan): string {
  const lines: string[] = [];

  lines.push("Goals for this response:");
  for (const intent of plan.intents) {
    lines.push(`- ${intent.instruction}`);
  }

  if (plan.allowedFacts.length > 0) {
    lines.push("");
    lines.push("You may only treat the following as established fact. Anything not here is unknown — do not invent it, and do not reference events, statements, or results that are not present:");
    for (const fact of plan.allowedFacts) {
      lines.push(`- ${fact}`);
    }
  } else if (plan.isColdContext) {
    lines.push("");
    lines.push("No established context yet. Do not reference prior statements, reactions, or results — none exist. Open the topic instead of citing history.");
  } else {
    lines.push("");
    lines.push("No additional facts are listed for this turn. Rely only on context already shared with you; do not invent events, statements, or results that are not present.");
  }

  if (plan.mustNotReveal.length > 0) {
    lines.push("");
    lines.push("Never reveal in this response:");
    for (const secret of plan.mustNotReveal) {
      lines.push(`- ${secret}`);
    }
  }

  if (plan.requiresForwardMove) {
    lines.push("");
    lines.push("Do not stop at a question or a wait-and-see note. Commit to a concrete position and state it plainly.");
  } else if (plan.isColdContext) {
    lines.push("");
    lines.push("There is nothing to react to yet, but do not be passive: open with a concrete proposal, criterion, or named question. Avoid filler such as 'let me see how this develops'.");
  }

  return lines.join("\n");
}
