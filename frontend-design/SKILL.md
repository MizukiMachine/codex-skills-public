---
name: frontend-design
description: Build, redesign, review, or polish production frontend interfaces with codebase-aware visual design. Use when Codex works on web components, pages, dashboards, SaaS tools, landing pages, apps, design-system UI, responsive layout, interaction polish, or visual QA, especially when the user asks for high-quality design, UI improvement, frontend implementation, or to avoid generic AI-looking aesthetics.
---

# Frontend Design

## Purpose

Use this skill to produce working frontend code that feels intentionally designed for its product, audience, and workflow. The goal is not decoration; it is a usable interface with a clear visual point of view, stable responsive behavior, accessible controls, and verified rendering.

## Operating Model

Great frontend design comes from context, hierarchy, and implementation integrity.

Prioritize:

1. User workflow and product purpose
2. Existing framework, design system, and code conventions
3. Clear visual hierarchy and information density suited to the domain
4. Responsive stability, accessibility, and interaction states
5. Distinctive details that support the concept without breaking usability
6. Browser verification with real screenshots or smoke tests

Before acting, answer:

- What is the user trying to accomplish on this screen?
- Is this an operational tool, marketing surface, portfolio, game, creative app, or content site?
- What framework, UI library, routing model, assets, fonts, icons, and design tokens already exist?
- Which one visual idea should make this interface feel specific to the product?
- What states must be designed: loading, empty, error, disabled, hover, active, selected, focused, mobile?

Ask at most one to three questions only when missing constraints would materially change the result.

## Discovery First

For an existing project, inspect before designing or editing:

```bash
rg --files | rg '(^|/)(package.json|src|app|pages|components|styles|public|assets|static|tailwind|vite|next|astro|nuxt|svelte)'
rg -n "className=|styled\\.|createTheme|ThemeProvider|tailwind|@theme|:root|--[a-zA-Z0-9-]+|font-family|from ['\\\"]lucide|from ['\\\"]@mui|from ['\\\"]antd|from ['\\\"]@radix-ui" .
rg -n "Button|Card|Dialog|Modal|Tabs|Toggle|Select|Slider|Tooltip|Navbar|Sidebar|Header|Footer|Logo|Icon" src app pages components 2>/dev/null
```

Extract:

- Framework and route structure
- Existing component primitives and UI libraries
- Color tokens, CSS variables, Tailwind config, font loading, and spacing scale
- Icon library and any brand/logo assets
- Existing page layout patterns and responsive breakpoints
- Available scripts for lint, typecheck, test, build, and dev preview

For a greenfield page or app, choose the simplest stack already implied by the workspace. Build the actual usable experience as the first screen unless the user specifically asks for a marketing landing page.

## Workflow

1. Define the design direction in a short phrase, then make concrete choices for typography, palette, density, motion, and imagery.
2. Map the interaction surface: navigation, primary actions, controls, data states, feedback states, and responsive behavior.
3. Implement in the project's native style. Reuse local components, CSS variables, Tailwind utilities, icon libraries, and framework patterns before adding new abstractions.
4. Use appropriate visual assets. Product, venue, person, object, game, and website experiences need real or generated visual signals, not abstract placeholders. If raster assets are required and absent, use an image-generation workflow when available.
5. Add polished states: hover, focus-visible, active, disabled, loading, empty, error, selected, drag/resize if relevant.
6. Keep layout stable with explicit constraints such as aspect ratio, min/max sizes, grid tracks, and fixed control dimensions.
7. Verify visually at desktop and mobile sizes, then revise anything that overlaps, clips, wraps badly, shifts unexpectedly, or renders blank.

## Direction By Surface

| Surface | Design Bias |
|---------|-------------|
| SaaS, CRM, admin, finance, operations | Quiet, dense, scan-friendly, restrained color, strong tables/forms, predictable navigation |
| Creative tool or editor | Full working canvas, compact controls, icon buttons with tooltips, stable toolbars, no explanatory marketing copy |
| Consumer app | More expressive brand moments, warm feedback, clear task progression, mobile ergonomics |
| Landing or product page | First viewport must clearly show the brand/product/place/person; hint at the next section; avoid generic split hero cards |
| Portfolio, editorial, culture | Strong typography, art direction, image rhythm, intentional whitespace |
| Game or playful experience | More animation, custom assets, immediate playable or interactive surface |

