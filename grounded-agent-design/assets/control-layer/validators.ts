// Censor layer — validate a generated output against ground truth and the plan.
//
// The core idea: faithfulness is not a vibe, it is a comparison. Every check
// here compares the output to the *visible context set* (what actually exists)
// or to the plan's contract. A violation carries a targeted revision hint that
// names the broken invariant, so the Correct layer can regenerate with that
// hint instead of blindly retrying.
//
// Language cue words are passed in as a `Lexicon`, never hardcoded. This is the
// generalization of an important lesson: detection patterns are configuration
// (per language / per domain), the detection *strategy* is the reusable part.

import type { ControlPlan } from "./plan";

export interface Violation {
  /** Stable machine code for diagnostics/tests, e.g. "invented_reference". */
  code: string;
  /** Human-readable description of what went wrong. */
  message: string;
  /** Instruction fed back to the generator on the next attempt. */
  revisionHint: string;
}

export interface ValidationContext {
  /** The model's raw output text. */
  output: string;
  /**
   * Ground-truth facts that actually exist this turn (typically plan.allowedFacts
   * plus the visible transcript). The output may reference these freely.
   */
  visibleFacts: string[];
  /**
   * Known entity labels (player names, doc ids, ticket keys…). If the output
   * claims one of these *acted* ("X said", "Y reported") but that action is not
   * in visibleFacts, it is an invented reference.
   */
  entities: string[];
  plan: ControlPlan;
}

export type Validator = (ctx: ValidationContext) => Violation | null;

/** Cue words, supplied per language so validators stay language-agnostic. */
export interface Lexicon {
  /** Verbs implying an entity performed a visible action ("said", "claimed"). */
  actionCues: string[];
  /** Phrases that assert a committed stance ("I think", "vote for", "trust"). */
  stanceCues: string[];
  /** Passive filler to reject when substance is required ("wait and see"). */
  fillerCues: string[];
  /**
   * Markers of a positive, substantive move ("I propose", "criterion", "let's
   * decide"). Used to require real content, not merely the absence of filler.
   */
  substanceCues: string[];
}

function includesAny(text: string, needles: string[]): boolean {
  const lower = text.toLowerCase();
  return needles.some((n) => n.length > 0 && lower.includes(n.toLowerCase()));
}

/**
 * Whole-word containment for ASCII terms (so a secret "art" does not match
 * "start"); falls back to substring for terms with non-ASCII characters (e.g.
 * CJK, where word boundaries do not apply).
 */
function containsTerm(text: string, term: string): boolean {
  if (term.length === 0) return false;
  if (/^[\x20-\x7e]+$/.test(term)) {
    return new RegExp(`(?<![A-Za-z0-9])${escapeRegExp(term)}(?![A-Za-z0-9])`, "i").test(text);
  }
  return text.toLowerCase().includes(term.toLowerCase());
}

const GROUNDING_STOPWORDS = new Set([
  "the", "a", "an", "is", "are", "was", "were", "to", "of", "and", "or", "it",
  "that", "this", "we", "i", "he", "she", "they", "for", "in", "on", "as", "so",
  "but", "with", "his", "her", "their", "them", "at", "by", "be", "been", "not",
  "no", "do", "did", "does", "has", "have", "had", "will", "would", "should"
]);

/** Content words of a text, minus stopwords and any excluded tokens (the entity). */
function contentTokens(text: string, exclude: Set<string>): string[] {
  return text
    .toLowerCase()
    .split(/[^\p{L}\p{N}]+/u)
    .filter((w) => w.length > 2 && !GROUNDING_STOPWORDS.has(w) && !exclude.has(w));
}

/**
 * Is the action the output attributes to `entity` corroborated by the facts?
 * Heuristic: some fact must mention the entity AND share a non-entity content
 * word with what the output says about that entity. This catches both unknown
 * entities (no fact mentions them) and content-divergent fabrications (the
 * entity is known, but the asserted action overlaps nothing the facts record).
 *
 * Known limitation: it cannot catch a paraphrastic action-swap that reuses a
 * shared noun ("Bob reported X approved" vs the fact "Bob asked about X"). For
 * that, add an entailment/NLI check in production.
 */
function actionGrounded(facts: string[], entity: string, output: string): boolean {
  const entityLower = entity.toLowerCase();
  const entityFacts = facts.filter((f) => f.toLowerCase().includes(entityLower));
  if (entityFacts.length === 0) return false;
  const exclude = new Set(entityLower.split(/[^\p{L}\p{N}]+/u).filter(Boolean));
  const claimWords = new Set(
    contentTokens(
      output.split(/(?<=[.!?。！？])/).filter((s) => s.toLowerCase().includes(entityLower)).join(" "),
      exclude
    )
  );
  if (claimWords.size === 0) return true; // nothing assertable to check
  return entityFacts.some((f) => contentTokens(f, exclude).some((w) => claimWords.has(w)));
}

