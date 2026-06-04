---
name: playwright-testing
description: "フロントエンドのテストを計画・実装・デバッグする。Playwright、Vitest/Jest、アクセシビリティ、視覚回帰、不安定テスト調査、canvas/WebGLゲームテストで使う。"
metadata:
  short-description: "フロントエンドテスト: Playwright、Vitest、flaky調査、ゲームテスト"
---

# Frontend Testing

安全な refactor を可能にするため、適切な test layer を選び、app を観測可能にし、nondeterminism を除去して actionable な失敗にする。

## 考え方: Confidence Per Minute

frontend tests が失敗する理由は2つだけ。product が壊れているか、test が嘘をついているか。signal を最大化し、"test is lying" を最小化する。

**test を書く前に確認すること:**

- どの user risk を cover するか。money、progression、auth、data loss、crashes など
- その bug class を捕まえる最小 layer は何か。pure logic、UI、full browser
- time、RNG、async loading、network、animations、fonts、GPU などの nondeterminism は何か
- `setTimeout` 以外で待てる "ready" signal は何か
- failure 時に CI で診断できるよう、何を print/screenshot すべきか

**基本原則**

1. **implementation ではなく contract を test する**: stable user-meaningful outcomes と public seams を assert する
2. **retries より determinism**: time/RNG/network を制御し、flake を原因から消す
3. **debugger のように観測する**: console errors、network failures、screenshots、state dumps を failure evidence にする
4. **まず1つの critical flow**: 50個の flaky tests より信頼できる smoke test を優先する

## Test Layer Decision Tree

必要な confidence を得られる最も安い layer を選ぶ。

| Layer | Speed | Use For |
|-------|-------|---------|
| **Unit** | Fastest | pure functions、reducers、validators、math、pathfinding、deterministic simulation |
| **Component** | Medium | mocked IO を使った UI behavior |
| **E2E** | Slowest | routing、storage、real bundling/runtime をまたぐ critical user flows |
| **Visual** | Specialized | layout/pixel regressions。canvas/WebGL では determinism を固定した後だけ |

## Quick Start: 最初の Smoke Test

1. **1 critical flow** を定義する: "page loads -> user can start -> one key action works"
2. app に **test seam** を追加する
3. runner を選ぶ: E2E は Playwright MCP、logic は unit tests
4. **fail loudly**: console errors と failed requests を test failures にする
5. **stabilize**: RNG seed、freeze time、fixed viewport、disable animations

## Concrete MCP Workflow: Game Testing

Phaser/canvas game を test するときの手順:

```text
1. mcp__playwright__browser_navigate
   -> http://localhost:3000?test=1&seed=42

2. mcp__playwright__browser_evaluate
   -> () => new Promise(r => { const c = () => window.__TEST__?.ready ? r(true) : setTimeout(c, 100); c(); })
   (game ready を待つ)

3. mcp__playwright__browser_console_messages
   -> level: "error"
   (error があれば fail)

4. mcp__playwright__browser_snapshot
   -> UI state と refs を取得

5. mcp__playwright__browser_click
   -> element: "Start Button", ref: [from snapshot]

6. mcp__playwright__browser_evaluate
   -> () => window.__TEST__.state()
   (game state を assert)

7. mcp__playwright__browser_press_key
   -> key: "ArrowRight"

8. mcp__playwright__browser_evaluate
   -> () => window.__TEST__.state().player.x
   (movement を検証)

9. mcp__playwright__browser_take_screenshot
   -> filename: "gameplay-state.png"
   (deterministic setup 後の visual evidence)
```

## Recommended Test Seams

testability のために app へ read-only、stable、minimal な seam を追加する。

```javascript
window.__TEST__ = {
  ready: false,           // true after first interactive frame
  seed: null,             // current RNG seed
  sceneKey: null,         // current scene/route
  state: () => ({         // JSON-serializable snapshot
    scene: this.sceneKey,
    player: { x, y, hp },
    score: gameState.score,
    entities: entities.map(e => ({ id: e.id, type: e.type, x: e.x, y: e.y }))
  }),
  commands: {             // optional mutation commands
    reset: () => {},
    seed: (n) => {},
    skipIntro: () => {}
  }
};
```

raw Phaser/engine objects ではなく、IDs と essential fields を expose する。

## 避けること

**wrong layer を test する**

