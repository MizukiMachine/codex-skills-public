# Prompt Design For AI-Generated OG Images

Use this reference when selecting a style, writing a `--theme-hint`, or replacing the preset with `--custom-prompt`.

## Prompt Contract

Every prompt must preserve these constraints:

- No text, words, letters, numbers, UI labels, watermarks, or fake logos in the generated background.
- Wide landscape composition that can be center-cropped to 1200x630.
- Quiet upper-left and central regions for deterministic text overlay.
- Brand colors used as palette guidance, not as exact token reproduction.
- Clear visual theme tied to the route, page type, and audience.

If a prompt asks for a realistic product, logo, person, or UI that the model has not been given as a reference, treat the result as illustrative rather than exact.

## Style Presets

These presets match the script's `--style` choices.

| Style | Use For | Avoid When |
|-------|---------|------------|
| `tech` | Developer tools, APIs, infrastructure, data, SaaS engineering posts | The brand is warm, editorial, or consumer-focused |
| `nature` | Sustainability, wellness, outdoor, climate, calm product narratives | The page needs operational or enterprise seriousness |
| `warm` | Community, education, coaching, people-centered services | The product needs a restrained B2B tone |
| `abstract` | Creative, portfolio, thought-leadership, conceptual articles | The topic needs concrete product evidence |
| `corporate` | B2B, professional services, company pages, trust-focused landing pages | The project already has a playful or highly visual brand |
| `dark` | Security, developer tools, AI, data, cinematic launch pages | The site uses a light or minimal identity |
| `neon` | Events, games, music, cyberpunk or retro-futuristic themes | Serious corporate, healthcare, finance, or public-sector pages |

Prefer the closest existing style plus `--theme-hint` before reaching for a full `--custom-prompt`.

## Page-Type Guidance

`--page-type` changes the prompt's role:

| Page Type | Prompt Focus |
|-----------|--------------|
| `landing` | Product or service category, audience, offer, and first impression |
| `article` | Topic metaphor, editorial feel, category, or technical domain |
| `product` | Capability, workflow, product surface, or customer outcome |
| `documentation` | Structured technical clarity, diagrams, reference texture, restrained accents |
| `about` | Identity, mission, team, place, or company values |
| `general` | Broad page-level visual theme when no stronger type is known |

## Theme Hints

Use `--theme-hint` for project-specific context that should influence imagery without overriding the whole prompt.

Good theme hints:

```text
healthcare scheduling SaaS, calm clinical trust, no medical symbols
privacy-first analytics dashboard, quiet enterprise tone
Japanese travel guide for rural inns, editorial photography mood
open-source database tooling, practical developer documentation
```

Weak theme hints:

```text
make it cool
modern gradient
nice background
```

## Custom Prompt Pattern

When presets are not enough, use this shape:

```text
A wide landscape illustration for [page type and audience].
Show [specific visual subject or metaphor] in [style and medium].
Use [brand colors or palette] with [mood].
Keep the upper-left third and center visually quiet for later text overlay.
No text, words, letters, numbers, watermarks, logos, or typography.
The image should remain readable as a small social-media thumbnail.
```

Do not include the final title or description in the image prompt. The generator overlays that text with Pillow.
If `--brand-colors` is also supplied, the script appends palette guidance after the custom prompt.

## Brand Color Injection

Use two or three brand colors at most:

```bash
--brand-colors "#2563eb,#14b8a6,#f97316"
```

If the source brand uses many colors, choose the primary action color, a secondary accent, and one neutral or support color. Avoid forcing a one-note palette when the site's visual identity is richer.

## Iteration Signals

Regenerate or revise the prompt when:

- The background contains text-like marks, fake labels, or logo shapes.
- The generated image competes with the text panel.
- The style could belong to any unrelated site.
- The color palette ignores the source project.
- The image is too literal for an article or too abstract for a product page.
- Important detail lands under the overlay area.

Use `--quality low` for prompt exploration and move to `medium` or `high` after the visual direction is acceptable.
