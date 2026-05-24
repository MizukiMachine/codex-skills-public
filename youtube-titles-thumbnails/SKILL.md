---
name: youtube-titles-thumbnails
description: "視聴者からの信頼を保ちながら、CTR向上を狙うYouTubeタイトル、サムネイル文言、タイトルとサムネの組み合わせ、hook、packaging strategyを作成または最適化する。YouTubeタイトル案、サムネコピー、A/B test案、transcriptや動画企画の分析、既存タイトル/サムネ改善、tutorial/analysis/story/comparison/review/education/tech/creator strategy向けのYouTube packaging助言を求められたときに使う。"
---

# YouTube Titles & Thumbnails

## Purpose

Use this skill to package a YouTube video so the title and thumbnail create a clear reason to click without misrepresenting the content. Produce title-thumbnail pairs, not isolated titles, and explain the strategic tradeoffs behind the strongest options.

## Operating Model

Treat YouTube packaging as a promise. The job is to create curiosity and value while keeping retention and trust intact.

Use this equation:

```text
Thumbnail hook + title promise = curiosity gap worth clicking
```

Prioritize:

1. Authentic promise: the video must deliver what the packaging suggests
2. Complementarity: thumbnail and title reinforce each other without duplicating
3. Specificity: concrete topic, audience, outcome, tension, or differentiator
4. Curiosity gap: withhold the answer, not the value
5. Audience fit: match sophistication, niche language, and channel tone
6. Search/discovery only when it matters for the request or niche

## Contracts

- Never imply outcomes, drama, proof, money, danger, controversy, or personal stakes that the video does not actually contain.
- Treat click-through rate as incomplete on its own. Prefer packaging likely to attract the right viewer and support retention, satisfaction, and watch time.
- Keep generated thumbnail text separate from visual direction. If the user asks for a thumbnail concept, provide a concise visual brief in addition to text.
- For YouTube Studio thumbnail testing, design up to three materially different thumbnail variants, not three near-identical wording changes. Treat the test as a watch-time and viewer-fit experiment, not just a CTR race.
- For Shorts or vertical videos, do not assume long-form thumbnail behavior. Note when the packaging needs a Shorts-specific approach.
- Check policy risk for thumbnails that use shock, gore, sexualized imagery, vulgar language, misleading imagery, or fake platform UI.

## Capabilities and Deliverables

Use this skill to:

- Generate title-thumbnail pairs from a transcript, outline, rough idea, or existing title
- Rewrite weak title/thumbnail packaging while preserving the real video promise
- Produce A/B or YouTube Studio Test & Compare variants with distinct hypotheses
- Create thumbnail text plus an optional visual concept brief
- Diagnose why existing packaging feels generic, misleading, redundant, too search-heavy, or too vague
- Adapt packaging for long-form, Shorts, podcasts, tutorials, reviews, comparisons, and creator commentary

Expected deliverables may include:

- Ranked title-thumbnail pairs with angle, target viewer, and tradeoff
- A top pick with the reason it is strongest
- A/B test variants and what each variant is testing
- A concise thumbnail visual brief: subject, expression/action, composition, text, and contrast cue
- Assumptions and missing information that would improve the next pass

## Before Generating

Extract or infer:

- Core value: the single most valuable insight, outcome, story turn, or decision point
- Target viewer: beginner, intermediate, advanced, buyer, fan, skeptic, or broad audience
- Content type: tutorial, analysis/opinion, story/experience, comparison, review, reaction, documentary, list, or update
- Emotional hook: curiosity, frustration relief, ambition, fear of missing out, identity, controversy, or relief
- Differentiator: unique angle, better depth, simpler explanation, fresh data, contrarian stance, personal access, or proof
- Constraints: must-use keyword, channel tone, title length preference, existing brand phrases, things to avoid

Ask at most one to three concise questions only when missing information would materially change the output. If the user asks for quick ideas or provides enough context, proceed with stated assumptions.

Good questions:

- What type of video is this and who is the target viewer?
- Should the packaging favor search discovery, click-through curiosity, or a balance?
- What is the one thing this video says that similar videos do not?

## Reference Files

| Topic | File | Use When |
|-------|------|----------|
| Pattern library | [pattern-library.md](references/pattern-library.md) | Need title structures, thumbnail copy patterns, content-type adaptations, scoring rules, or before/after examples |

## Workflow

1. Analyze the material.

   Read the transcript, summary, notes, existing title, or video idea. Identify the actual payoff and the best tension. Do not package the video around a claim the content cannot deliver.

2. Choose the packaging mode.

   | Mode | Use When | Output Bias |
   |------|----------|-------------|
   | Long-form standard | Most videos with a custom thumbnail and title | Full title-thumbnail pair |
   | Test & Compare | User wants variants for YouTube Studio testing | Up to three distinct thumbnail hypotheses |
   | Shorts | Vertical or Shorts-first content | Hook, first-frame/title framing, minimal thumbnail assumptions |
   | Podcast | Podcast episode or playlist packaging | Clear topic, guest/entity, 1:1 art note if relevant |
   | Existing-package rewrite | User provides current title/thumbnail | Diagnose before rewriting |

3. Choose the packaging strategy.

   Select one primary angle:

   | Strategy | Use When | Bias |
   |----------|----------|------|
   | Search-first | Tutorials, evergreen guides, beginner content, keyword-driven niches | Front-load topic and outcome |
   | CTR-first | Opinion, story, revelation, crowded topics, returning audience | Lead with tension or curiosity |
   | Trust-first | Sensitive topics, expert audiences, brand channels | Lead with specificity and accuracy |
   | Debate-first | Contrarian analysis, comparisons, hot takes | Lead with a clear stance |
   | Utility-first | Practical how-to, productivity, coding, tools | Lead with concrete result |