問題: pure logic を E2E で検証すると遅く brittle になり、failure の原因も分かりにくい。
改善: logic は unit test、E2E は integration contract と critical flow に使う。

**implementation details を assert する**

問題: DOM structure や classnames は refactor で変わりやすく、user-visible behavior を保証しない。
改善: text、score、HP changes、navigation、visible state など user-meaningful outputs を assert する。

**sleep-driven tests**

問題: `wait 2s then click` は machine speed、network、animation に依存して flaky になる。
改善: DOM marker、network idle、`window.__TEST__.ready` など explicit readiness を待つ。

**uncontrolled randomness**

問題: RNG/time が uncontrolled だと同じ test が別状態を検証してしまう。
改善: `?seed=42`、freeze time、stable invariants を使う。

**determinism なしの pixel snapshots**

問題: canvas screenshots は timing、DPR、randomness、animation frame で揺れる。
改善: deterministic mode を先に作り、known stable frames で screenshot する。

**retries を戦略にする**

問題: retry は real failures を隠し、CI green でも product confidence を上げない。
改善: flake source を分類し、readiness、timing、environment、data の原因を直す。

## Failed Tests の debug

失敗時はこの順序で evidence を集める。

1. **Console errors**: `mcp__playwright__browser_console_messages({ level: "error" })`
2. **Network failures**: `mcp__playwright__browser_network_requests()` で non-2xx を確認
3. **Screenshot**: `mcp__playwright__browser_take_screenshot()` で失敗時の visual state
4. **App state**: `mcp__playwright__browser_evaluate({ function: "() => window.__TEST__.state()" })`
5. **Flake classification** (`references/flake-reduction.md`):
   - readiness -> explicit wait を追加
   - timing -> animation/physics を制御
   - environment -> viewport/DPR を固定
   - data -> test data を isolate

## "十分な testing" の基準

Minimum viable test suite:

- [ ] app が load し primary action が動く **1 smoke test**
- [ ] ready flag と state を持つ **test seam** (`window.__TEST__`)
- [ ] canvas/game 用 deterministic mode (`?test=1` で seeding)
- [ ] console errors が tests を fail させる
- [ ] CI が push ごとに tests を実行する

次の段階:

- auth、payment、save/load など critical paths に dedicated E2E
- pathfinding、damage calc、state machines など complex logic に unit tests
- menu、HUD など key screens の visual regression。determinism は固定する

## Visual Regression with `imgdiff.py`

screenshot の pixel comparison:

```bash
# Compare baseline to current
python scripts/imgdiff.py baseline.png current.png --out diff.png

# Allow small tolerance (anti-aliasing differences)
python scripts/imgdiff.py baseline.png current.png --max-rms 2.0
```

exit codes: 0 = identical、1 = different、2 = error

## UI Slicing Regressions

Canvas UI issues (panel seams、segmented ribbons、invisible HUD fills) は、full gameplay flow より dedicated UI harness で検出する。

1. UI assets だけを load する simple `test.html` / scene を作る
2. raw slices と assembled panels を並べ、ribbon/bar も "raw crop + scale" と "stitched multi-slice" の両方で表示する
3. `window.__TEST__.commands.showTest(n)` を expose し、Playwright が deterministic に mode を切り替えられるようにする
4. panels、ribbons、bars の targeted screenshots を capture し、CI で diff する

deterministic setup と screenshot workflow は `references/phaser-canvas-testing.md` を読む。

## Variation Guidance

- **DOM app**: standard Playwright selectors、text/elements を待つ
- **Canvas game**: test seams 必須。`window.__TEST__.ready` で待つ
- **Hybrid**: menus は DOM、gameplay は test seams
- **CI-only GPU**: software rendering flags、または visual tests の skip が必要な場合あり
- **UI slicing regressions**: nine-slice/ribbon/bar は deterministic modes と targeted screenshots を持つ小さな harness を優先する

## Bundled Resources

必要なときだけ読む。

- `references/playwright-mcp-cheatsheet.md`: MCP tool patterns
- `references/phaser-canvas-testing.md`: Phaser games の deterministic mode
- `references/flake-reduction.md`: flake classification and fixes

## 覚えておくこと

小さく安定した readiness + state seam を足せば、canvas/WebGL games を含むほぼすべての frontend は testable になる。coverage numbers ではなく、deterministic で failure evidence が豊富な、保守しやすい tests を目指す。
