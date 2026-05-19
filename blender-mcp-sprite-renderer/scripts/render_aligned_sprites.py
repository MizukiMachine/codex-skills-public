#!/usr/bin/env python3
"""Render aligned game sprite sequences through Blender MCP."""

from __future__ import annotations

import argparse
import json
import re
import socket
import sys
from pathlib import Path
from typing import Any


RESULT_START = "__BLENDER_MCP_SPRITE_RENDER_RESULT_START__"
RESULT_END = "__BLENDER_MCP_SPRITE_RENDER_RESULT_END__"


def load_config(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        config = json.load(f)
    if "groups" not in config or not isinstance(config["groups"], dict):
        raise ValueError("jobs config must contain a 'groups' object")
    return config


def send_mcp(host: str, port: int, command: dict[str, Any], timeout: float) -> dict[str, Any]:
    payload = json.dumps(command).encode("utf-8")
    with socket.create_connection((host, port), timeout=min(timeout, 30.0)) as sock:
        sock.settimeout(timeout)
        sock.sendall(payload)
        data = b""
        while True:
            chunk = sock.recv(65536)
            if not chunk:
                break
            data += chunk
            try:
                return json.loads(data.decode("utf-8"))
            except json.JSONDecodeError:
                continue
    if not data:
        raise RuntimeError("Blender MCP returned no data")
    return json.loads(data.decode("utf-8"))


def extract_result(response: dict[str, Any]) -> dict[str, Any]:
    if response.get("status") != "success":
        raise RuntimeError(f"Blender MCP error: {response}")
    result = response.get("result", {})
    output = result.get("result", "") if isinstance(result, dict) else ""
    match = re.search(
        re.escape(RESULT_START) + r"\s*(\{.*\})\s*" + re.escape(RESULT_END),
        output,
        flags=re.S,
    )
    if not match:
        tail = output[-4000:] if output else ""
        raise RuntimeError(f"Could not find render result markers in Blender output:\n{tail}")
    return json.loads(match.group(1))


def blender_code(config: dict[str, Any]) -> str:
    config_json = json.dumps(config)
    return f"""
import bpy, os, glob, json, math
from mathutils import Vector

CONFIG = json.loads({config_json!r})
RESULT_START = {RESULT_START!r}
RESULT_END = {RESULT_END!r}

base_out = CONFIG.get('output_dir')
if not base_out:
    raise ValueError('CONFIG.output_dir is required')
resolution = int(CONFIG.get('resolution', 1024))
frames_per_clip = int(CONFIG.get('frames_per_clip', 16))
margin = float(CONFIG.get('margin', 1.24))
os.makedirs(base_out, exist_ok=True)
ORIGINAL_SCENE_NAME = bpy.context.scene.name if bpy.context.scene else None
TEMP_SCENE_PREFIX = '__sprite_renderer_tmp__'

def norm_path(path):
    return os.path.abspath(os.path.expanduser(path))

def set_active_scene(scene):
    if bpy.context.window:
        bpy.context.window.scene = scene

def make_temp_scene(name):
    safe_name = ''.join(ch if ch.isalnum() or ch in ('_', '-') else '_' for ch in name)
    scene = bpy.data.scenes.new(TEMP_SCENE_PREFIX + safe_name[:48])
    set_active_scene(scene)
    return scene

def restore_original_scene():
    scene = bpy.data.scenes.get(ORIGINAL_SCENE_NAME) if ORIGINAL_SCENE_NAME else None
    if scene:
        set_active_scene(scene)

def cleanup_temp_scene(scene):
    if not scene:
        return
    if bpy.context.scene == scene:
        restore_original_scene()
    for obj in list(scene.objects):
        bpy.data.objects.remove(obj, do_unlink=True)
    if scene.name in bpy.data.scenes:
        bpy.data.scenes.remove(scene, do_unlink=True)

def import_job(job):
    scene = make_temp_scene(job['name'])
    fbx_path = norm_path(job['fbx'])
    if not os.path.exists(fbx_path):
        raise FileNotFoundError(fbx_path)
    bpy.ops.import_scene.fbx(filepath=fbx_path, automatic_bone_orientation=False)
    armatures = [obj for obj in scene.objects if obj.type == 'ARMATURE']
    meshes = [obj for obj in scene.objects if obj.type == 'MESH']
    if not armatures or not meshes:
        raise RuntimeError('No armature/mesh after import: ' + fbx_path)
    arm = armatures[0]
    action = arm.animation_data.action if arm.animation_data and arm.animation_data.action else None
    if action is None:
        action = max(bpy.data.actions, key=lambda a: a.frame_range[1] - a.frame_range[0])
        arm.animation_data_create()
        arm.animation_data.action = action
    arm.name = job['name'] + '_Armature'
    for i, obj in enumerate(meshes, 1):
        obj.name = job['name'] + '_Mesh' if len(meshes) == 1 else job['name'] + '_Mesh_' + str(i).zfill(2)
    objects = [obj for obj in scene.objects if obj.type in {{'ARMATURE', 'MESH'}}]
    return scene, action, meshes, objects

def bounds_for_frame(scene, meshes, frame):
    scene.frame_set(frame)
    bpy.context.view_layer.update()
    pts = []
    for obj in meshes:
        for corner in obj.bound_box:
            pts.append(obj.matrix_world @ Vector(corner))
    if not pts:
        return Vector((0, 0, 0)), Vector((0, 0, 1))
    return (
        Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts))),
        Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts))),
    )

def animated_bounds(scene, meshes, start, end):
    mins, maxs = [], []
    for frame in range(start, end + 1):
        mn, mx = bounds_for_frame(scene, meshes, frame)
        mins.append(mn)
        maxs.append(mx)
    return (
        Vector((min(v.x for v in mins), min(v.y for v in mins), min(v.z for v in mins))),
        Vector((max(v.x for v in maxs), max(v.y for v in maxs), max(v.z for v in maxs))),
    )

def sample_frames(start, end, mode):
    duration = max(end - start, 1)
    if frames_per_clip <= 1:
        return [start]
    if mode == 'loop':
        return [start + int(round(i * duration / frames_per_clip)) for i in range(frames_per_clip)]
    return [start + int(round(i * duration / (frames_per_clip - 1))) for i in range(frames_per_clip)]

def horizontal_axis(side_axis):
    return 'y' if side_axis == 'X' else 'x'

def axis_value(vec, axis_name):
    return getattr(vec, axis_name)

def align_first_frame_anchor(scene, objects, meshes, frame, side_axis):
    mn, mx = bounds_for_frame(scene, meshes, frame)
    h_axis = horizontal_axis(side_axis)
    anchor_h = (axis_value(mn, h_axis) + axis_value(mx, h_axis)) / 2.0
    anchor_z = mn.z
    delta = Vector((0.0, -anchor_h, -anchor_z)) if h_axis == 'y' else Vector((-anchor_h, 0.0, -anchor_z))
    for obj in objects:
        obj.location += delta
    return {{
        'first_frame_anchor_axis': h_axis,
        'first_frame_anchor': {{h_axis: round(float(anchor_h), 6), 'z': round(float(anchor_z), 6)}},
        'delta': [round(float(v), 6) for v in delta],
    }}

def analyze_job(job, side_axis):
    scene, action, meshes, objects = import_job(job)
    try:
        start = int(math.floor(action.frame_range[0]))
        end = int(math.ceil(action.frame_range[1]))
        frames = sample_frames(start, end, job.get('mode', 'action'))
        alignment = align_first_frame_anchor(scene, objects, meshes, start, side_axis)
        mn_all, mx_all = animated_bounds(scene, meshes, start, end)
        return {{
            'job': job,
            'range': [start, end],
            'frames': frames,
            'alignment': alignment,
            'bounds_all': [mn_all, mx_all],
            'action_name': action.name,
        }}
    finally:
        cleanup_temp_scene(scene)

def side_params(group_name, group_config, analyses):
    side_axis = group_config.get('side_axis', 'X').upper()
    if side_axis not in ('X', 'Y'):
        raise ValueError('side_axis must be X or Y for group ' + group_name)
    all_mins = [a['bounds_all'][0] for a in analyses]
    all_maxs = [a['bounds_all'][1] for a in analyses]
    common_min = Vector((min(v.x for v in all_mins), min(v.y for v in all_mins), min(v.z for v in all_mins)))
    common_max = Vector((max(v.x for v in all_maxs), max(v.y for v in all_maxs), max(v.z for v in all_maxs)))
    common_size = common_max - common_min
    screen_width = common_size.y if side_axis == 'X' else common_size.x
    camera_depth = common_size.x if side_axis == 'X' else common_size.y
    return {{
        'group_name': group_name,
        'side_axis': side_axis,
        'center_x': float((common_min.x + common_max.x) / 2.0),
        'center_y': float((common_min.y + common_max.y) / 2.0),
        'center_z': float((common_min.z + common_max.z) / 2.0),
        'max_z': float(common_max.z),
        'camera_distance': float(max(camera_depth * 4.0, 4.0)),
        'ortho_scale': float(max(max(common_size.z, screen_width) * margin, 1.9)),
        'common_bounds': {{
            'min': [round(float(v), 4) for v in common_min],
            'max': [round(float(v), 4) for v in common_max],
            'size': [round(float(v), 4) for v in common_size],
        }},
    }}

def render_job(job, params):
    side_axis = params['side_axis']
    scene, action, meshes, objects = import_job(job)
    try:
        start = int(math.floor(action.frame_range[0]))
        end = int(math.ceil(action.frame_range[1]))
        frames = sample_frames(start, end, job.get('mode', 'action'))
        alignment = align_first_frame_anchor(scene, objects, meshes, start, side_axis)

        scene.frame_start = start
        scene.frame_end = end
        scene.render.fps = int(CONFIG.get('fps', 30))
        scene.render.resolution_x = resolution
        scene.render.resolution_y = resolution
        scene.render.resolution_percentage = 100
        scene.render.film_transparent = True
        scene.render.image_settings.file_format = 'PNG'
        scene.render.image_settings.color_mode = 'RGBA'
        scene.render.image_settings.color_depth = '8'
        scene.render.image_settings.compression = int(CONFIG.get('png_compression', 15))
        try:
            scene.render.engine = 'BLENDER_EEVEE_NEXT'
        except Exception:
            try:
                scene.render.engine = 'BLENDER_EEVEE'
            except Exception:
                pass

        bpy.ops.object.camera_add()
        cam = bpy.context.object
        cam.name = job['name'] + '_Aligned_Side_Camera'
        scene.camera = cam
        cam.data.type = 'ORTHO'
        cam.data.ortho_scale = params['ortho_scale']

        bpy.ops.object.light_add(type='AREA')
        light = bpy.context.object
        light.name = job['name'] + '_Aligned_Key_Light'
        light.data.type = 'AREA'
        light.data.energy = float(CONFIG.get('light_energy', 800))
        light.data.size = float(CONFIG.get('light_size', 3.2))
        target = Vector((params['center_x'], params['center_y'], params['center_z']))

        def set_side_camera(sign):
            if side_axis == 'X':
                cam.location = Vector((params['center_x'] + sign * params['camera_distance'], params['center_y'], params['center_z']))
                light.location = Vector((params['center_x'] + sign * min(params['camera_distance'] * 0.75, 3.0), params['center_y'] - 1.0, params['max_z'] + 1.0))
            else:
                cam.location = Vector((params['center_x'], params['center_y'] + sign * params['camera_distance'], params['center_z']))
                light.location = Vector((params['center_x'] - 1.0, params['center_y'] + sign * min(params['camera_distance'] * 0.75, 3.0), params['max_z'] + 1.0))
            cam.rotation_euler = (target - cam.location).to_track_quat('-Z', 'Y').to_euler()

        def render_side(label, sign):
            out_dir = os.path.join(base_out, params['group_name'], job['name'], label)
            os.makedirs(out_dir, exist_ok=True)
            prefix = job['name'] + '_' + label + '_'
            for path in glob.glob(os.path.join(out_dir, prefix + '*.png')):
                try:
                    os.remove(path)
                except OSError:
                    pass
            set_side_camera(sign)
            rendered = []
            for idx, src_frame in enumerate(frames, 1):
                scene.frame_set(src_frame)
                bpy.context.view_layer.update()
                filepath = os.path.join(out_dir, prefix + str(idx).zfill(4) + '.png')
                scene.render.filepath = filepath
                bpy.ops.render.render(write_still=True)
                rendered.append(filepath)
            return {{'label': label, 'output_dir': out_dir, 'file_count': len(rendered), 'first_file': rendered[0], 'last_file': rendered[-1]}}

        return {{
            'name': job['name'],
            'mode': job.get('mode', 'action'),
            'source_fbx': norm_path(job['fbx']),
            'source_action': action.name,
            'source_action_range': [start, end],
            'sample_frames': frames,
            'alignment': alignment,
            'results': [render_side('right_view', 1), render_side('left_view', -1)],
        }}
    finally:
        cleanup_temp_scene(scene)

final = {{
    'base_output_dir': base_out,
    'resolution': [resolution, resolution],
    'frames_per_clip': frames_per_clip,
    'alignment_rule': 'shared camera per character group; first-frame foot center and ground aligned before measurement and rendering',
    'groups': [],
}}

for group_name, group_config in CONFIG['groups'].items():
    if isinstance(group_config, list):
        group_config = {{'side_axis': 'X', 'jobs': group_config}}
    jobs = group_config.get('jobs', [])
    if not jobs:
        continue
    side_axis = group_config.get('side_axis', 'X').upper()
    analyses = [analyze_job(job, side_axis) for job in jobs]
    params = side_params(group_name, group_config, analyses)
    rendered = [render_job(job, params) for job in jobs]
    final['groups'].append({{'group': group_name, 'params': dict(params), 'jobs': rendered}})

restore_original_scene()

print(RESULT_START)
print(json.dumps(final, ensure_ascii=False))
print(RESULT_END)
"""


def main() -> int:
    parser = argparse.ArgumentParser(description="Render aligned game sprites via Blender MCP.")
    parser.add_argument("--jobs-file", required=True, type=Path, help="Path to JSON job configuration.")
    parser.add_argument("--host", help="Override Blender MCP host.")
    parser.add_argument("--port", type=int, help="Override Blender MCP port.")
    parser.add_argument("--timeout-seconds", type=float, help="Override MCP timeout.")
    args = parser.parse_args()

    config = load_config(args.jobs_file)
    mcp_config = dict(config.get("mcp", {}))
    host = args.host or mcp_config.get("host", "127.0.0.1")
    port = args.port or int(mcp_config.get("port", 9876))
    timeout = args.timeout_seconds or float(mcp_config.get("timeout_seconds", 3600))

    response = send_mcp(host, port, {"type": "execute_code", "params": {"code": blender_code(config)}}, timeout)
    result = extract_result(response)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
