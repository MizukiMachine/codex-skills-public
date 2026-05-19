---
name: blender-mcp-sprite-renderer
description: Render Mixamo or FBX character animations into game-ready 2D sprite PNG sequences through Blender MCP, but always ask the user to choose or confirm image resolution first, then capture rules, before importing/rendering. Use when the user asks Codex to use Blender/Blender MCP to capture, render, batch export, align, normalize, preview, or re-render side-view animation frames for games, especially 1024x1024 transparent PNG sprites with consistent character size, first-frame anchor, camera framing, left/right views, loop clips, or one-shot action clips.
---

# Blender MCP Sprite Renderer

## Purpose

Use Blender MCP to convert FBX character animation clips into aligned 2D game sprite sequences. The default target is side-scroller sprites: square transparent PNGs, left/right side views, 16 frames per clip, and stable per-character framing across all actions.

Prefer the bundled script for repeatability:

```text
scripts/render_aligned_sprites.py
```

## Mandatory Preflight

The first user-facing step after this skill is invoked must be an image resolution confirmation. Do not create job configs for execution, import FBX files into Blender, create Blender MCP jobs, or render anything until the user has chosen or confirmed the resolution.

Ask the resolution question with numbered options and an explicit recommended choice:

```text
画像解像度を選んでください。これはPNGキャンバスのピクセル数です。キャラクターを大きく写すためのカメラ倍率や余白marginの変更とは別設定です。

1. 1024x1024（推奨・標準）
2. 1536x1536（高解像度・ファイルサイズ中）
3. 2048x2048（最高品質・ファイルサイズ大）
4. カスタム解像度を指定
```

If the user already specified a resolution such as `1024x1024`, still ask for final confirmation before any job creation, FBX import, or rendering:

```text
指定解像度は 1024x1024 です。この解像度で開始してよいですか？
1. はい、この解像度で開始する
2. 解像度を変更する
```

Treat resolution as the square output canvas size in pixels. Do not present higher resolution as a way to zoom the character in. If the user wants the character to appear larger or smaller within the frame, discuss camera framing, orthographic scale, or `margin` separately after the resolution is confirmed.

Do not start importing FBX files, creating job configs for execution, or rendering immediately when this skill is invoked. After the resolution is chosen or confirmed, ask the user what remaining capture rules to use, present numbered options, and wait for their answer.

It is acceptable to inspect local filenames to offer better choices, but do not create executable job configs or run Blender import/render operations until the user confirms the resolution and capture rules.

If the user already gave detailed settings, still summarize them and ask for confirmation after the separate resolution confirmation:

```text
この設定で撮影を開始してよいですか？
1. はい、この設定で開始する
2. 設定を変更する
```

When the user's language is Japanese, ask the preflight questions in Japanese.

After the resolution is chosen or confirmed, use this concise setup questionnaire for the remaining capture rules unless the user already answered part of it:

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

After the user answers, restate the final config briefly and ask one final start confirmation before creating executable job configs, importing FBX files, or rendering. If the user chooses the recommended temporary-scene behavior, use the bundled script as-is; it creates temporary Blender scenes and restores the original scene when finished.

## Required Behavior

Default output contract:

- PNG with transparent background.
- `1024 x 1024` square images unless the user explicitly confirms another resolution.
- Resolution controls PNG canvas pixels only; it does not change camera zoom, character scale in frame, orthographic scale, or `margin`.
- `16` output frames per animation unless the user specifies another count.
- `right_view` and `left_view` directories for each clip.
- Orthographic side camera, not perspective camera.
- True character side view, not top-down, 3/4, front, or back view.
- Same character group uses one shared camera center and one shared orthographic scale for all actions.
- Do not fit camera per action; that causes game animation popping.
- Align each imported FBX by its first-frame foot/ground anchor before measuring and rendering.
- Treat `idle`, `walk`, `run`, and similar cyclic motions as loops: sample evenly and exclude the duplicated endpoint.
- Treat `attack`, `slash`, `impact`, `hit`, `death`, `dying`, and similar actions as one-shot clips: sample from start through final pose, including both endpoints.

## Workflow

1. Ask the mandatory image resolution question and wait until the user chooses or confirms a resolution.
2. Ask the remaining mandatory preflight questions and wait for the user's answers.
3. Restate the final config, including resolution, transparent PNG, frame count, views, side axis, alignment, loop/action handling, and temporary-scene behavior. Ask for final start confirmation.
4. Confirm Blender MCP is reachable. If it is not, start Blender with the local MCP addon/script, then retry.
5. Identify FBX files and group them by character, not by action. Examples: all `Zombie *.fbx` in one group; all `Sword And Shield *.fbx` in another group.
6. Classify each clip as `loop` or `action` according to the user's selected rule.
7. Create a jobs JSON file following `references/job-config.md` only after the user has approved the resolution and capture rules.
8. Run `scripts/render_aligned_sprites.py --jobs-file <jobs.json>` only after the user has approved the final start confirmation.
9. Inspect at least one first frame from each group and one large-motion frame from each action.
10. If the output is front/back instead of side view, ask whether to rerun with the alternate `side_axis` in the group config.

## Preview/Test Output

If the user chooses "先に1枚だけテスト出力して確認する", do not render the full set first.

Use a temporary preview job:

- Use only one representative action per character group, preferably `idle` or `walk` if available.
- Set `frames_per_clip` to `1`.
- Keep the same `resolution`, `side_axis`, grouping, alignment, and output rules that would be used for the full run.
- Write to an output directory ending in `_preview`.
- Render both `right_view` and `left_view`.
- Ask the user to confirm:
  1. whether the view is truly from the character side,
  2. whether `right_view` and `left_view` naming is acceptable,
  3. whether the feet/ground position and character scale are acceptable.

Only render the full sequence after the user approves the preview.

## Alignment Rules

For each character group:

1. Import every FBX independently.
2. For each FBX, evaluate its first action frame.
3. Move the character so the first-frame foot center on the screen-horizontal axis is at `0`, and the first-frame ground/bottom `Z` is at `0`.
4. Measure all frames of all actions after that anchor alignment.
5. Compute one common bounding box for the whole character group.
6. Use the common bounding box to set one orthographic camera scale and one camera target for every action in the group.

This keeps `idle -> walk -> attack -> death` transitions visually stable in a game.

## Side View Axis

The script supports `side_axis` per character group:

- `X`: cameras are placed on `+X` and `-X`; screen horizontal is world `Y`; vertical is world `Z`.
- `Y`: cameras are placed on `+Y` and `-Y`; screen horizontal is world `X`; vertical is world `Z`.

Use `X` first for the Mixamo cases from this project. If the rendered result shows the character's front or back instead of the side, rerun the same jobs with `side_axis: "Y"`.

Do not promise that `right_view` always means the anatomical right side of the character. It means the view rendered from the positive side of the selected `side_axis`. Confirm the naming with a preview when correctness matters for game logic or asset naming.

## Output Layout

Use this directory structure:

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

## Example User Request Mapping

If the user says:

```text
Use Blender MCP to render Zombie Idle, Zombie Walk, and Zombie Attack as game sprites.
```

Build jobs like:

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

Then run:

```powershell
& "<python>" "<skill-dir>\scripts\render_aligned_sprites.py" --jobs-file "<jobs.json>"
```

Use the workspace bundled Python when available.