## Visual Rules

- Match the aesthetic to the domain. Do not make operational software look like a marketing hero unless the user asked for that.
- Use distinctive typography when appropriate, but respect existing font loading and performance. Avoid converging on the same popular choices across unrelated projects.
- Use palettes with real contrast and purposeful accents. Avoid one-note themes made only from one hue family.
- Prefer icons for tool actions when a familiar symbol exists. Use the project's icon library, often Lucide, instead of hand-drawn inline SVG.
- Use familiar controls: segmented controls for modes, toggles or checkboxes for booleans, sliders or numeric inputs for numbers, tabs for views, menus for option sets.
- Keep cards to real repeated items, modals, and framed tools. Do not put cards inside cards or turn every page section into a floating card.
- Keep card radii modest unless the existing design system says otherwise.
- Use motion for meaningful state change, spatial orientation, and high-impact reveals. Avoid scattered animation that distracts from the workflow.
- Do not add visible in-app text that explains the app's features, keyboard shortcuts, or visual styling unless the product surface genuinely needs onboarding.
- Ensure text fits its container at mobile and desktop sizes. Do not use viewport-width font scaling or negative letter spacing to force drama.

## Anti-Patterns

**Generic AI aesthetic**

Bad: Purple-blue gradients, glass cards, floating blobs, same rounded cards, generic Inter/Roboto/system typography, stock-like copy, and no domain signal.

Better: Extract the product context first, then pick a specific visual concept and implement it through layout, typography, assets, interaction states, and copy density.

**Decorative dashboard**

Bad: An operations screen with oversized hero text, ornamental cards, sparse fake metrics, and weak tables or forms.

Better: Prioritize navigation, filtering, scanning, comparison, status, dense controls, and fast repeated actions.

**Marketing page when asked for an app**

Bad: A landing page that describes the tool instead of providing the tool.

Better: Put the usable app, game, editor, or workflow in the first viewport. Add explanatory content only when it helps the actual task.

**Unstable responsive design**

Bad: Text clipping, buttons growing on hover, controls changing size, mobile overlap, or layout depending on ideal content length.

Better: Use stable dimensions, responsive constraints, wrapping rules, and screenshot checks at realistic viewport sizes.

**Unverified polish**

Bad: Shipping CSS changes without opening the page.

Better: Run the app, inspect desktop and mobile screenshots, test interactions, and revise visible defects.

## Review Mode

When the user asks to review an existing frontend, lead with findings rather than praise. Prioritize:

1. Broken behavior, inaccessible controls, unreadable contrast, layout overlap, and mobile failures
2. Mismatches with existing design system or framework conventions
3. Information hierarchy and workflow friction
4. Generic visual choices that weaken the product signal
5. Missing states, assets, or verification

Reference files and line numbers when reviewing code. If screenshots are available, mention the viewport and visible issue.

## Verification

Use the repo's scripts first:

```bash
npm run lint
npm run typecheck
npm run build
npm test
```

Run only the commands that exist for the project. If the app needs a dev server, start it and provide the local URL. If static HTML is enough, point to the file.

For visual QA:

- Check at least one desktop and one mobile viewport.
- Confirm images, icons, fonts, gradients, canvas/WebGL, and videos render as intended.
- Confirm controls have hover, focus, selected, disabled, and loading behavior when relevant.
- Confirm text does not overlap, clip, or overflow its parent.
- Scan the CSS for accidental one-note palette, excessive purple/blue gradients, beige/brown monotony, dark slate monotony, or decorative blobs.
- For 3D/canvas/game surfaces, verify the canvas is nonblank, framed correctly, and interactive or animated.

## Deliverables

Return:

- The implemented or reviewed files
- The design direction chosen and why it fits
- The verification commands and visual checks performed
- Any remaining risks, such as unrun tests, missing assets, or browser checks that were not possible
