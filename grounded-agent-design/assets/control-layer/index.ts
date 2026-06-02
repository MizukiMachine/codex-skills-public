// control-layer — a deterministic Direct -> Censor -> Correct wrapper around
// a stochastic generator (the run-time half of the grounded-agent-design skill).
// Copy this folder into your project and adapt:
//   1. plan.ts        — derive intents/allowedFacts/mustNotReveal from YOUR state
//   2. validators.ts  — supply a Lexicon for your language; add domain validators
//   3. revisionLoop.ts — wire generate()/validate()/fallback() and run it
//
// See lexicons.ts for ready-made English/Japanese cue words.

export * from "./plan";
export * from "./validators";
export * from "./revisionLoop";
export * from "./lexicons";
export * from "./loadLexicon";
