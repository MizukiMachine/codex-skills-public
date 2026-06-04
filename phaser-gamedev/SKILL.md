---
name: phaser-gamedev
description: "Phaser 3/4の2Dブラウザゲームを構築・デバッグ・最適化する。シーン、入力、物理、タイルマップ、UI、アニメーション、移行相談で使う。"
---

# Phaser Game Development

## 目的

Phaser browser games の実装、debug、optimization、migration を、codebase-aware な判断で行う。working game code、asset metadata、focused tests / smoke checks、Phaser version と verification の短い summary を出す。

## 基本方針

Phaser の品質は3つの contract で決まる。exact asset metadata、clear scene ownership、frame-rate independent simulation。

優先順位:

1. 正しい gameplay と input feel
2. 測定済み asset dimensions と stable loader keys
3. gameplay、UI、menus、loading を分ける scene boundaries
4. profiling / visual checks に基づく browser/mobile performance
5. 既存 project style に合う小さく戻しやすい変更

作業前に確認すること:

- installed / vendored Phaser major/minor
- source of truth の assets と exact dimensions、spacing、margin、frame names、Tiled properties
- mechanic に合う physics: Arcade、Matter、なし
- どの scene がどの object を所有し、state が scene transitions をどう跨ぐか
- every frame に churn する objects や pooling が必要な spawn/despawn は何か

## Version Contract

Phaser game だからといって Phaser 3 API と仮定しない。version-specific APIs を使う前に installed / vendored version を確認する。

```bash
rg -n "\"phaser\"|from ['\"]phaser['\"]|Phaser\\.VERSION|new Phaser\\.Game" . -g 'package.json' -g '*lock*' -g 'src/**' -g 'public/**' -g 'assets/**'
```

no matches は vendored bundles、HTML script tags、runtime `Phaser.VERSION` を調べる signal。

| Project state | Rule |
|---------------|------|
| Phaser 4.x | WebGL-focused patterns を優先。v3 renderer pipelines、masks、FX、tint fill、camera internals、DynamicTexture timing は migration-sensitive。`references/versioning-migration.md` を読む |
| Phaser 3.x | matching 3.x docs/examples を使う。built-in `NineSlice` は 3.60+ で優先し、WebGL needs を確認 |
| Unknown version | dependency、vendored banner、`Phaser.VERSION` を見つけるまで API-sensitive edit をしない |
| migration request | gameplay logic 変更前に removed APIs と custom rendering を inventory する |

current API details が重要な場合は memory ではなく exact major/minor の official Phaser docs を確認する。

## 実装前調査

```bash
rg --files | rg '(^|/)(package.json|vite.config|src|public|assets|static|maps|tilemaps|textures|sprites)'
rg -n "class .*Scene|extends Phaser\\.Scene|scene:|this\\.scene\\.|this\\.load\\.|this\\.physics|this\\.anims|tilemap|nineslice|NineSlice|Matter|Arcade" .
```

抽出するもの:

- entry point と `Phaser.GameConfig`
- scene list、scene keys、transition flow
- asset locations、loader keys、spritesheet frame configs、atlas formats、Tiled map names
- input model、camera/scale mode、physics system、debug toggles
- typecheck、lint、test、build、dev preview scripts

rules、controls、art direction、target platform の欠落で実装が大きく変わる場合だけ、1-2問確認する。

## ワークフロー

1. version、architecture、assets を調べる
2. content を追加する前に scene / state model を選ぶか維持する
3. animation、tilemap、UI 作成前に assets を測定し loader config を固定する
4. delta-time movement、explicit physics bodies、stable object lifecycle で gameplay を実装する
5. fragile systems には collision bodies、tile collision、animation test scenes、FPS、bounds overlays などの debug visibility を足す
6. repo scripts と browser smoke test で検証する

## 参照ファイル

