---
name: frontend-observation
description: "本番品質のフロントエンドUIを構築・改善・レビューする。既存デザインに沿った視覚設計、アクセシビリティ、レスポンシブ対応、状態設計、ブラウザ検証で使う。"
---

# Frontend Observation

## 目的

product、audience、workflow に合う意図的な frontend code を作る。装飾や design essay ではなく、明確な visual point of view、stable responsive behavior、accessible controls、verified rendering を備えた usable interface を目指す。

## 基本方針

良い frontend design は context、hierarchy、concept、implementation integrity から生まれる。

優先順位:

1. user workflow と product purpose
2. existing framework、design system、code conventions
3. domain に合う visual hierarchy と information density
4. responsive stability、accessibility、interaction states
5. task を支える aesthetic concept、typography、theme
6. browser verification with screenshots / smoke tests

作業前に確認すること:

- この screen で user は何を達成するのか
- operational tool、marketing surface、portfolio、game、creative app、content site のどれか
- framework、UI library、routing、assets、fonts、icons、design tokens は何か
- この product らしさを出す visual idea / typography / themed interaction は何か
- canvas、3D scene、video、map など primary visual layer があるか。UI safe areas はどこか
- loading、empty、error、disabled、hover、active、selected、focused、mobile など設計すべき states は何か

不足情報で結果が大きく変わる場合だけ、1-3問まで確認する。

## Design Contracts

- local design system を source of truth にする。Storybook、Figma notes、`DESIGN.md`、component docs、shadcn config、CSS variables、theme tokens があれば先に確認する
- design system がなければ compact token set を先に定義する: color roles、type scale、spacing、radius、elevation、motion、interaction states。CSS variables、Tailwind theme values、または project の equivalent で実装する
- scope は requested surface に閉じる。既存 stack で対応できる限り framework/router/styling system/UI library を置き換えない
- canvas、3D、game、map、video、editor surfaces では visual layer と DOM UI を1つの composition として扱う。safe zones、z-index、pointer events、focus、resize rules を先に決める
- 可能な範囲で WCAG 2.2 AA を目指す: semantic structure、labels、keyboard flow、focus、contrast、target size、error identification、reduced motion
- inspiration は local principles に変換する。proprietary brand / UI / asset set は user が所有または提供している場合だけ使う
- typography、motion、density、palette、spacing の targeted refinement では、その dimension に絞り、直接 conflict しない限り無関係な structure は保つ

## Discovery First

既存 project では設計・編集前に調べる。

```bash
rg --files | rg '(^|/)(DESIGN\.md|AGENTS\.md|README\.md|package.json|src|app|pages|components|styles|public|assets|static|tailwind|vite|next|astro|nuxt|svelte|storybook|\.storybook)'
rg -n "className=|styled\\.|createTheme|ThemeProvider|tailwind|@theme|:root|--[a-zA-Z0-9-]+|font-family|from ['\\\"]lucide|from ['\\\"]@mui|from ['\\\"]antd|from ['\\\"]@radix-ui|from ['\\\"]react-aria|from ['\\\"]framer-motion|from ['\\\"]motion/react|cva\\(" .
rg -n "Button|Card|Dialog|Modal|Tabs|Toggle|Select|Slider|Tooltip|Navbar|Sidebar|Header|Footer|Logo|Icon|Empty|Error|Skeleton|Toast" src app pages components stories 2>/dev/null
rg -n "canvas|WebGLRenderer|three|phaser|pixi|requestAnimationFrame|setAnimationLoop|pointer-events|aria-label|data-role" src app pages components styles 2>/dev/null
```

output が多い場合は target route / component / style folder に絞る。

抽出するもの:

- framework / route structure
- existing component primitives / UI libraries
- design docs、Storybook stories、Figma handoff、screenshots、acceptance criteria
- color tokens、CSS variables、Tailwind config、font loading、spacing、radius、elevation、motion patterns
- icon library、brand/logo assets
- page layout patterns と responsive breakpoints
- primary visual layer constraints: canvas/media bounds、HUD safe areas、overlay stack、pointer routing、resize behavior
- loading、empty、error、disabled、selected、focus、validation patterns
- lint、typecheck、test、build、dev preview scripts

