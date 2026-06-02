// Load a cue-word Lexicon from a YAML file, so the word lists can be edited
// without touching code (see lexicons/en.yaml, lexicons/ja.yaml).
//
// Dependency-free on purpose: this is a tiny reader for the *constrained* shape
// these lexicons use — top-level keys, each holding a list of strings:
//
//   actionCues:
//     - said
//     - "pointed out"   # quote values that contain spaces
//
// It is NOT a general YAML parser. If you outgrow this shape, swap in a real
// YAML library and keep loadLexicon's signature.
//
// Node-only (it reads the filesystem). In a browser, build a Lexicon object
// literal, or fetch the text and call parseLexiconYaml() on it.

import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, isAbsolute, join } from "node:path";
import type { Lexicon } from "./validators";

const REQUIRED_KEYS = ["actionCues", "stanceCues", "fillerCues", "substanceCues"] as const;

/** Strip a matching pair of surrounding quotes, if present. */
function unquote(s: string): string {
  if (s.length >= 2) {
    const first = s[0];
    const last = s[s.length - 1];
    if ((first === '"' && last === '"') || (first === "'" && last === "'")) {
      return s.slice(1, -1);
    }
  }
  return s;
}

/**
 * Parse the constrained "key:" / "  - value" YAML subset into string lists.
 * Blank lines and whole-line `#` comments are ignored. Throws on a line that is
 * neither a key, a list item, a comment, nor blank — so typos surface loudly
 * instead of silently dropping cue words.
 */
export function parseLexiconYaml(text: string): Record<string, string[]> {
  const out: Record<string, string[]> = {};
  let current: string | null = null;
  let lineNo = 0;
  for (const rawLine of text.split(/\r?\n/)) {
    lineNo += 1;
    const trimmed = rawLine.trim();
    if (trimmed === "" || trimmed.startsWith("#")) continue;

    const item = /^\s*-\s+(.*)$/.exec(rawLine);
    if (item) {
      if (current === null) {
        throw new Error(`lexicon parse error (line ${lineNo}): list item before any key.`);
      }
      out[current].push(unquote(item[1].trim()));
      continue;
    }

    const key = /^([A-Za-z0-9_]+):\s*$/.exec(rawLine);
    if (key) {
      current = key[1];
      if (!out[current]) out[current] = [];
      continue;
    }

    throw new Error(
      `lexicon parse error (line ${lineNo}): expected "key:" or "  - value", got: ${rawLine}`
    );
  }
  return out;
}

/** A bare name ("en"/"ja") resolves to lexicons/<name>.yaml next to this file. */
function resolveLexiconPath(nameOrPath: string): string {
  if (isAbsolute(nameOrPath)) return nameOrPath;
  if (nameOrPath.includes("/") || nameOrPath.endsWith(".yaml")) {
    return join(process.cwd(), nameOrPath);
  }
  const here = dirname(fileURLToPath(import.meta.url));
  return join(here, "lexicons", `${nameOrPath}.yaml`);
}

/**
 * Read a Lexicon from YAML. `name` is a bundled language ("en" / "ja") or a path
 * to your own .yaml file. Throws a clear error if a required list is missing.
 */
export function loadLexicon(name: string): Lexicon {
  const path = resolveLexiconPath(name);
  const parsed = parseLexiconYaml(readFileSync(path, "utf8"));
  for (const key of REQUIRED_KEYS) {
    if (!Array.isArray(parsed[key])) {
      throw new Error(
        `lexicon "${path}" is missing the "${key}:" list. Required keys: ${REQUIRED_KEYS.join(", ")}.`
      );
    }
  }
  return {
    actionCues: parsed.actionCues,
    stanceCues: parsed.stanceCues,
    fillerCues: parsed.fillerCues,
    substanceCues: parsed.substanceCues
  };
}
