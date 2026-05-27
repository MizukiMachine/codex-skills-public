---
name: frontend-design
description: "本番向けフロントエンドUIを、コードベースに沿った視覚設計、デザインシステム遵守、アクセシビリティ、インタラクション状態、レスポンシブレイアウト、ブラウザスクリーンショットQAまで含めて構築、再設計、レビュー、改善する。Webコンポーネント、ページ、ダッシュボード、SaaSツール、ランディングページ、アプリ、デザインシステムUI、視覚QA、UIコードレビューを扱うときに使う。特に高品質なデザイン、UI改善、フロントエンド実装、汎用的なAIっぽい見た目の回避、タイポグラフィ設計、テーマ固定、単一デザイン軸の改善を求められた場合に使う。"
---

# Frontend Design

## Purpose

Use this skill to produce working frontend code that feels intentionally designed for its product, audience, and workflow. The goal is not decoration or a design essay; it is a usable interface with a clear visual point of view, stable responsive behavior, accessible controls, and verified rendering.

## Operating Model

Great frontend design comes from context, hierarchy, concept, and implementation integrity.

Prioritize:

1. User workflow and product purpose
2. Existing framework, design system, and code conventions
3. Clear visual hierarchy and information density suited to the domain
4. Responsive stability, accessibility, and interaction states
5. A distinctive aesthetic concept, typography, and theme that support the task
6. Browser verification with real screenshots or smoke tests

Before acting, answer:

- What is the user trying to accomplish on this screen?
- Is this an operational tool, marketing surface, portfolio, game, creative app, or content site?
- What framework, UI library, routing model, assets, fonts, icons, and design tokens already exist?
- Which one visual idea, typographic identity, or themed interaction should make this interface feel specific to the product?
- Does the screen include a canvas, 3D scene, video, map, or other primary visual layer, and what safe areas must the UI preserve around it?
- What states must be designed: loading, empty, error, disabled, hover, active, selected, focused, mobile?

Ask at most one to three questions only when missing constraints would materially change the result.

## Design Contracts

- Treat the local design system as the source of truth. If Storybook, Figma notes, `DESIGN.md`, component docs, shadcn config, CSS variables, or theme tokens exist, inspect them before inventing new styles.
- If no design system exists, define a compact token set first: color roles, type scale, spacing, radius, elevation, motion, and interaction states. Implement through CSS variables, Tailwind theme values, or the project's equivalent.
- Keep scope bounded to the requested surface. Do not replace the framework, router, styling system, or UI library unless the existing stack cannot reasonably support the task.
- For canvas, 3D, game, map, video, or editor surfaces, treat the visual layer and DOM UI as one composition. Define safe zones, z-index layers, pointer-event ownership, focus behavior, and resize rules before styling overlays.
- Design toward WCAG 2.2 AA where feasible: semantic structure, labels, keyboard flow, visible focus, contrast, target size, error identification, and reduced-motion behavior.
- Translate inspiration into local principles. Do not copy a proprietary brand, product UI, or external asset set unless the user owns it or explicitly provided it for reuse.
- When the user asks for a targeted refinement such as typography, motion, density, palette, or spacing, isolate that dimension and preserve unrelated structure unless there is a direct conflict.

## Discovery First

For an existing project, inspect before designing or editing:

```bash
rg --files | rg '(^|/)(DESIGN\.md|AGENTS\.md|README\.md|package.json|src|app|pages|components|styles|public|assets|static|tailwind|vite|next|astro|nuxt|svelte|storybook|\.storybook)'
rg -n "className=|styled\\.|createTheme|ThemeProvider|tailwind|@theme|:root|--[a-zA-Z0-9-]+|font-family|from ['\\\"]lucide|from ['\\\"]@mui|from ['\\\"]antd|from ['\\\"]@radix-ui|from ['\\\"]react-aria|from ['\\\"]framer-motion|from ['\\\"]motion/react|cva\\(" .
rg -n "Button|Card|Dialog|Modal|Tabs|Toggle|Select|Slider|Tooltip|Navbar|Sidebar|Header|Footer|Logo|Icon|Empty|Error|Skeleton|Toast" src app pages components stories 2>/dev/null
rg -n "canvas|WebGLRenderer|three|phaser|pixi|requestAnimationFrame|setAnimationLoop|pointer-events|aria-label|data-role" src app pages components styles 2>/dev/null
```

If these searches produce too much output, narrow them to the target route, component, or style folder before reading more.