greenfield page/app では workspace が示す最も単純な stack を選ぶ。ユーザーが marketing landing page を明示しない限り、最初の画面に actual usable experience を作る。

## ワークフロー

1. screen job と design direction を短い phrase で定義する。surface type、audience、density、palette、typography、imagery、motion、product-specific move を含める
2. token contract を合わせる / 作る。color roles、type scale、spacing、radius、elevation、focus ring、disabled、motion rules を決める
3. interaction surface を map する: navigation、actions、controls、data states、feedback、keyboard、touch、responsive behavior
4. canvas/3D/media/map/game/editor では primary visual layer を先に確保し、HUD / rails / toolbars / modals / status bars を stable な safe zones に置き、どの layer が pointer/keyboard input を持つか決める
5. project native style で実装する。local components、CSS variables、Tailwind utilities、icon libraries、accessibility primitives、framework patterns を再利用する
6. 適切な visual assets を使う。product、venue、person、object、game、website experiences には abstract placeholder ではなく real/generated visual signals が必要。raster assets が必要で無い場合は、可能なら image-generation workflow を使う
7. hover、focus-visible、active、disabled、loading、empty、error、selected、drag/resize などの states を polish する
8. aspect ratio、min/max、grid tracks、container queries、fixed control dimensions などで layout を stable にする
9. desktop/mobile で視覚確認し、overlap、clip、bad wrap、layout shift、blank rendering を修正する

## Surface 別の方向性

| Surface | Design Bias |
|---------|-------------|
| SaaS, CRM, admin, finance, operations | quiet、dense、scan-friendly、restrained color、tables/forms、predictable navigation |
| Creative tool or editor | working canvas、compact controls、icon buttons + tooltips、stable toolbars、no marketing copy |
| Canvas, 3D, map, media app | primary visual layer first、safe-zone DOM controls、pointer-event contract、responsive framing、readable overlays |
| Consumer app | expressive brand moments、warm feedback、clear task progression、mobile ergonomics |
| Landing/product page | first viewport で brand/product/place/person を明示し、next section を少し見せる。generic split hero cards を避ける |
| Portfolio/editorial/culture | strong typography、art direction、image rhythm、intentional whitespace |
| Game/playful | immediate playable surface、readable HUD、custom assets、responsive input、pause/game-over/settings |

## Aesthetic Direction

generic "modern" ではなく specific visual concept を選ぶ。quiet でも loud でも、surface に合って deliberate であること。

product が支えられる場合は強い方向性を使う:

- **Brutally minimal**: sparse structure、precise spacing、strong type contrast、few effects
- **Editorial / magazine-like**: expressive display type、image rhythm、asymmetric pacing
- **Industrial / technical**: exposed grids、utility color、monospaced accents、dense controls
- **Luxury / refined**: restrained palette、high-quality imagery、subtle motion、careful proportion
- **Playful / toy-like**: saturated accents、tactile controls、bouncy feedback、custom assets
- **Retro-futuristic / solarpunk / cyberpunk / art deco / Memphis / brutalist**: product に合うか user が求めた場合だけ

Theme-locking rule: user が aesthetic を指定したら、color、typography、layout rhythm、texture、motion、component detailing をその theme に lock する。実装の複雑さは concept に合わせる ― maximal な方向性はより richer な layer と motion を要し、refined で minimal な方向性はより厳格な spacing、contrast、抑制を要する。

## Typography / Theme

- typography を design system の中核として扱い、afterthought にしない。display、body、numeric、code styles を意図的に選ぶ
- project に brand や performance budget があれば existing fonts を再利用する。greenfield では、product が utilitarian neutrality を求めない限り Inter/Roboto/Arial/system fonts に無自覚に寄せない
- serif + geometric sans、display + restrained body、mono accents + readable UI face など、必要なら contrast を作る
- heroes/editorial surfaces/brand moments では strong な weight/scale contrast、dashboards/editors/operational tools では compact/stable type scale
- font loading は project の仕組みに合わせる。offline/privacy/performance が問題なら remote dependency を避ける
- colors、radius、shadow、type scale、focus、disabled、motion は variables/tokens にする
- palette は domain、product materials、imagery、named aesthetic から引く。dominant roles + sharp accents を使い、臆病な evenly distributed palettes を避ける

