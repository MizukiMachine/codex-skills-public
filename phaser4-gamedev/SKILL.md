---
name: phaser4-gamedev
description: "Phaser 4専用のゲーム開発・移行を扱う。Phaser 4プロジェクト、Phaser 3からの移行、レンダラー、シェーダー、GPUレイヤー、v4固有の不具合調査で使う。Phaser 3のみ、またはバージョン不明の場合はphaser-gamedevを優先する。"
---

# Phaser 4 Game Development

## 目的

Phaser 4 browser games の実装、debug、optimization、migration を codebase-aware に行う。ユーザーが Phaser 4 を明示した、codebase が Phaser 4.x と確認できた、または Phaser 3 -> 4 migration の場合に使う。working game code、measured asset metadata、explicit な rendering / migration decisions、project scripts または browser smoke test による verification を成果物とする。Phaser 3 のみ、または version 不明なら先に `phaser-gamedev` を使う。

## Companion Skill

この skill は `phaser-gamedev` を置き換えず、拡張する。Phaser 4 task ではまず `phaser-gamedev/SKILL.md` を必要分読み、version discovery、scene ownership、asset metadata、delta-time simulation、object lifecycle、debug visibility、verification を適用する。その後、この Phaser 4-specific skill で renderer、API、migration、WebGL decisions を扱う。

task が特に必要としない限り、追加の `phaser-gamedev` references を deep-read しない。

## 基本方針

Phaser 4 work は renderer-aware game engineering。既定 target は WebGL。Canvas は compatibility 用で、filters、real-time lighting、GPU layers、modern renderer path は WebGL 中心。まず game feel を保ち、visual / performance constraints を満たす最も単純な rendering path を選ぶ。

優先順位:

1. gameplay、input feel、scene lifecycle
2. exact asset metadata
3. filters、shaders、render targets、GPU layers より simple rendering paths
4. installed minor version に対して検証済みの Phaser 4 APIs
5. visual、input、animation、performance-sensitive changes の browser evidence

作業前に確認すること:

- installed / vendored Phaser 4 minor version
- new work、bug fix、performance pass、Phaser 3 migration のどれか
- scene ownership: objects、input、physics、UI、transitions
- asset source of truth と exact measurements
- standard objects、filters、lighting、shaders、`DynamicTexture`、`RenderTexture`、`SpriteGPULayer`、`TilemapGPULayer` のどれが必要か
- browser、mobile、DPR、pixel-art、FPS constraints

## Version / Renderer Contract

- version-specific APIs は installed Phaser version を確認してから使う
- project の local typings と installed version を generic snippets より優先する
- renderer、filter、shader、texture、migration details は exact version の official docs で確認する
- new Phaser 4 work は concrete Canvas requirement がない限り `Phaser.WEBGL`
- Phaser 3 renderer internals、custom pipelines、masks、FX、texture assumptions は audit なしに port しない
- `DynamicTexture` / `RenderTexture` drawing は通常 explicit `render()` が必要な buffered work として扱う
- filters / lighting は render passes、batching、WebGL-only constraints を変える architecture choices

Official starting points:

- `https://docs.phaser.io/api-documentation`
- `https://phaser.io/tutorials/phaser-4-rendering-concepts`
- `https://github.com/phaserjs/phaser/blob/v4.0.0/changelog/v4/4.0/CHANGELOG-v4.0.0.md`

## 参照ファイル

| Topic | File | Use When |
|-------|------|----------|
| Phaser 3 to 4 migration | [migration-hotspots.md](references/migration-hotspots.md) | removed APIs、renderer internals、masks、FX、math constants、custom pipelines |
| Spritesheets, atlases, textures | [spritesheets-and-textures.md](references/spritesheets-and-textures.md) | spritesheets、atlases、compressed textures、TileSprite、shaders、texture orientation |
| Rendering and performance | [rendering-and-performance.md](references/rendering-and-performance.md) | GPU layers、filters、lighting、render targets、batching、profiling |

## 実装前調査

```bash
rg --files | rg '(^|/)(package.json|vite.config|webpack.config|src|public|assets|static|maps|tilemaps|textures|sprites)'
rg -n "\"phaser\"|from ['\"]phaser['\"]|Phaser\\.VERSION|new Phaser\\.Game|extends Phaser\\.Scene|scene:|this\\.scene\\.|this\\.load\\.|this\\.physics|this\\.anims" .
```

migration / renderer-sensitive work:

```bash
rg -n "setTintFill|tintFill|BitmapMask|GeometryMask|preFX|postFX|ColorMatrix|Phaser\\.Geom\\.Point|Math\\.TAU|Math\\.PI2|setPipeline\\(['\"]Light2D['\"]\\)|DynamicTexture|RenderTexture|TileSprite|Shader|Pipeline|WebGLRenderer|gl\\." .
```

