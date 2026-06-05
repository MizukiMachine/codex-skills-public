---
name: blender-mcp-sprite-renderer
description: "Blender MCPでMixamo/FBXキャラクターを2Dゲーム用スプライトPNGとしてレンダリングする。解像度とキャプチャ規則を確認し、横視点フレームの書き出し、整列、正規化、プレビューに使う。"
---

# Blender MCP Sprite Renderer

## 目的

Blender MCP を使い、FBX character animation clips を aligned 2D game sprite sequences に変換する。既定 target は side-scroller sprites: square transparent PNGs、left/right side views、clip ごと 16 frames、character ごとに all actions で stable framing。

repeatability のため同梱 script を優先する。

```text
scripts/render_aligned_sprites.py
```

## Mandatory Preflight

この skill が呼ばれた後の最初の user-facing step は、必ず image resolution confirmation にする。user が resolution を選択または確認するまで、executable job configs の作成、FBX import、Blender MCP jobs、rendering を行わない。

resolution question は numbered options と recommended choice で聞く。

```text
画像解像度を選んでください。これはPNGキャンバスのピクセル数です。キャラクターを大きく写すためのカメラ倍率や余白marginの変更とは別設定です。

1. 1024x1024（推奨・標準）
2. 1536x1536（高解像度・ファイルサイズ中）
3. 2048x2048（最高品質・ファイルサイズ大）
4. カスタム解像度を指定
```

user が `1024x1024` などを既に指定していても、job creation、FBX import、rendering 前に最終確認する。

```text
指定解像度は 1024x1024 です。この解像度で開始してよいですか？
1. はい、この解像度で開始する
2. 解像度を変更する
```

resolution は square output canvas size in pixels として扱う。higher resolution を character zoom として説明しない。character を frame 内で大きく/小さくしたい場合は、resolution 確認後に camera framing、orthographic scale、`margin` を別設定として扱う。

resolution 確認後、残りの capture rules を numbered options で聞き、回答を待つ。local filenames を inspect して better choices を提案するのはよいが、resolution と capture rules の承認前に executable job configs や import/render operations は作らない。

user が詳細設定を既に渡している場合も、resolution confirmation の後に設定を要約して確認する。

```text
この設定で撮影を開始してよいですか？
1. はい、この設定で開始する
2. 設定を変更する
```

user の言語が日本語なら preflight questions は日本語で行う。

remaining capture rules の default questionnaire:

```text
撮影ルールを選んでください。

1. 出力仕様
   1. 透明PNG / 16枚 / 左右ビュー（推奨）
   2. 枚数やビュー構成を変更する

2. 位置合わせ
   1. キャラクター単位で共通カメラ・足元中心・地面基準を揃える（推奨）
   2. アクションごとに個別に画面いっぱいへ収める

3. アニメーション種別
   1. ファイル名から loop/action を推定する（Idle/Walkはloop、Attack/Deathはaction）
   2. すべてloopとして扱う
   3. すべてactionとして扱う

4. 横向き判定
   1. side_axis=X で撮る（Mixamoでまず試す推奨）
   2. side_axis=Y で撮る
   3. 先に1枚だけテスト出力して確認する

5. 出力対象
   1. 指定されたFBXだけ
   2. 同じキャラクター名のFBXをまとめて処理する

6. Blenderシーンの扱い
   1. レンダー用の一時シーンを作って処理し、元のシーンへ戻す（推奨）
   2. 現在のシーンをクリアしてよい
```

user 回答後、final config を短く restate し、executable job configs、FBX import、rendering 前に final start confirmation を取る。recommended temporary-scene behavior では bundled script をそのまま使う。

## Required Behavior

default output contract:

- transparent background の PNG
- user が別 resolution を明示確認しない限り `1024x1024`
- resolution は PNG canvas pixels のみ。camera zoom、character scale、orthographic scale、`margin` は変えない
- user 指定がなければ animation ごとに `16` frames
- clip ごとに `right_view` / `left_view` directories
- orthographic side camera。perspective、top-down、3/4、front/back ではない
- same character group では all actions に one shared camera center / orthographic scale
- action ごとに camera fit しない。game animation popping の原因になる
- imported FBX は first-frame foot/ground anchor で align してから measure/render
- `idle`、`walk`、`run` は loop として evenly sample、duplicated endpoint を除外
- `attack`、`slash`、`impact`、`hit`、`death` は action として start/final pose を含める