| Topic | File | Use When |
|-------|------|----------|
| Phaser 3/4 compatibility and migration | `references/versioning-migration.md` | version-specific APIs、Phaser 3 to 4 migration、renderer/filter/camera/tint changes |
| Spritesheets, animation frames, UI slicing | `references/spritesheets-nineslice.md` | spritesheets、frames、atlases、nine-slice panels |
| Tiled tilemaps and collision layers | `references/tilemaps.md` | JSON maps、tilesets、object layers、collisions、cameras、parallax |
| Arcade physics tuning and pooling | `references/arcade-physics.md` | Arcade bodies、colliders、overlaps、groups、debug rendering |
| Performance and profiling | `references/performance.md` | FPS drops、object churn、draw calls、memory leaks、update-loop costs |

## Capabilities / Deliverables

- Phaser scenes、game config、input、cameras、UI overlays、scene transitions の追加 / refactor
- spritesheets、texture atlases、audio、tilemaps、generated assets の load / validate
- Arcade / Matter physics、collision callbacks、groups、pooling、debug visualization
- Tiled JSON から collision / object layers 付き levels を構築
- object churn、draw calls、memory leaks、expensive update work の profiling / reduction
- Phaser 3 から Phaser 4 への migration

成果物:

- existing framework、TypeScript style、asset paths、naming に合う code edits
- measured asset constants と map property assumptions
- scripts run、browser URL / screenshot check、remaining risk を含む verification output

## Core Patterns

### Game Configuration

```ts
const config: Phaser.Types.Core.GameConfig = {
  type: Phaser.AUTO,
  width: 800,
  height: 600,
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

### Scene Lifecycle

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

### Scene Transitions

```ts
this.scene.start('GameScene', { level: 1 });
this.scene.launch('UIScene');
this.scene.pause('GameScene');
this.scene.stop('UIScene');
```

## Architecture Decisions

### Physics System

| System | Use When |
|--------|----------|
| Arcade | platformers、shooters、top-down action、AABB collision games |
| Matter | physics puzzles、irregular shapes、sensors、constraints |
| None | menus、visual novels、card games、puzzle UIs、static interactive screens |

### Scene Structure

```text
scenes/
  BootScene.ts
  MenuScene.ts
  GameScene.ts
  UIScene.ts
  GameOverScene.ts
```

global `window` state より scene data、registries、services、typed game-state modules を優先する。

## 避けること

| Anti-pattern | Why It Fails | Better |
|--------------|--------------|--------|
| Phaser version を推測 | Phaser 3/4 は renderer、filters、camera、tint、texture behavior が違う | dependency または `Phaser.VERSION` を確認 |
| spritesheet dimensions を推測 | off-by-one frame math が animation を壊す | dimensions、spacing、margin を測定 |
| assets を `create()` で load | unloaded textures を参照し得る | `preload()` または Boot scene |
| `update()` で objects を生成 | GC pauses と frame spikes | pre-create または group pooling |
| movement を frame count で管理 | FPS で game speed が変わる | `delta / 1000` または physics velocity |
| 1巨大 scene | menus、HUD、gameplay、transitions が結合する | lifecycle / ownership で split |
| simple AABB に Matter | 不必要な複雑化 | irregular shapes まで Arcade |
| invisible collision setup | tile/body 問題が推測になる | debug graphics / toggles を追加 |

## Variation Guidance

- small jam game: scenes は少なく、simple constants、browser verification
- larger TypeScript project: typed asset keys、typed scene data、focused modules
- mobile target: scale mode、touch input、DPR、audio unlock、low-power FPS
- pixel art: `pixelArt`、camera rounding、nearest-neighbor CSS、integer scaling
- asset-heavy game: atlases、manifests、preload progress、pooled objects
- Phaser 4: current WebGL/filter/rendering patterns、v3 renderer internals は避ける

controls、level format、physics complexity、asset volume、target platform に合わせ、すべての game に同じ architecture を使わない。

## 検証

```bash
npm run typecheck
npm run lint
npm test
npm run build
npm run dev
```

playable changes では game を開き、次を確認する。

- canvas が nonblank で desktop/mobile widths で正しい
- main scene、transitions、loader errors
- movement が delta または physics velocity を使い variable frame rates で安定
- collision bodies、tile collision、bounds が visible art と一致
- animations の frames、bleeding、offsets、skipped rows
- object pools が inactive objects を再利用し active bodies を leak しない
- busiest moment の FPS / memory が安定

check が実行できない場合は理由と残る risk を明記する。
