// Ready-made cue-word lexicons. Detection patterns are configuration, not core
// logic: swap or extend these per language and domain.
//
// The actual word lists now live in YAML so they can be edited WITHOUT touching
// code — see lexicons/en.yaml and lexicons/ja.yaml. These exports just load
// those files (Node only; see loadLexicon.ts). The YAML files are the single
// source of truth, so there is no list to keep in sync here.
//
// In a browser (no filesystem), build a Lexicon object literal instead, or fetch
// the YAML text and pass it to parseLexiconYaml() from ./loadLexicon.

import type { Lexicon } from "./validators";
import { loadLexicon } from "./loadLexicon";

export const englishLexicon: Lexicon = loadLexicon("en");
export const japaneseLexicon: Lexicon = loadLexicon("ja");