Extract:

- Framework and route structure
- Existing component primitives and UI libraries
- Design docs, Storybook stories, Figma handoff notes, screenshots, and acceptance criteria
- Color tokens, CSS variables, Tailwind config, font loading, spacing scale, radius, elevation, and motion patterns
- Icon library and any brand/logo assets
- Existing page layout patterns and responsive breakpoints
- Primary visual layer constraints: canvas/media bounds, HUD safe areas, overlay stack, pointer-event routing, and resize behavior
- Existing loading, empty, error, disabled, selected, focus, and validation patterns
- Available scripts for lint, typecheck, test, build, and dev preview

For a greenfield page or app, choose the simplest stack already implied by the workspace. Build the actual usable experience as the first screen unless the user specifically asks for a marketing landing page.

## Workflow

1. Define the screen job and design direction in a short phrase. Include surface type, audience, density, palette, typography, imagery, motion, and one memorable product-specific move.
2. Align or create the token contract. Decide color roles, type scale, spacing, radius, elevation, focus ring, disabled treatment, and motion rules before styling many components.
3. Map the interaction surface: navigation, primary and secondary actions, controls, data states, feedback states, keyboard paths, touch ergonomics, and responsive behavior.
4. For canvas, 3D, media, map, game, or editor screens, reserve the primary visual layer first. Place HUD, rails, toolbars, modals, and status bars in stable safe zones and decide which layer owns pointer and keyboard input.
5. Implement in the project's native style. Reuse local components, CSS variables, Tailwind utilities, icon libraries, accessibility primitives, and framework patterns before adding new abstractions.
6. Use appropriate visual assets. Product, venue, person, object, game, and website experiences need real or generated visual signals, not abstract placeholders. If raster assets are required and absent, use an image-generation workflow when available.
7. Add polished states: hover, focus-visible, active, disabled, loading, empty, error, selected, drag/resize if relevant.
8. Keep layout stable with explicit constraints such as aspect ratio, min/max sizes, grid tracks, container queries where useful, and fixed control dimensions.
9. Verify visually at desktop and mobile sizes, then revise anything that overlaps, clips, wraps badly, shifts unexpectedly, or renders blank.

## Direction By Surface

| Surface | Design Bias |
|---------|-------------|
| SaaS, CRM, admin, finance, operations | Quiet, dense, scan-friendly, restrained color, strong tables/forms, predictable navigation |
| Creative tool or editor | Full working canvas, compact controls, icon buttons with tooltips, stable toolbars, no explanatory marketing copy |
| Canvas, 3D, map, or media app | Primary visual layer first, DOM controls in safe zones, pointer-event contract, responsive framing, readable overlays |
| Consumer app | More expressive brand moments, warm feedback, clear task progression, mobile ergonomics |
| Landing or product page | First viewport must clearly show the brand/product/place/person; hint at the next section; avoid generic split hero cards |
| Portfolio, editorial, culture | Strong typography, art direction, image rhythm, intentional whitespace |
| Game or playful experience | Immediate playable surface, readable HUD, custom assets, responsive input, pause/game-over/settings states |

## Aesthetic Direction

Choose a specific visual concept instead of a generic "modern" look. The concept can be quiet or loud, but it must be deliberate and appropriate to the surface.

Use strong directions when the product can support them:

- **Brutally minimal**: sparse structure, precise spacing, strong type contrast, few effects
- **Editorial or magazine-like**: expressive display type, image rhythm, asymmetric pacing
- **Industrial or technical**: exposed grids, utility color, monospaced accents, dense controls
- **Luxury or refined**: restrained palette, high-quality imagery, subtle motion, careful proportion
- **Playful or toy-like**: saturated accents, tactile controls, bouncy feedback, custom assets
- **Retro-futuristic, solarpunk, cyberpunk, art deco, Memphis, or brutalist**: use only when it fits the product or the user asks for it

Theme-locking rule: when the user names an aesthetic, lock color, typography, layout rhythm, texture, motion, and component detailing to that theme. Match implementation complexity to the concept: maximal directions need richer layers and motion; refined minimal directions need stricter spacing, contrast, and restraint.

## Typography And Theme

