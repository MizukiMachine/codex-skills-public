---
name: love2d-gamedev
description: "LÖVE/Love2Dゲーム開発とiOSデプロイを扱う。main.lua/conf.lua、主要コールバック、ゲーム処理、アセット、.loveパッケージ化、Xcode統合で使う。"
---

# Love2D ゲーム開発

## 概要

LÖVE/Love2D (Lua) で完成度の高い 2D ゲームを作る。Xcode 経由の iOS ビルド実務も含めて扱う。

## クイックリファレンス

| トピック | 読む場面 |
|-------|---------------------|
| [Core Architecture](references/core-architecture.md) | game loop、callback、module pattern |
| [Project Structure](references/project-structure.md) | ファイル構成、`conf.lua`、配布 |
| [Graphics & Drawing](references/graphics-drawing.md) | 描画、transform、scaling |
| [Animation](references/animation.md) | sprite sheet、quad、frame timing |
| [Tiles & Maps](references/tiles-maps.md) | tile map、level loading |
| [Collision](references/collision.md) | AABB、circle、SAT pattern |
| [Audio](references/audio.md) | SFX/music、volume、pooling |
| [Libraries](references/libraries.md) | よく使う community library |
| [iOS Overview](references/ios/overview.md) | mobile workflow と落とし穴 |
| [iOS Setup](references/ios/setup.md) | Xcode/Love2D iOS source/libs、signing |
| [iOS Touch Controls](references/ios/touch-controls.md) | multitouch、virtual controls |
| [iOS Xcode Project](references/ios/xcode-project.md) | pbxproj 構造と編集 |

## 基本原則

- 移動、タイマー、アニメーションなど時間ベースの処理では `dt` を必ず使う
- アセットは `love.load()` で一度だけ読み込み、`love.update()` や `love.draw()` で読み込まない
- globals より locals と modules を優先し、状態を明示する
- UI/layout に固定ピクセルを多用せず、`love.graphics.getDimensions()` に基づいて anchor/scale する

### 最小ループ

```lua
function love.load()
  -- init + load assets
end

function love.update(dt)
  -- game logic
end

function love.draw()
  -- render
end
```

## デスクトップ開発ループ

1. 実装中はデスクトップで頻繁にゲームを実行する
2. iOS 専用コードは分離する。例: `love.system.getOS()` で gated した `touch.lua`
3. どこでも `dt` を使い、低 FPS（高負荷をシミュレート）でもプレイフィールを確認する

## iOS ビルド / デプロイループ

`.love` アーカイブの再生成と Xcode プロジェクトへのコピーには `scripts/` の helper を使う。

1. `.love` archive を作成または更新する
   - `python3 scripts/make_game_love.py --src /path/to/game --out /path/to/game.love`
2. iOS app bundle resources などの配置先へコピーする
   - `python3 scripts/sync_game_love.py --love /path/to/game.love --dest /path/to/xcode/project/resources/`
3. Xcode で build/run し、signing、deployment target、bundle resource の問題を直す

詳細とトラブルシューティングは次を読む。

- [iOS Overview](references/ios/overview.md)
- [iOS Setup](references/ios/setup.md)
- [iOS Xcode Project](references/ios/xcode-project.md)

## メモ

実装対象が上記トピックに触れる場合は、対応する参照 doc を読み、既存パターンを適用する。必要のない新規アーキテクチャを作らない。