/**
 * invented_reference — output narrates an entity acting, but that action is not
 * corroborated by the visible facts. The highest-value check: it catches the
 * model treating its own imagination as shared history. Grounding is checked at
 * the action level (see `actionGrounded`), so it also flags an invented action
 * attributed to an entity that the facts mention only for an unrelated reason —
 * not just fully-unknown entities. See `actionGrounded` for the residual limit.
 */
export function groundedReferences(lexicon: Lexicon): Validator {
  return ({ output, visibleFacts, entities }) => {
    for (const entity of entities) {
      if (!containsTerm(output, entity)) continue;
      const narratesAction = lexicon.actionCues.some((cue) =>
        new RegExp(`${escapeRegExp(entity)}[^.!?。！？]{0,24}${escapeRegExp(cue)}`, "i").test(output) ||
        new RegExp(`${escapeRegExp(cue)}[^.!?。！？]{0,24}${escapeRegExp(entity)}`, "i").test(output)
      );
      if (narratesAction && !actionGrounded(visibleFacts, entity, output)) {
        return {
          code: "invented_reference",
          message: `Output attributes an action to "${entity}" that the visible context does not support.`,
          revisionHint: `Do not reference "${entity}" having said or done anything that is not in the established facts. Speak only from what is actually recorded.`
        };
      }
    }
    return null;
  };
}

/**
 * boundary_leak — output exposes something the plan marked as must-not-reveal.
 */
export const noBoundaryLeak: Validator = ({ output, plan }) => {
  for (const secret of plan.mustNotReveal) {
    if (containsTerm(output, secret)) {
      return {
        code: "boundary_leak",
        message: `Output reveals protected information: "${secret}".`,
        revisionHint: `Remove any reference to "${secret}". It must stay hidden in this response.`
      };
    }
  }
  return null;
};

/**
 * passive_filler — the output must carry real content when the turn demands it.
 * Two scopes, to require substance without over-rejecting ordinary warm lines:
 *   - Cold opening: require a *positive* signal (a stance OR a substantive move
 *     such as a proposal/criterion/named question). An opening with neither is
 *     rejected even if it contains no obvious filler words.
 *   - Warm forward-move: reject only the clear stall — filler present with no
 *     stance or substance to carry it.
 * This fixes the double-negative gap where a content-free non-filler line ("nice
 * weather") slipped through a forced opening.
 */
export function hasForwardSubstance(lexicon: Lexicon): Validator {
  return ({ output, plan }) => {
    if (!plan.requiresForwardMove && !plan.isColdContext) return null;

    const isFiller = includesAny(output, lexicon.fillerCues);
    const hasStance = includesAny(output, lexicon.stanceCues);
    const hasSubstance = includesAny(output, lexicon.substanceCues);
    const carriesContent = hasStance || hasSubstance;

    const fails = plan.isColdContext ? !carriesContent : isFiller && !carriesContent;
    if (fails) {
      return {
        code: "passive_filler",
        message: "Output does not carry a concrete position or substantive move.",
        revisionHint: plan.isColdContext
          ? "Open with a concrete proposal, criterion, or named question instead of waiting to see how things develop."
          : "State a committed position plainly. Do not end on a question or a wait-and-see note."
      };
    }
    return null;
  };
}

/**
 * repetition — output merely repeats an angle already used by others. Pass the
 * prior reads (compact strings) to enable this check; skip it otherwise.
 */
export function notRepetitive(priorAngles: string[]): Validator {
  const normalized = priorAngles.map((a) => a.trim().toLowerCase()).filter(Boolean);
  return ({ output }) => {
    const text = output.trim().toLowerCase();
    if (normalized.some((angle) => angle.length > 8 && text.includes(angle))) {
      return {
        code: "repetition",
        message: "Output repeats an angle already stated by another actor.",
        revisionHint: "Add a distinct consequence, counterpoint, or new candidate instead of restating an angle already on the table."
      };
    }
    return null;
  };
}

/** Run every validator; return all violations (empty array == accepted). */
export function runValidators(ctx: ValidationContext, validators: Validator[]): Violation[] {
  const out: Violation[] = [];
  for (const validate of validators) {
    const v = validate(ctx);
    if (v) out.push(v);
  }
  return out;
}

export function escapeRegExp(text: string): string {
  return text.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}
