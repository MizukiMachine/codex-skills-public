# Information-Boundary Design (the precondition layer)

The design-time work that produces a per-viewer projection of a single
authoritative state, so each actor's context is *constructed* from only what it
may know. This is what makes the control loop's `allowedFacts` trustworthy — the
censor can only enforce grounding if the context was built from an allowlist in
the first place. Pairs with `plan-object.md` (the projection feeds `allowedFacts`)
and `architecture.md` (where the boundary sits in the app).

## Contents

- [Why a boundary, not "be careful"](#why-a-boundary-not-be-careful)
- [Map actors and scopes](#map-actors-and-scopes)
- [Classify information (sensitivity lattice)](#classify-information-sensitivity-lattice)
- [Build an access matrix](#build-an-access-matrix)
- [Isolate generation contexts](#isolate-generation-contexts)
- [Split agent tasks](#split-agent-tasks)
- [Choose output contracts by risk](#choose-output-contracts-by-risk)
- [Construct prompts from rendered context](#construct-prompts-from-rendered-context)
- [Untrusted input & indirect prompt injection](#untrusted-input--indirect-prompt-injection)
- [Redact by view (egress)](#redact-by-view-egress)
- [RAG pattern](#rag-pattern)
- [Simulation / game pattern](#simulation--game-pattern)
- [Prompt boundary template](#prompt-boundary-template)
- [Boundary tests](#boundary-tests)

## Why a boundary, not "be careful"

Asking one LLM to hold the entire truth and "be careful" fails because a secret
in the context leaks under pressure, probabilistically, over enough turns. The
robust design is a **per-viewer projection** of a single authoritative state:

- one source-of-truth state on the server;
- a redaction/projection function per viewer that strips anything that viewer may
  not see (other actors' secret roles, private results, hidden targets, tool
  traces, retrieval internals);
- generation, and any UI for that viewer, runs only on the projected slice in a
  fresh/scoped context that has not seen the hidden state.

This is the same idea as fog-of-war in an authoritative multiplayer server, and
it doubles as the source of the plan's `allowedFacts`. Build the boundary first;
the fact whitelist falls out of it. When auditing an app that "leaks", grep the
**context builder**, not the prompt text — the fix is usually that secret state
reaches a context it should never enter.

## Map actors and scopes

List every actor: users, agents, tools, documents, memories, system processes,
external viewers. For each, define:

- role, goal, what it is trying to optimize;
- allowed inputs, forbidden inputs;
- allowed outputs, downstream consumers.

Cover the cases the naive design forgets:

- **Games/sims:** hidden roles, factions, private memories, public history,
  private chat, spectator views.
- **RAG/enterprise:** user auth, document ACLs, retrieval indexes, citations,
  internal notes, tool traces, redaction rules.

## Classify information (sensitivity lattice)

Use a small lattice unless the codebase already has one:

```text
public        visible to end users / all participants
user_provided visible to the originating user and authorized processors
confidential  role-, tenant-, session-, or document-permission scoped
secret        credentials, system prompts, hidden chain/tool traces
forbidden     must never enter prompts or user-facing output
```

Treat retrieval results, generated summaries, memories, and diagnostics as data
with their own sensitivity, not as harmless text.

## Build an access matrix

Create a table *before* writing prompts:

```text
actor | public history | private memory | retrieved docs | hidden state | tool traces | may reveal
```

Prefer allowlists over denylists — enumerating what to hide always misses a case.
Render role-visible context from code, not from prompt prose alone.

## Isolate generation contexts

Do not generate public or actor-limited free text from a model invocation that has
already seen hidden, forbidden, or cross-actor private state. The orchestrator may
hold full state; the speaker, answerer, or downstream agent should receive only a
projection.

Acceptable isolation mechanisms:

- **Fresh model call** — build messages from the projection only.
- **Restricted sub-agent** — launch with the projected context and scoped tools.
- **Scoped worker/process** — accept only projected context, legal IDs, and the
  output contract.

The boundary must include tools and data access, not just prompt text. A
sub-agent is not isolated if it can read unrestricted files, databases, RAG
indexes, memories, logs, or tool traces. If the current invocation has already
read secret state, use it only as the orchestrator that builds the projection and
validates the result.

## Split agent tasks

Avoid a single "mega prompt". Use narrow tasks, each with its own context and
contract:

- **Public response / speech** — natural language only, visible context only.
- **Internal decision** — structured output (`targetId`, `docIds`, `action`,
  `reasonKind`).
- **Retrieval planning** — query specs, filters, ACL constraints.
- **Verification** — citation coverage, policy checks, contradiction checks,
  leakage checks.
- **Redaction** — remove or mask fields before display or before sending to
  another actor.
- **Summary** — public-safe summary from public-safe structured data.

## Choose output contracts by risk

- Free text only where naturalness is the product value.
- JSON / typed schemas for actions, target selection, retrieval plans,
  authorization decisions, tool calls, and safety gates.
- Symbolic reason codes when user-facing text can be generated deterministically.
- Never let unconstrained prose directly drive irreversible actions.

This maps onto the control loop's **two channels** (see `plan-object.md`): the
public channel is validated by prose validators; the decision channel by schema
parse + a legal-choice check.

## Construct prompts from rendered context

The prompt builder should receive already-authorized data. A good context
includes: actor identity/role/objective/style, current phase/task, allowed public
history or retrieved evidence, allowed private memory, legal IDs/document IDs for
target selection, and the output contract + refusal/uncertainty rules.

For public or actor-limited natural language, pass the rendered context to an
isolated generator: a fresh API call, restricted sub-agent, or scoped worker. Do
not reuse an all-knowing conversation that saw raw state and then ask it to
"ignore" hidden fields.

The prompt must **not** contain: API keys/credentials/env values; raw hidden
state for actors that cannot see it; system-only instructions disguised as
user-visible facts; documents outside the user's permissions; tool traces the
answerer must not cite or reveal.

## Untrusted input & indirect prompt injection

Treat user input, retrieved documents, emails, tickets, chat logs, and database
text as **untrusted data**. They may contain instructions to ignore system rules,
reveal secrets, alter permissions, change roles, or cite unavailable sources. The
prompt must clearly mark them as evidence/content, **not** instructions. Detect
or neutralize document text that asks the model to bypass access checks or follow
instructions outside the user's request — flag it, do not obey it.

## Redact by view (egress)

Redaction is a product layer, not a prompt instruction:

- store authoritative events/state with full data on the server;
- generate view-specific snapshots for user, admin, participant, spectator, or
  agent;
- delete or mask forbidden fields before they reach the client or the next agent;
- preserve enough metadata for UI continuity without exposing secrets.

There are two redaction points: **ingress** (building the actor's context) and
**egress** (before output reaches a client or downstream agent). Both matter.

## RAG pattern

```text
User request
  -> Auth/tenant scope
  -> Planner: structured retrieval plan with filters
  -> Retriever: ACL-filtered documents
  -> Reader/Answerer: isolated generation with authorized snippets + citation IDs
  -> Verifier: citation coverage and unsupported-claim check
  -> Redactor: remove internal fields
  -> User-facing answer
```

Hard rules:

- Apply ACL filtering **before** generation, not after.
- Give the answerer document IDs and excerpts in a fresh/scoped generation
  context, not raw unrestricted corpora or an all-knowing orchestrator context.
- Treat retrieved documents as untrusted evidence, never as system instructions.
- Ignore/flag document text that asks the model to reveal secrets, bypass access
  checks, change roles, or act outside the user's request.
- If evidence is missing, say so or ask a follow-up; do not infer from hidden
  knowledge.
- Do not expose retrieval scores, internal ranking notes, private user
  attributes, or tool traces unless they are explicitly part of the product.

The control-loop counterpart: `allowedFacts` = the retrieved chunks; the censor's
**claim-traces-to-source** validator rejects any factual sentence not overlapping
a chunk (see `validators.md`).

## Simulation / game pattern

```text
Authoritative state
  -> actor-specific prompt context
  -> isolated public speech or private speech generator
  -> metadata extraction / action decision
  -> rule engine validation
  -> redacted event stream per viewer
```

Hard rules:

- Give each character only role-visible secrets.
- Use a fresh/scoped generation context for each actor's public or private speech.
- Keep public speech simple and natural; infer metadata from the displayed text
  when possible (the metadata round-trip in `validators.md`).
- Use structured outputs for votes, targets, actions, and binary decisions.
- Validate actions against current legal targets.
- Do not feed private warm-up, hidden planning, or speculative generations back
  as public evidence.

## Prompt boundary template

```text
You are {actor_name}.
Role: {role}   Goal: {goal}   Task: {task}

Visible information (you may treat these as established fact, nothing else):
{authorized_public_context}

Private information visible only to you (never reveal in public output):
{authorized_private_context}

Legal options:
{legal_ids_or_docs}

Rules:
- Use only the information shown above. Anything not here is unknown — do not invent it.
- Do not reference events, statements, results, or documents not present above.
- Do not mention private/system/forbidden information in public output.
- If evidence is insufficient, say what is missing or choose the safe fallback.

Output:
{free_text_or_json_schema}
```

## Boundary tests

Add narrow tests around the boundaries:

- An unauthorized document never appears in prompt context.
- An agent cannot select an illegal target/document/action ID.
- A public/actor-limited generator cannot access unrestricted tools, memory,
  filesystem, RAG indexes, logs, or hidden state.
- Public output does not expose hidden state.
- Viewer-specific redaction removes private event fields.
- RAG answer citations are drawn only from authorized retrieval results.
- Fallbacks continue the workflow without privileged data.

These are the boundary half of the Verification section in `SKILL.md`; the
control-loop half lives in `failure-modes.md` and `validators.md`.