- Treat typography as a core design system, not an afterthought. Choose display, body, numeric, and code styles deliberately.
- Reuse existing fonts when the project already has a brand or performance budget. For greenfield work, avoid defaulting to Inter, Roboto, Arial, or system fonts unless the product calls for utilitarian neutrality.
- Pair fonts for contrast when useful: serif with geometric sans, display with restrained body, or mono accents with a readable UI face.
- Use strong weight and scale contrast for heroes, editorial surfaces, and brand moments; use compact, stable type scales for dashboards, editors, and operational tools.
- Load fonts through the project's established mechanism. Avoid adding remote font dependencies when offline use, privacy, or performance constraints make that a poor tradeoff.
- Build the theme with variables or tokens. Color, radius, shadow, type scale, focus, disabled state, and motion should be reusable rather than scattered one-offs.
- Pull palette inspiration from the domain, product materials, imagery, or named aesthetic. Use dominant roles plus sharp accents; avoid timid evenly distributed palettes.

## Targeted Refinement

When the user asks to improve one dimension, keep the edit narrowly focused:

| Request | Preserve | Change |
|---------|----------|--------|
| Better typography | Layout, palette, components | Font choice, scale, weight, line-height, measure, hierarchy |
| Better color/theme | Layout, type hierarchy, workflow | Tokens, semantic roles, contrast, accents, surfaces |
| Better motion | Layout, palette, information architecture | Timing, easing, entrance, hover/focus, state transitions |
| More premium/playful/minimal/etc. | Core workflow and accessibility | Aesthetic tokens, imagery, texture, rhythm, detailing |
| Fix responsive polish | Visual identity and behavior | Constraints, wrapping, breakpoints, overflow, touch targets |

## Interaction Rules

- Make the common path obvious. Each screen should make the next action clear without competing primary buttons.
- Use progressive disclosure for secondary actions, filters, advanced settings, and destructive controls.
- Give each async region a loading, empty, error, retry, and success or saved state when relevant.
- Prefer URL state for shareable filters, search, sort, tabs, and pagination. Use local state for transient UI such as open menus and temporary selections.
- Build forms with persistent labels, useful helper text, inline validation, submit feedback, and safe destructive confirmation.
- Make dialogs, popovers, menus, command palettes, and drawers manage focus, Escape, outside click, scroll lock, and return focus.
- Treat keyboard and touch as first-class: visible focus, logical tab order, hit targets large enough for touch, and no hover-only affordances.
- For layered canvas/HUD screens, keep passive overlay regions `pointer-events: none` and restore `pointer-events: auto` only on controls. Do not let decorative layers intercept gameplay, map, editor, or camera input.

## Visual Rules

- Match the aesthetic to the domain. Do not make operational software look like a marketing hero unless the user asked for that.
- Commit to a clear aesthetic direction, then execute it with restraint or intensity as the domain requires. Minimal designs need precision; maximal designs need orchestration.
- Use distinctive typography when appropriate, but respect existing font loading and performance. Avoid converging on the same popular choices across unrelated projects.
- Use palettes with real contrast, purposeful accents, and semantic roles. Avoid one-note themes made only from one hue family.
- Prefer icons for tool actions when a familiar symbol exists. Use the project's icon library, often Lucide, instead of hand-drawn inline SVG.
- Use familiar controls: segmented controls for modes, toggles or checkboxes for booleans, sliders or numeric inputs for numbers, tabs for views, menus for option sets.
- For HUDs, dashboards, previews, counters, meters, and keycaps, use fixed or bounded dimensions, tabular numerals, stable SVG/canvas viewBoxes, and wrapping rules that tolerate localization and long labels.
- Keep cards to real repeated items, modals, and framed tools. Do not put cards inside cards or turn every page section into a floating card.
- Keep card radii modest unless the existing design system says otherwise.
- Use motion for meaningful state change, spatial orientation, and high-impact reveals. Avoid scattered animation that distracts from the workflow.
- Do not add visible in-app text that explains the app's features, keyboard shortcuts, or visual styling unless the product surface genuinely needs onboarding.
- Ensure text fits its container at mobile and desktop sizes. Do not use viewport-width font scaling or negative letter spacing to force drama.

## Quality Gates

Before calling the work done, confirm:

- The first viewport contains a product, brand, workflow, or domain signal specific enough that it could not belong to any generic app.
- For canvas, 3D, media, map, game, or editor screens, the primary visual layer remains visible and correctly framed; HUD overlays do not hide critical content at desktop or mobile sizes.
- Primary task completion is clear, with no more than one dominant primary action per view unless the workflow truly requires branching.
- Design tokens and local primitives are used instead of hardcoded one-off styling when a system exists.
- For interactive or data-driven surfaces, critical states are designed: loading, empty, error, disabled, selected, focused, active, hover, mobile, and long-content cases.
- Accessibility basics pass: semantic elements, labels, contrast, focus-visible, keyboard operation, reduced motion, and screen-reader names for icon-only controls.
- The UI tolerates realistic content: long names, localized text, many/few items, missing images, slow network, and narrow screens.
- Visual assets, fonts, animation, shadows, and effects support the concept without excessive payload, jank, or readability loss.

