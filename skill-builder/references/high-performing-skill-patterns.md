# High-Performing Skill Patterns

Use this reference when creating a complex skill, improving a weak skill, or adapting good ideas from another skill collection. The goal is to turn a skill from a reminder list into an operational guide that changes Codex's behavior.

## Contents

- [Quick Diagnostic](#quick-diagnostic)
- [Pattern 1: Philosophy First](#pattern-1-philosophy-first)
- [Pattern 2: Discovery Before Generation](#pattern-2-discovery-before-generation)
- [Pattern 3: Reference Map Table](#pattern-3-reference-map-table)
- [Pattern 4: Contracts and Calibration](#pattern-4-contracts-and-calibration)
- [Pattern 5: Capabilities and Deliverables](#pattern-5-capabilities-and-deliverables)
- [Pattern 6: Anti-Patterns With Replacement](#pattern-6-anti-patterns-with-replacement)
- [Pattern 7: Variation Guidance](#pattern-7-variation-guidance)
- [Pattern 8: Conditional Questions](#pattern-8-conditional-questions)
- [Pattern 9: Scripts as Productized Workflow](#pattern-9-scripts-as-productized-workflow)
- [Pattern 10: Framework-Native Guidance](#pattern-10-framework-native-guidance)
- [Pattern 11: Verification Matched to Failure Modes](#pattern-11-verification-matched-to-failure-modes)
- [Final Checklist](#final-checklist)

## Quick Diagnostic

A skill is probably underpowered if it:

- Lists facts but does not say how to decide
- Starts producing output before inspecting the user's artifact or codebase
- Has no anti-patterns for common bad outputs
- Has no verification loop
- Uses one template for cases that need context-specific variation
- Hides detailed references without telling Codex when to read them

## Pattern 1: Philosophy First

Add a short domain philosophy when judgment matters.

Good shape:

```markdown
## Operating Model

The purpose of this work is [real objective], not [common proxy].

Prioritize:
1. [First priority]
2. [Second priority]
3. [Third priority]

Before acting, answer:
- [Question that changes the approach]
- [Question that prevents generic output]
```

Use for design, content, SEO, analysis, architecture, games, agents, data work, and any workflow where a rigid recipe is insufficient.

## Pattern 2: Discovery Before Generation

For codebase-aware or artifact-aware skills, make discovery step 1. Be specific about what to inspect.

Examples:

```markdown
## Workflow

### 1. Discover Existing State

- Identify the framework and routing pattern.
- Find current metadata, styles, assets, and config.
- Extract brand colors, fonts, icons, and repeated component patterns.
- Summarize missing pieces before editing.
```

If the discovery can be automated, include a script in `scripts/` or exact commands in SKILL.md.

## Pattern 3: Reference Map Table

When there are multiple reference files, include a table near the top of SKILL.md.

```markdown
## Reference Files

| Topic | File | Use When |
|-------|------|----------|
| Audit checklist | [audit.md](references/audit.md) | Reviewing an existing project |
| Frameworks | [frameworks.md](references/frameworks.md) | Implementing in a specific framework |
| Schemas | [schemas.md](references/schemas.md) | Writing structured data |
```

Keep references one hop away from SKILL.md. Avoid a maze of references linking to references.

## Pattern 4: Contracts and Calibration

Fragile domains need invariants before implementation. Write down the contract and force a small calibration pass.

Use for:

- Coordinate systems, units, axes, anchors, and dimensions
- API version assumptions
- Database ownership and schema constraints
- State-machine transitions
- File naming, output formats, and compatibility boundaries

Good shape:

```markdown
## Contract

- Input format:
- Output format:
- Required dimensions:
- Naming convention:
- State transition rule:

## Calibration

1. Run the smallest representative case.
2. Print or inspect key invariants.
3. Lock constants before scaling up.
```

## Pattern 5: Capabilities and Deliverables

Make the skill's value tangible before the detailed workflow.

Good shape:

```markdown
## Capabilities

- Analyze [artifact] and extract [signal]
- Generate [asset/report/code]
- Integrate output into [framework/location]

## Deliverables

- [file or artifact]
- [summary or decision]
- [verification output]
```

Use this for production-ready skills, generated assets, reports, codebase edits, or any skill where the user should know what concrete result to expect.

## Pattern 6: Anti-Patterns With Replacement

Anti-patterns work best when they include the failure reason and the better move.

```markdown
## Anti-Patterns

**Generic template output**

Bad: Same layout, same colors, same phrasing for every case.

Why bad: It ignores the actual context and produces indistinguishable output.

Better: Extract the relevant page type, audience, brand, or framework first, then choose a matching pattern.
```

Use anti-patterns to block the exact mistakes the agent keeps making.

## Pattern 7: Variation Guidance

A strong skill tells Codex what should vary. This prevents repetitive, template-shaped output.

Good dimensions:

- Framework or platform
- Audience skill level
- Page, route, or content type
- Risk level and blast radius
- Brand tone or visual system
- Performance, accessibility, security, or compatibility constraints

Good shape:

```markdown
## Variation Guidance

Vary based on:
- Page type: landing, article, product, docs
- Framework: Next.js, Astro, static HTML
- Audience: beginner, expert, buyer, operator

Avoid converging on:
- One title format for every page
- The same visual layout for every asset
- Generic wording that could fit any project
```

## Pattern 8: Conditional Questions

Ask only when the missing answer changes the result materially.

Good question guidance:

- Ask 1 to 3 questions first, not a survey.
- Ask about constraints, audience, success criteria, and the user's preferred tradeoff.
- Skip questions when the user already provided enough context or explicitly asks for a quick pass.
- For multi-choice tools, make options mutually exclusive and explain the tradeoff.

## Pattern 9: Scripts as Productized Workflow

Add scripts when repeated mechanics would otherwise be rewritten.

Good script candidates:

- Analyze a project and output structured findings
- Generate a deterministic asset suite
- Convert or validate files
- Create a manifest, sitemap, report, or index
- Preview or screenshot outputs

Script instructions should include:

- The exact command
- Expected inputs and outputs
- Where generated files go
- What validation to run afterward

## Pattern 10: Framework-Native Guidance

When a task spans frameworks, keep the core workflow in SKILL.md and put framework details in references.

Good SKILL.md content:

- How to detect the framework
- Which reference to read
- The common priority order
- The verification checks shared by all frameworks

Good reference content:

- Framework-specific snippets
- File locations
- Configuration examples
- Pitfalls and compatibility notes

## Pattern 11: Verification Matched to Failure Modes

Do not end a skill at generation. Tell Codex how to know the output worked.

Examples:

- Visual work: screenshot, compare at target sizes, check text fit
- Web metadata: inspect rendered head tags, validate sitemap and robots.txt
- 3D work: verify nonblank canvas, frame bounds, camera, color space, controls
- Code changes: run tests, typecheck, lint, or focused smoke tests
- Data transformations: validate schema, row counts, checksums, or sample records

## Final Checklist

Before shipping a skill, confirm:

- The description contains real trigger contexts.
- SKILL.md teaches a mental model and a workflow.
- The what, why, capabilities, and deliverables are clear enough to evaluate success.
- Required discovery happens before generation.
- Optional references are listed with "Use When" guidance.
- Scripts are tested or clearly marked as examples.
- Anti-patterns block common weak outputs.
- Variation guidance prevents generic convergence.
- Verification steps match the skill's real failure modes.
- Unsupported frontmatter from other ecosystems has not been copied blindly.