以下を抽出する:

- entry point、bundler、`Phaser.GameConfig`、scale mode、renderer type
- scene list、scene keys、boot/preload flow、UI overlay strategy、restart flow
- asset locations、loader keys、frame config、atlas JSON、tilesets、Tiled map names
- physics system、collision setup、input model、camera behavior、debug toggles
- typecheck、lint、tests、build、dev preview の既存 scripts

rules、controls、art direction、target platform、migration scope が欠けていて、それが実装を実質的に変える場合にのみ質問する。

## ワークフロー

1. installed version、architecture、scenes、assets、verification scripts を調べる
2. feature、bug、optimization、asset integration、migration に分類する
3. scene ownership、state flow、physics system、rendering path を決めてから code を書く
4. animations、tilemaps、UI slices、GPU layer data の前に assets を測定し loader config を固定する
5. requirement が正当化しない限り standard game objects から始める
6. collision、tile collision、animation probes、bounds overlays、FPS、batching checks など debug visibility を足す
7. scripts と browser behavior で検証する。playable changes では dev server を起動し、canvas、console、transitions、input、animation、performance を確認する

## Rendering Path Decisions

| Path | Use When | Avoid When |
|------|----------|------------|
| Standard game objects | most gameplay、UI、ordinary sprites、text、interactive entities | scene が大量の simple similar quads で支配される場合 |
| `SpriteGPULayer` | predictable animation を持つ大量の simple quads (starfields、dense background motion、particle-like decoration など) | members が rich gameplay logic、frequent structural edits、multiple texture sources、constant per-member mutation を要する場合 |
| `TilemapGPULayer` | very large orthographic tile layers、one tileset、high visible tile counts、smooth filtered tile boundaries | isometric/staggered maps、regeneration なしの frequent tile edits、multiple tilesets、small ordinary maps |
| `DynamicTexture` / `RenderTexture` | runtime compositing、capture、stamping、generated textures、multi-pass setup、reusable rendered output | plain sprite / atlas frame / tint / simple animation で済む場合 |
| Filters / lighting | effect が image-space / light-aware / mask-like で、追加 render passes に見合う場合 | art、tint、animation frames、より安価な object-level effect で同じ見た目が得られる場合 |
| Custom shaders / raw WebGL | Phaser objects / filters / supported renderer integration で表現できない effect | code が renderer state を予測不能に mutate する、または Phaser 3 pipeline internals に依存する場合 |

## Physics System Decisions

| System | Use When |
|--------|----------|
| Arcade | platformers、shooters、top-down action、tile collisions、AABB bodies、ほとんどの 2D action games |
| Matter | irregular shapes、compound bodies、sensors、constraints、physics puzzles、より realistic な collisions |
| None | menus、visual novels、puzzle boards、card games、static UI、purely visual scenes |

## Core Patterns

新規 Phaser 4 work では explicit WebGL を優先する。

```ts
const config: Phaser.Types.Core.GameConfig = {
  type: Phaser.WEBGL,
  width: 800,
  height: 600,
  roundPixels: false,
  scale: {
    mode: Phaser.Scale.FIT,
    autoCenter: Phaser.Scale.CENTER_BOTH
  },
  physics: {
    default: 'arcade',
    arcade: { gravity: { y: 300 }, debug: false }
  },
  scene: [BootScene, MenuScene, GameScene, UIScene]
};
```

scene lifecycle は明示的に保つ。

```ts
class GameScene extends Phaser.Scene {
  init(data: unknown) {}
  preload() {}
  create() {}
  update(time: number, delta: number) {
    this.player.x += this.speed * (delta / 1000);
  }
}
```

scene transitions は意図して使う。

```ts
this.scene.start('GameScene', { level: 1 });
this.scene.launch('UIScene');
this.scene.pause('GameScene');
this.scene.stop('UIScene');
```

render targets は意図して flush する。

```ts
const rt = this.add.renderTexture(0, 0, 256, 256);
rt.draw(sprite, 0, 0);
rt.render();
```

filters は WebGL-only として guard する。

```ts
sprite.enableFilters();

if (sprite.filters) {
  sprite.filters.internal.addGlow(0xffffff, 2, 0);
}
```

## Migration Replacements To Verify

| Phaser 3 Pattern | Phaser 4 Direction |
|------------------|--------------------|
| `sprite.setTintFill(color)` | `sprite.setTint(color).setTintMode(Phaser.TintModes.FILL)` |
| `Math.PI2` | `Math.TAU` |
| 旧 code で `Math.TAU` を PI / 2 として使用 | `Math.PI_OVER_2` |
| `sprite.setPipeline('Light2D')` | `sprite.setLighting(true)` |
| `preFX` / `postFX` | Phaser 4 filters |
| `BitmapMask`-style masking | Phaser 4 `Mask` filter or current filter APIs |
| `Phaser.Geom.Point` helpers | `Phaser.Math.Vector2` or new math helpers |
| Custom pipelines | Renderer `RenderNode` or supported Phaser 4 shader/filter APIs |