## Anti-Patterns

**Generic AI aesthetic**

Bad: Purple-blue gradients, glass cards, floating blobs, same rounded cards, generic Inter/Roboto/system typography, stock-like copy, predictable layouts, and no domain signal.

Better: Extract the product context first, then pick a specific visual concept and implement it through layout, typography, assets, interaction states, and copy density.

**Theme as decoration**

Bad: Naming an aesthetic but changing only colors while leaving default layout, type, motion, and component shapes untouched.

Better: Lock the theme across palette, typography, spacing rhythm, imagery, texture, motion, and control details.

**Uncontrolled maximalism**

Bad: Adding many effects, patterns, overlaps, custom cursors, and animations that compete with the task.

Better: Choose one or two high-impact expressive moves and keep interaction, readability, and performance intact.

**Over-broad refinement**

Bad: Rebuilding the whole page when the user only asked for better typography, color, motion, or mobile polish.

Better: Isolate the requested design dimension, adjust it deeply, and leave unrelated structure alone.

**Decorative dashboard**

Bad: An operations screen with oversized hero text, ornamental cards, sparse fake metrics, and weak tables or forms.

Better: Prioritize navigation, filtering, scanning, comparison, status, dense controls, and fast repeated actions.

**Marketing page when asked for an app**

Bad: A landing page that describes the tool instead of providing the tool.

Better: Put the usable app, game, editor, or workflow in the first viewport. Add explanatory content only when it helps the actual task.

**HUD pasted over a scene**

Bad: Floating panels, status bars, and controls are positioned after the canvas without reserving safe space, so they hide the subject, capture input accidentally, or break at shorter viewports.

Better: Design the canvas/media framing and DOM HUD together. Reserve safe zones, route pointer events deliberately, test pause/settings/error states, and adjust camera or visual composition when overlays are present.

**Unstable responsive design**

Bad: Text clipping, buttons growing on hover, controls changing size, mobile overlap, or layout depending on ideal content length.

Better: Use stable dimensions, responsive constraints, wrapping rules, and screenshot checks at realistic viewport sizes.

**Token drift**

Bad: Adding hardcoded colors, spacing, radii, shadows, or custom controls in a project with established tokens and primitives.

Better: Extend existing tokens or compose existing primitives. If an exception is necessary, keep it local and explain why.

**Incomplete state surface**

Bad: Designing only the happy path with static mock data.

Better: Implement or at least account for loading, empty, error, disabled, focused, long-content, and mobile states.

**Unverified polish**

Bad: Shipping CSS changes without opening the page.

Better: Run the app, inspect desktop and mobile screenshots, test interactions, and revise visible defects.

## Review Mode

When the user asks to review an existing frontend, lead with findings rather than praise. Prioritize:

1. Broken behavior, inaccessible controls, unreadable contrast, layout overlap, and mobile failures
2. Mismatches with existing design system, token, accessibility, or framework conventions
3. Information hierarchy, action hierarchy, and workflow friction
4. Generic visual choices that weaken the product signal
5. Missing states, assets, content stress handling, or verification

Classify issues as blocking, major, or minor when useful. Reference files and line numbers when reviewing code. If screenshots are available, mention the viewport and visible issue.

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
- Inspect browser console errors, page errors, failed requests, and obvious layout overflow when browser automation is available.
- Confirm images, icons, fonts, gradients, canvas/WebGL, and videos render as intended.
- Confirm controls have hover, focus, selected, disabled, and loading behavior when relevant.
- Confirm text does not overlap, clip, overflow its parent, or change control dimensions unexpectedly.
- Scan the CSS for accidental one-note palette, excessive purple/blue gradients, beige/brown monotony, dark slate monotony, or decorative blobs.
- For 3D/canvas/game surfaces, verify the canvas is nonblank, framed correctly, and interactive or animated.

## Deliverables

Return:

- The implemented or reviewed files
- The design direction chosen and why it fits
- The verification commands and visual checks performed
- Any remaining risks, such as unrun tests, missing assets, or browser checks that were not possible