## Targeted Refinement

| Request | Preserve | Change |
|---------|----------|--------|
| typography | layout、palette、components | font、scale、weight、line-height、measure、hierarchy |
| color/theme | layout、type hierarchy、workflow | tokens、semantic roles、contrast、accents、surfaces |
| motion | layout、palette、IA | timing、easing、entrance、hover/focus、state transitions |
| more premium/playful/minimal | core workflow、accessibility | aesthetic tokens、imagery、texture、rhythm、detailing |
| responsive polish | visual identity、behavior | constraints、wrapping、breakpoints、overflow、touch targets |

## Interaction Rules

- common path を明確にし、不要な competing primary buttons を置かない
- secondary actions、filters、advanced settings、destructive controls は progressive disclosure
- async region には loading、empty、error、retry、success/saved state
- shareable filters/search/sort/tabs/pagination は URL state を優先
- forms は persistent labels、helper text、inline validation、submit feedback、destructive confirmation
- dialogs/popovers/menus/drawers は focus、Escape、outside click、scroll lock、return focus を管理
- keyboard/touch を first-class に扱う。visible focus、logical tab order、touch targets、no hover-only affordances
- layered canvas/HUD では passive overlay region を `pointer-events: none` にし、controls だけ `pointer-events: auto` に戻す。decorative layers が gameplay、map、editor、camera input を奪わないようにする

## Visual Rules

- domain に合う aesthetic にする。operational software を marketing hero にしない
- clear aesthetic direction に commit し、domain に応じた restraint または intensity で実装する。minimal designs は precision を、maximal designs は orchestration を要する
- distinctive typography は使えるが、existing font loading/performance を尊重する。無関係な project 間で同じ popular choices に収束させない
- palettes は real contrast、purposeful accents、semantic roles を持たせる。1つの hue family だけで作る one-note themes を避ける
- familiar な symbol がある tool actions は icons を優先し、hand-drawn inline SVG ではなく project の icon library（多くは Lucide）を使う
- modes は segmented controls、booleans は toggles/checkboxes、numbers は sliders/inputs、views は tabs、options は menus
- HUDs/dashboards/previews/counters/meters/keycaps は fixed/bounded dimensions、tabular numerals、stable SVG/canvas viewBoxes、localization と long labels に耐える wrapping rules
- cards は repeated items、modals、framed tools に限定する。cards inside cards や floating page sections を避ける
- card radii は design system が求めない限り控えめ
- motion は meaningful state change、spatial orientation、high-impact reveals に使い、workflow を邪魔する散らばった animation を避ける
- visible in-app text で features / shortcuts / styling を説明しない。onboarding が本当に必要な場合だけ
- mobile/desktop で text が container に収まるようにする。viewport-width font scaling や negative letter spacing で無理に演出しない

## Quality Gates

完了前に確認すること:

- first viewport に generic app ではない product/brand/workflow/domain signal がある
- canvas/3D/media/map/game/editor では primary visual layer が見え、HUD が critical content を隠さない
- primary task completion が明確で、不要に複数 primary actions を競合させない
- design tokens / local primitives を使い、one-off hardcode を避ける
- interactive/data-driven surface では loading、empty、error、disabled、selected、focused、active、hover、mobile、long content を扱う
- accessibility basics: semantic elements、labels、contrast、focus-visible、keyboard operation、reduced motion、icon-only controls の screen-reader names
- long names、localized text、many/few items、missing images、slow network、narrow screens に耐える
- assets、fonts、animation、shadows、effects が readability/performance を損なわない

## 避けること

**generic AI aesthetic**

