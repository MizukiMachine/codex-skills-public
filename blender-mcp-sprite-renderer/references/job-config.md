# Job Configuration

Create a JSON file and pass it to `scripts/render_aligned_sprites.py --jobs-file`.

Before creating and executing this config, ask the user to choose or confirm the capture rules. Do not render immediately just because the skill was invoked.

Before creating this config, always confirm image resolution with numbered options. This is required even when the user already wrote a resolution such as `1024x1024`; ask whether to start with that resolution or change it. Do not create executable job JSON, import FBX files, create Blender MCP jobs, or render until the user has chosen or confirmed the resolution.

Use these resolution choices unless the user has already provided a custom set:

```text
1. 1024x1024（推奨・標準）
2. 1536x1536（高解像度・ファイルサイズ中）
3. 2048x2048（最高品質・ファイルサイズ大）
4. カスタム解像度を指定
```

Resolution is only the square PNG canvas size in pixels. It is separate from camera zoom, orthographic scale, character size in frame, and `margin`. If the user wants the character to appear larger, keep that as a separate camera/framing decision after resolution is confirmed.

Use the bundled script's default scene behavior unless the user explicitly asks otherwise: it creates temporary Blender scenes for import/render work and restores the original scene after finishing. Do not use a workflow that clears the user's active Blender scene unless the user explicitly confirms that is acceptable.

## Minimal Shape

```json
{
  "output_dir": "C:/path/to/output",
  "resolution": 1024,
  "frames_per_clip": 16,
  "mcp": {
    "host": "127.0.0.1",
    "port": 9876,
    "timeout_seconds": 3600
  },
  "groups": {
    "character_group_name": {
      "side_axis": "X",
      "jobs": [
        {
          "name": "clip_name",
          "fbx": "C:/path/to/Clip.fbx",
          "mode": "loop"
        }
      ]
    }
  }
}
```

## Fields

- `output_dir`: Parent output directory.
- `resolution`: Square output canvas size in pixels. Default: `1024`. Must be chosen or confirmed by the user before this config is created for execution.
- `frames_per_clip`: Number of rendered PNG frames per animation. Default: `16`.
- `mcp.host`: Blender MCP host. Default: `127.0.0.1`.
- `mcp.port`: Blender MCP port. Default: `9876`.
- `groups`: Object keyed by character group. Each group receives one shared camera and framing.
- `side_axis`: Use `X` when cameras should be placed at `+X/-X`; use `Y` for `+Y/-Y`.
- `jobs[].name`: Safe output name, lowercase with underscores recommended.
- `jobs[].fbx`: Absolute or workspace-resolvable FBX path.
- `jobs[].mode`: `loop` or `action`.

## Mode Selection

Use `loop` for:

- idle
- walk
- run
- breathing
- patrol cycles

Use `action` for:

- attack
- slash
- impact
- hit
- death
- dying
- jump, if it should play once

If the user has not specified mode handling, ask whether to infer modes from filenames, force all clips to `loop`, or force all clips to `action`.

## Preview Config

When the user wants to confirm the side view before the full render:

- Use one representative FBX per character group.
- Set `frames_per_clip` to `1`.
- Set `output_dir` to a separate path ending in `_preview`.
- Keep the same `side_axis`, `resolution`, and grouping rules intended for the full render.
- Render both `right_view` and `left_view`, then ask the user to approve the view and naming before rendering all clips.

## Example

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
        {"name": "zombie_death", "fbx": "C:/Users/negic/Downloads/Zombie Death.fbx", "mode": "action"}
      ]
    },
    "sword_and_shield": {
      "side_axis": "X",
      "jobs": [
        {"name": "sword_and_shield_idle", "fbx": "C:/Users/negic/Downloads/Sword And Shield Idle.fbx", "mode": "loop"},
        {"name": "sword_and_shield_slash", "fbx": "C:/Users/negic/Downloads/Sword And Shield Slash.fbx", "mode": "action"}
      ]
    }
  }
}
```