4. Generate distinct title-thumbnail pairs.

   Produce 5 to 10 options unless the user requests a different number. Each option should use a meaningfully different angle, not small wording variations.

5. Score and rank.

   Evaluate each pair for authenticity, clarity, curiosity, specificity, complementarity, and audience fit. Put the strongest option first.

6. Explain tradeoffs.

   Note why the top options work and when a different option might be better, such as SEO, a more provocative channel voice, or a safer brand tone.

7. Provide iteration hooks.

   Suggest what to test next: stronger keyword, bolder thumbnail, less redundancy, clearer audience signal, or a tighter curiosity gap.

## Output Shape

Use this default format when generating options:

```markdown
**Top Pick**
Title:
Thumbnail text:
Why it works:
Tradeoff:

**Options**
| # | Title | Thumbnail Text | Angle | Best For |
|---|-------|----------------|-------|----------|

**Notes**
- Assumptions:
- What to test:
- Avoid:
```

When the user asks for thumbnail concepts, add:

```markdown
**Thumbnail Brief**
- Visual subject:
- Expression/action:
- Composition:
- Text:
- Contrast cue:
- Policy risk:
```

For optimization of an existing title/thumbnail, use:

```markdown
**Diagnosis**
- Current issue:
- Missed opportunity:

**Rewrites**
| # | Title | Thumbnail Text | Change Made | Why |
|---|-------|----------------|-------------|-----|
```

## Quality Rules

Titles:

- Keep most titles around 40-70 characters when possible; stay under 100 unless the user explicitly wants long-form titles.
- Front-load the most important searchable or emotional words.
- Use neutral, conversational language. Avoid spammy all-caps, empty hype, and excessive punctuation.
- Include enough specificity that the title could not fit any video in the niche.
- Promise an outcome, insight, decision, or story payoff.

Thumbnail text:

- Use 2-5 words in most cases.
- Make it emotionally legible at a glance: subject, question, reveal, stance, or action.
- Avoid repeating the title unless the keyword is critical for search or brand consistency.
- Prefer short words and strong contrast in meaning, not word count.

Thumbnail execution notes:

- Default custom thumbnail spec should target 1280 x 720, 16:9, JPG/PNG/GIF, and under 2 MB for standard videos unless the user states another format.
- Keep text large and readable on mobile; avoid cluttered designs with too many focal points.
- Use the visual subject, expression/action, and text to communicate one idea.
- For podcast playlist artwork, account for square artwork when relevant.

Pairing:

- The thumbnail should create the visual hook; the title should complete the verbal promise.
- Neither element should reveal the full answer alone.
- The pair must point to the same topic and emotional frame.
- Strategic redundancy is acceptable only when a keyword is essential.

## Anti-Patterns

**Misleading clickbait**

Bad: Packaging implies drama, danger, income, failure, or proof the video does not contain.

Better: Create tension from a real mistake, tradeoff, lesson, or unanswered question.

**Generic tutorial phrasing**

Bad: "Python Tips and Tricks" or "How to Learn JavaScript."

Better: "3 Python Patterns That Make Code Self-Documenting" or "How to Learn JavaScript Without Tutorial Hell."

**Thumbnail repeats title**

Bad: Thumbnail "How to Learn Python"; title "How to Learn Python for Beginners."

Better: Thumbnail "Python Basics"; title "The 3 Concepts Beginners Actually Need."

**Hype without substance**

Bad: "This Changes Everything!!!"

Better: Name the real shift: "Why Experienced Developers Write Less Code."

**One favorite formula**

Bad: Every output uses "The Real Reason..." or "Nobody Talks About..."

Better: Vary by content type, audience, and promise.

**Optimizing only for CTR**

Bad: Pick the most provocative option even if it attracts the wrong viewers.

Better: Balance curiosity with expected retention and viewer satisfaction.

## Variation Guidance

Adapt by:

- Tutorial: clarity, outcome, searchable topic, beginner/intermediate signal
- Analysis/opinion: stance, hidden tradeoff, contrarian insight, timing
- Story/experience: personal turn, lesson, stakes, transformation
- Comparison/review: decision clarity, surprising winner, use-case split
- Expert audience: precise language, nuance, novelty, no beginner framing
- Beginner audience: plain language, confidence, "what matters" framing
- Brand-safe channel: credible language, lower hype, stronger specificity
- Provocative channel: sharper stance, still anchored to truth
- Shorts-first video: prioritize first-frame clarity and immediate hook over long-form thumbnail assumptions
- Test variant: vary the hypothesis, such as face/emotion vs product/result vs problem/tension

Avoid converging on:

- "The truth about..." for every idea
- "I tried X..." when the story is not personal
- Overusing "nobody" without a genuinely under-discussed point
- Titles that only optimize search and ignore why a human would click

## Verification

Before finalizing, check:

- The title and thumbnail describe the same video.
- The video can deliver the promised payoff.
- The strongest option has a clear reason to click within one glance.
- Thumbnail text is short enough to read on mobile.
- Titles are not all minor variants of one pattern.
- At least one option optimizes for search, one for curiosity, and one for trust when the request is broad.
- Test variants are genuinely different hypotheses, not synonym swaps.
- Any thumbnail concept avoids obvious policy and trust risks.
- Tradeoffs are explicit enough for the user to choose or A/B test.

If a transcript is long or messy, summarize the core value first, then generate packaging from that summary.