mechanical に置換する前に [migration-hotspots.md](references/migration-hotspots.md) を読む。

## Capabilities And Deliverables

この skill で扱うこと:

- Phaser 4 scenes、boot flows、game config、input、cameras、UI overlays、transitions の追加・refactor
- spritesheets、atlases、compressed textures、audio、tilemaps、generated assets の load / validate
- Arcade / Matter physics、collisions、overlaps、groups、pooling、debug overlays の実装
- Tiled JSON から camera bounds、collision layers、object layers、parallax を持つ tilemap-driven levels を構築
- ordinary game objects、GPU layers、render textures、filters、lighting、shaders の選択
- behavior と visual output を保ちながら Phaser 3 projects を Phaser 4 へ migration
- object churn、batch breaks、fill-rate problems、memory leaks、update-loop costs の profile / reduction

deliverables:

- 既存 framework、TypeScript style、asset paths、scene keys、naming に合う code edits
- 実装で使った measured asset constants または map property assumptions
- rendering-path、physics、migration choices の短い説明
- verification output: 実行した scripts、browser URL または smoke result、残る risk

## 避けること

| Anti-pattern | 問題 | 改善 |
|--------------|------|------|
| Phaser 4 を drop-in Phaser 3 upgrade として扱う | renderer、filters、masks、shaders、texture orientation、math constants が変わっている | まず hotspots を audit し、意図して port する |
| spritesheet / atlas metadata を推測する | off-by-one frame math が loader config から離れた箇所で animation corruption を起こす | load 前に dimensions、spacing、margin、frame names を測定する |
| shaders、filters、GPU layers から始める | 早すぎる時点で render-pass コストと debugging complexity を増やす | requirement が advanced rendering を正当化するまで standard objects を使う |
| gameplay entities を `SpriteGPULayer` に入れる | GPU layer の速度は rich object behavior ではなく constrained members から来る | interactive entities は normal objects / physics sprites のままにする |
| `TilemapGPULayer` data を regeneration なしで edit | GPU-side tile data が stale になる | edit 後に layer tile data texture を regenerate する |
| dynamic render targets の `render()` を忘れる | queued drawing commands が表示されない | texture を更新すべき箇所で `render()` を呼ぶ |
| lighting / filters を全体に適用する | shader / render target の変更が batches を壊し fill-rate を増やす | effect は視覚的に重要な objects / cameras のみに適用する |
| frame metadata 前に animation timing を debug する | 悪い frame config は skipped / mistimed animation のように見える | まず frame grid を証明する |
| raw `gl` calls で renderer state を mutate する | Phaser の renderer が desynchronize しうる | Phaser 4 APIs、`Extern`、filters、render nodes を意図して使う |

## Variation Guidance

- migration: risky APIs を先に inventory し、behavior を保ってから renderer paths を選択的に modernize する
- new small game: scenes を少なく保ち、standard objects を使い、browser で素早く verify する
- larger TS project: typed scene data、typed asset keys、service modules、focused tests を足す
- mobile target: constrained device 上で DPR、touch input、audio unlock、scale mode、memory、worst-case FPS を verify する
- pixel art: frames を測定し、適切な箇所で nearest filtering を使い、camera motion を test し、rounding を意図して適用する
- asset-heavy game: atlases / packs、preload progress、pooled objects、stable asset key naming を優先する
- performance-heavy scene: architecture を書き直す前に object count、update churn、batch breakers、fill-rate、GPU layer fit を profile する

すべての Phaser 4 project に固定の game architecture を一つだけ使うことは避ける。controls、level format、asset volume、target device、renderer constraints に形を決めさせる。

## 検証

```bash
npm run typecheck
npm run lint
npm test
npm run build
npm run dev
```

playable / visual changes では game を開いて以下を確認する:

- canvas が nonblank、正しいサイズで、console loader errors がない
- boot、preload、scene transitions、restart、UI overlays が動く
- target devices / viewport sizes で input が動く
- movement が `delta` または physics velocity を使い、可変 frame rate でも安定している
- collision bodies、tile collisions、object bounds、camera bounds が見える art と一致する
- animations が意図した frames を使い、bleeding、offset rows、skipped frames、orientation errors がない
- filters、lighting、render textures、GPU layers が意図どおり render し、target hardware で FPS を破壊しない
- object pools が inactive objects を再利用し、active bodies、timers、tweens、event listeners を leak しない

check が実行できない場合は、その理由と残る risk を正確に述べる。