## ワークフロー

1. mandatory resolution question を聞き、回答を待つ
2. remaining preflight questions を聞き、回答を待つ
3. resolution、PNG transparency、frame count、views、side axis、alignment、loop/action handling、temporary-scene behavior を含む final config を restate し、final start confirmation を取る
4. Blender MCP が reachable か確認。不可なら local MCP addon/script 付きで Blender を起動して retry
5. FBX files を identify し、action ではなく character で group 化する。例: すべての `Zombie *.fbx` を1グループ、すべての `Sword And Shield *.fbx` を別グループ
6. selected rule に従い clip を `loop` / `action` に分類
7. user が承認した後だけ `references/job-config.md` に従い jobs JSON を作る
8. final start confirmation 後だけ `scripts/render_aligned_sprites.py --jobs-file <jobs.json>` を実行
9. group ごとに first frame と large-motion frame を少なくとも1枚 inspect
10. front/back なら alternate `side_axis` で rerun するか確認

## Preview / Test Output

user が "先に1枚だけテスト出力して確認する" を選んだ場合、full set を先に render しない。

temporary preview job:

- character group ごとに representative action 1つ。可能なら `idle` または `walk`
- `frames_per_clip = 1`
- full run と同じ `resolution`、`side_axis`、grouping、alignment、output rules
- output directory は `_preview` suffix
- `right_view` と `left_view` の両方

確認項目:

1. true side view か
2. `right_view` / `left_view` naming が許容か
3. feet/ground position と character scale が許容か

full sequence は preview approval 後だけ。

## Alignment Rules

character group ごと:

1. 各 FBX を独立に import
2. 各 FBX の first action frame を evaluate
3. screen-horizontal axis の first-frame foot center を `0`、first-frame ground/bottom `Z` を `0` に move
4. anchor alignment 後、全 actions の全 frames を measure
5. character group 全体の common bounding box を compute
6. common bounding box から all actions に one orthographic camera scale / target を使う

これで `idle -> walk -> attack -> death` transitions が安定する。

## Side View Axis

script は group ごとに `side_axis` を support する。

- `X`: cameras on `+X` / `-X`; screen horizontal は world `Y`; vertical は world `Z`
- `Y`: cameras on `+Y` / `-Y`; screen horizontal は world `X`; vertical は world `Z`

この project の Mixamo cases ではまず `X` を試す。front/back なら同じ jobs を `side_axis: "Y"` で rerun する。

`right_view` が anatomical right side を常に意味すると約束しない。選択された `side_axis` の positive side から render した view を意味する。game logic / asset naming で重要なら preview で確認する。

## Output Layout

```text
output_dir/
  character_group/
    action_name/
      right_view/
        action_name_right_view_0001.png
        ...
        action_name_right_view_0016.png
      left_view/
        action_name_left_view_0001.png
        ...
        action_name_left_view_0016.png
```

## Example Mapping

user request:

```text
Use Blender MCP to render Zombie Idle, Zombie Walk, and Zombie Attack as game sprites.
```

jobs example:

```json
{
  "output_dir": "C:/Users/negic/Documents/blender/renders/aligned_1024_game_sprites",
  "resolution": 1024,
  "frames_per_clip": 16,
  "groups": {
    "zombie": {
      "side_axis": "X",
      "jobs": [
        {"name": "zombie_idle", "fbx": "C:/Users/negic/Downloads/Zombie Idle.fbx", "mode": "loop"},
        {"name": "zombie_walk", "fbx": "C:/Users/negic/Downloads/Zombie Walk.fbx", "mode": "loop"},
        {"name": "zombie_attack", "fbx": "C:/Users/negic/Downloads/Zombie Attack.fbx", "mode": "action"}
      ]
    }
  }
}
```

run:

```powershell
& "<python>" "<skill-dir>\scripts\render_aligned_sprites.py" --jobs-file "<jobs.json>"
```

available なら workspace bundled Python を使う。
