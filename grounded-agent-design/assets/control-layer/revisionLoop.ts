// Correct layer — the Direct -> Censor -> Correct loop.
//
// A stochastic generator will sometimes violate the plan. The control layer does
// not discard-and-hope; it feeds back the *specific* violated invariant as a
// revision hint and regenerates, a bounded number of times, then falls back to a
// safe deterministic output so the system never hangs on a stubborn model.
//
// `generate` and `validate` are injected, so this harness is fully
// domain-agnostic. `T` is your output type (a string, a structured speech, a
// decision object — anything).

import type { Violation } from "./validators";

export interface RevisionLoopOptions<T> {
  /**
   * Produce a candidate. On retries, `revisionHint` is the concatenated hints
   * from the previous attempt's violations — weave it into your prompt.
   */
  generate: (revisionHint: string | undefined, attempt: number) => Promise<T>;
  /** Return all violations for a candidate; empty array means accept. */
  validate: (candidate: T) => Violation[];
  /**
   * Deterministic safe output used when every attempt fails. This is what keeps
   * the loop bounded and the product responsive. Make it dull but always valid.
   */
  fallback: (lastCandidate: T | null, violations: Violation[]) => T;
  /** Total attempts including the first. Default 3. Keep small for latency. */
  maxAttempts?: number;
  /** Diagnostics hook; mirror these into your telemetry. */
  onAttempt?: (info: {
    attempt: number;
    accepted: boolean;
    violations: Violation[];
    usedFallback: boolean;
  }) => void;
}

export interface RevisionLoopResult<T> {
  value: T;
  attempts: number;
  accepted: boolean;
  usedFallback: boolean;
}

function combineHints(violations: Violation[]): string | undefined {
  if (violations.length === 0) return undefined;
  return violations.map((v) => v.revisionHint).join(" ");
}

export async function runRevisionLoop<T>(options: RevisionLoopOptions<T>): Promise<RevisionLoopResult<T>> {
  const maxAttempts = Math.max(1, options.maxAttempts ?? 3);
  let lastCandidate: T | null = null;
  let lastViolations: Violation[] = [];
  let hint: string | undefined;

  for (let attempt = 1; attempt <= maxAttempts; attempt += 1) {
    const candidate = await options.generate(hint, attempt);
    lastCandidate = candidate;
    const violations = options.validate(candidate);
    const accepted = violations.length === 0;

    // Emit per attempt, except the final failing attempt — that one is reported
    // by the fallback emit below, so each attempt produces exactly one event.
    if (accepted || attempt < maxAttempts) {
      options.onAttempt?.({ attempt, accepted, violations, usedFallback: false });
    }

    if (accepted) {
      return { value: candidate, attempts: attempt, accepted: true, usedFallback: false };
    }

    lastViolations = violations;
    hint = combineHints(violations);
  }

  // Every attempt failed — return the safe deterministic output.
  const value = options.fallback(lastCandidate, lastViolations);
  options.onAttempt?.({ attempt: maxAttempts, accepted: false, violations: lastViolations, usedFallback: true });
  return { value, attempts: maxAttempts, accepted: false, usedFallback: true };
}