問題: purple-blue gradients、glass cards、floating blobs、同じ rounded cards、generic な Inter/Roboto/system typography、stock-like copy、predictable layouts、domain signal なし。
改善: まず product context を抽出し、specific visual concept を選んで、layout、typography、assets、interaction states、copy density を通じて実装する。

**theme as decoration**

問題: aesthetic 名を付けても color だけ変え、default の layout、type、motion、component shapes はそのままにする。
改善: palette、typography、spacing rhythm、imagery、texture、motion、control details にわたって theme を lock する。

**uncontrolled maximalism**

問題: 多数の effects、patterns、overlaps、custom cursors、animations を足して task と競合させる。
改善: high-impact な expressive move を1〜2個だけ選び、interaction、readability、performance を保つ。

**over-broad refinement**

問題: user が typography、color、motion、mobile polish だけを依頼したのに page 全体を作り替える。
改善: 依頼された design dimension に絞り、それを deeply に調整し、無関係な structure はそのまま残す。

**decorative dashboard**

問題: operations 画面に oversized hero text、ornamental cards、sparse fake metrics、weak tables/forms。
改善: navigation、filtering、scanning、comparison、status、dense controls、fast repeated actions を優先する。

**app 依頼に marketing page を返す**

問題: tool を提供せず tool を説明する landing page。
改善: usable な app、game、editor、workflow を first viewport に置く。explanatory content は actual task に役立つ場合だけ追加する。

**HUD pasted over a scene**

問題: floating panels、status bars、controls を safe space を確保せず canvas の後に配置するため、subject を隠したり、誤って input を奪ったり、短い viewport で崩れたりする。
改善: canvas/media framing と DOM HUD を一体で設計する。safe zones を確保し、pointer events を意図的に route し、pause/settings/error states を test し、overlay があるときは camera や visual composition を調整する。

**unstable responsive design**

問題: text clipping、hover で buttons が大きくなる、controls の size 変化、mobile overlap、ideal content length への依存。
改善: stable dimensions、responsive constraints、wrapping rules、realistic な viewport sizes での screenshot checks を使う。

**token drift**

問題: established tokens と primitives がある project に hardcoded colors、spacing、radii、shadows、custom controls を足す。
改善: existing tokens を拡張するか existing primitives を組み合わせる。例外が必要なら local に留め、理由を説明する。

**incomplete state surface**

問題: static mock data で happy path だけを設計する。
改善: loading、empty、error、disabled、focused、long-content、mobile の states を実装するか、少なくとも考慮する。

**unverified polish**

問題: page を開かずに CSS changes を ship する。
改善: app を実行し、desktop/mobile screenshot を確認し、interactions を test し、見える defects を修正する。

## Review Mode

existing frontend の review 依頼では、称賛ではなく findings を先に出す。優先順位:

1. broken behavior、inaccessible controls、unreadable contrast、layout overlap、mobile failures
2. design system、token、accessibility、framework conventions との不一致
3. information hierarchy、action hierarchy、workflow friction
4. product signal を弱める generic visuals
5. missing states、assets、content stress handling、verification

blocking / major / minor に分類すると有用。code review では file/line を参照し、screenshots がある場合は viewport と visible issue を示す。

## 検証

existing scripts を使う。

```bash
npm run lint
npm run typecheck
npm run build
npm test
```

存在する commands だけ実行する。dev server が必要なら起動して URL を渡す。static HTML で足りるなら file を示す。

Visual QA:

- desktop と mobile viewport を少なくとも1つずつ確認
- browser automation があれば console errors、page errors、failed requests、layout overflow を見る
- images、icons、fonts、gradients、canvas/WebGL、videos が意図どおり render されるか確認
- controls の hover、focus、selected、disabled、loading
- text の overlap / clip / overflow / control dimension shift
- CSS palette が one-note、purple/blue gradient 過多、beige/brown/dark slate monotony、decorative blobs になっていないか確認
- 3D/canvas/game surfaces は canvas nonblank、correctly framed、interactive/animated を確認

## 成果物

implemented / reviewed files、選んだ design direction と理由、verification commands / visual checks、remaining risks を報告する。
