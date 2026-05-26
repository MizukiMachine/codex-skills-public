#!/usr/bin/env python3
"""Run Hugo-Dz/spritefusion-pixel-snapper on a local image."""

from __future__ import annotations

import argparse
import binascii
import math
import os
import shutil
import subprocess
import struct
import zlib
from pathlib import Path


REPO_URL = "https://github.com/Hugo-Dz/spritefusion-pixel-snapper.git"
VERIFIED_REF = "9f1ccdf0496d0eb2e6b343b6385f4cb42cf36a36"
NO_REF_VALUES = {"", "none", "skip", "false", "no"}
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
PNG_RGBA_BYTES_PER_PIXEL = 4


def default_repo_dir() -> Path:
    env_repo = os.environ.get("SPRITEFUSION_PIXEL_SNAPPER_REPO")
    if env_repo:
        return Path(env_repo).expanduser()
    cache_root = os.environ.get("LOCALAPPDATA")
    if cache_root:
        return Path(cache_root) / "Codex" / "spritefusion-pixel-snapper"
    return Path.home() / ".cache" / "codex" / "spritefusion-pixel-snapper"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Pixel-snap an image with Sprite Fusion Pixel Snapper."
    )
    parser.add_argument("--input", "-i", required=True, help="Input image path.")
    parser.add_argument("--output", "-o", required=True, help="Output PNG path.")
    parser.add_argument(
        "--colors",
        "-k",
        type=int,
        default=None,
        help="Optional k-colors palette size. Upstream default is 16.",
    )
    parser.add_argument(
        "--pixel-size",
        type=float,
        default=None,
        help="Optional pixel-size override when auto-detection is wrong.",
    )
    parser.add_argument(
        "--repo",
        type=Path,
        default=None,
        help="Path to an existing spritefusion-pixel-snapper checkout.",
    )
    parser.add_argument(
        "--repo-url",
        default=REPO_URL,
        help="Git URL to clone when the repo is missing.",
    )
    parser.add_argument(
        "--ref",
        default=os.environ.get("SPRITEFUSION_PIXEL_SNAPPER_REF", VERIFIED_REF),
        help="Git ref to checkout before running. Use 'none' to skip checkout.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the Cargo command without executing it.",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Use cargo run without --release.",
    )
    aspect_group = parser.add_mutually_exclusive_group()
    aspect_group.add_argument(
        "--preserve-aspect",
        dest="preserve_aspect",
        action="store_true",
        default=True,
        help=(
            "Pad the output PNG canvas with transparent pixels when needed so "
            "the final dimensions keep the input image aspect ratio. This is the default."
        ),
    )
    aspect_group.add_argument(
        "--no-preserve-aspect",
        dest="preserve_aspect",
        action="store_false",
        help="Keep the upstream output dimensions exactly, even if the aspect ratio changes.",
    )
    return parser.parse_args()


def require_executable(name: str) -> None:
    if shutil.which(name) is None:
        raise SystemExit(f"Required executable not found on PATH: {name}")


def should_checkout_ref(ref: str | None) -> bool:
    if ref is None:
        return False
    return ref.strip().lower() not in NO_REF_VALUES


def checkout_repo_ref(repo: Path, ref: str | None, dry_run: bool) -> None:
    if not should_checkout_ref(ref) or dry_run:
        return

    require_executable("git")
    rev_parse = subprocess.run(
        ["git", "-C", str(repo), "rev-parse", "--is-inside-work-tree"],
        capture_output=True,
        text=True,
    )
    if rev_parse.returncode != 0:
        raise SystemExit(
            f"Cannot checkout --ref {ref!r}: {repo} is not a git working tree. "
            "Pass --ref none or provide a git checkout."
        )

    checkout = subprocess.run(
        ["git", "-C", str(repo), "checkout", "--quiet", ref],
        capture_output=True,
        text=True,
    )
    if checkout.returncode == 0:
        return

    fetch = subprocess.run(
        ["git", "-C", str(repo), "fetch", "--quiet", "--tags", "origin", ref],
        capture_output=True,
        text=True,
    )
    if fetch.returncode == 0:
        fetched_checkout = subprocess.run(
            ["git", "-C", str(repo), "checkout", "--quiet", "FETCH_HEAD"],
            capture_output=True,
            text=True,
        )
        if fetched_checkout.returncode == 0:
            return

    details = checkout.stderr.strip() or fetch.stderr.strip() or "unknown git error"
    raise SystemExit(f"Failed to checkout --ref {ref!r} in {repo}: {details}")


def ensure_repo(repo: Path, repo_url: str, ref: str | None, dry_run: bool) -> Path:
    repo = repo.expanduser().resolve()
    manifest = repo / "Cargo.toml"
    if manifest.exists():
        checkout_repo_ref(repo, ref, dry_run)
        return repo

    if dry_run:
        return repo

    if repo.exists():
        if not repo.is_dir():
            raise SystemExit(f"Repository path exists but is not a directory: {repo}")
        if any(repo.iterdir()):
            raise SystemExit(
                f"Repository path exists but Cargo.toml is missing: {manifest}. "
                "Remove the broken cache, pass --repo to a valid checkout, or use a different --repo path."
            )

    require_executable("git")
    repo.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "clone", repo_url, str(repo)], check=True)
    if not manifest.exists():
        raise SystemExit(f"Clone completed but Cargo.toml was not found at {manifest}")
    checkout_repo_ref(repo, ref, dry_run)
    return repo


def build_command(args: argparse.Namespace, repo: Path) -> list[str]:
    input_path = Path(args.input).expanduser().resolve()
    output_path = Path(args.output).expanduser().resolve()
    if not input_path.exists() and not args.dry_run:
        raise SystemExit(f"Input image does not exist: {input_path}")
    if args.colors is not None and args.colors <= 0:
        raise SystemExit("--colors must be greater than 0")
    if args.pixel_size is not None and args.pixel_size <= 0:
        raise SystemExit("--pixel-size must be greater than 0")

    if not args.dry_run:
        output_path.parent.mkdir(parents=True, exist_ok=True)
    command = ["cargo", "run"]
    if not args.debug:
        command.append("--release")
    command.extend(["--manifest-path", str(repo / "Cargo.toml"), "--"])
    command.extend([str(input_path), str(output_path)])
    if args.colors is not None:
        command.append(str(args.colors))
    if args.pixel_size is not None:
        command.extend(["--pixel-size", str(args.pixel_size)])
    return command


def read_image_dimensions(path: Path) -> tuple[int, int]:
    data = path.read_bytes()
    if data.startswith(PNG_SIGNATURE):
        return read_png_dimensions(data)
    if data.startswith((b"\xff\xd8\xff", b"\xff\xd8")):
        return read_jpeg_dimensions(data)
    if data.startswith((b"GIF87a", b"GIF89a")):
        return struct.unpack_from("<HH", data, 6)
    if data.startswith(b"BM") and len(data) >= 26:
        width = struct.unpack_from("<i", data, 18)[0]
        height = abs(struct.unpack_from("<i", data, 22)[0])
        if width > 0 and height > 0:
            return width, height
    raise ValueError(f"unsupported image format for dimension read: {path}")


def read_png_dimensions(data: bytes) -> tuple[int, int]:
    if not data.startswith(PNG_SIGNATURE):
        raise ValueError("not a PNG file")
    if len(data) < 33:
        raise ValueError("truncated PNG header")
    chunk_len = struct.unpack(">I", data[8:12])[0]
    chunk_type = data[12:16]
    if chunk_type != b"IHDR" or chunk_len != 13:
        raise ValueError("missing PNG IHDR chunk")
    width, height = struct.unpack(">II", data[16:24])
    if width == 0 or height == 0:
        raise ValueError("PNG dimensions cannot be zero")
    return width, height


def read_jpeg_dimensions(data: bytes) -> tuple[int, int]:
    offset = 2
    sof_markers = {
        0xC0,
        0xC1,
        0xC2,
        0xC3,
        0xC5,
        0xC6,
        0xC7,
        0xC9,
        0xCA,
        0xCB,
        0xCD,
        0xCE,
        0xCF,
    }
    while offset < len(data):
        while offset < len(data) and data[offset] == 0xFF:
            offset += 1
        if offset >= len(data):
            break
        marker = data[offset]
        offset += 1
        if marker in {0xD8, 0xD9} or 0xD0 <= marker <= 0xD7:
            continue
        if offset + 2 > len(data):
            break
        segment_len = struct.unpack(">H", data[offset : offset + 2])[0]
        if segment_len < 2 or offset + segment_len > len(data):
            break
        if marker in sof_markers:
            if segment_len < 7:
                break
            height, width = struct.unpack(">HH", data[offset + 3 : offset + 7])
            if width > 0 and height > 0:
                return width, height
        offset += segment_len
    raise ValueError("could not find JPEG dimensions")


def aspect_canvas_for_output(
    source_width: int,
    source_height: int,
    output_width: int,
    output_height: int,
) -> tuple[int, int]:
    if min(source_width, source_height, output_width, output_height) <= 0:
        raise ValueError("image dimensions must be positive")

    common = math.gcd(source_width, source_height)
    ratio_width = source_width // common
    ratio_height = source_height // common
    ceil_width_scale = (output_width + ratio_width - 1) // ratio_width
    ceil_height_scale = (output_height + ratio_height - 1) // ratio_height
    scale = max(
        ceil_width_scale,
        ceil_height_scale,
    )
    return ratio_width * scale, ratio_height * scale


def _iter_png_chunks(data: bytes):
    if not data.startswith(PNG_SIGNATURE):
        raise ValueError("not a PNG file")
    offset = len(PNG_SIGNATURE)
    while offset < len(data):
        if offset + 8 > len(data):
            raise ValueError("truncated PNG chunk")
        chunk_len = struct.unpack(">I", data[offset : offset + 4])[0]
        chunk_type = data[offset + 4 : offset + 8]
        chunk_start = offset + 8
        chunk_end = chunk_start + chunk_len
        crc_end = chunk_end + 4
        if crc_end > len(data):
            raise ValueError("truncated PNG chunk data")
        yield chunk_type, data[chunk_start:chunk_end]
        offset = crc_end
        if chunk_type == b"IEND":
            break


def _paeth_predictor(left: int, up: int, upper_left: int) -> int:
    estimate = left + up - upper_left
    dist_left = abs(estimate - left)
    dist_up = abs(estimate - up)
    dist_upper_left = abs(estimate - upper_left)
    if dist_left <= dist_up and dist_left <= dist_upper_left:
        return left
    if dist_up <= dist_upper_left:
        return up
    return upper_left


def decode_rgba_png(path: Path) -> tuple[int, int, list[bytes]]:
    data = path.read_bytes()
    idat_parts: list[bytes] = []
    width = height = bit_depth = color_type = interlace = None

    for chunk_type, payload in _iter_png_chunks(data):
        if chunk_type == b"IHDR":
            width, height, bit_depth, color_type, compression, filter_method, interlace = (
                struct.unpack(">IIBBBBB", payload)
            )
            if compression != 0 or filter_method != 0:
                raise ValueError("unsupported PNG compression or filter method")
        elif chunk_type == b"IDAT":
            idat_parts.append(payload)

    if width is None or height is None:
        raise ValueError("missing PNG IHDR chunk")
    if bit_depth != 8 or color_type != 6 or interlace != 0:
        raise ValueError("only non-interlaced 8-bit RGBA PNG output is supported")

    stride = width * PNG_RGBA_BYTES_PER_PIXEL
    raw = zlib.decompress(b"".join(idat_parts))
    expected_min = height * (stride + 1)
    if len(raw) < expected_min:
        raise ValueError("truncated PNG pixel data")

    rows: list[bytes] = []
    previous = bytearray(stride)
    offset = 0
    for _ in range(height):
        filter_type = raw[offset]
        offset += 1
        row = bytearray(raw[offset : offset + stride])
        offset += stride
        for idx in range(stride):
            left = row[idx - PNG_RGBA_BYTES_PER_PIXEL] if idx >= PNG_RGBA_BYTES_PER_PIXEL else 0
            up = previous[idx]
            upper_left = (
                previous[idx - PNG_RGBA_BYTES_PER_PIXEL]
                if idx >= PNG_RGBA_BYTES_PER_PIXEL
                else 0
            )
            if filter_type == 1:
                row[idx] = (row[idx] + left) & 0xFF
            elif filter_type == 2:
                row[idx] = (row[idx] + up) & 0xFF
            elif filter_type == 3:
                row[idx] = (row[idx] + ((left + up) // 2)) & 0xFF
            elif filter_type == 4:
                row[idx] = (row[idx] + _paeth_predictor(left, up, upper_left)) & 0xFF
            elif filter_type != 0:
                raise ValueError(f"unsupported PNG filter type: {filter_type}")
        rows.append(bytes(row))
        previous = row

    return width, height, rows


def _png_chunk(chunk_type: bytes, payload: bytes) -> bytes:
    crc = binascii.crc32(chunk_type)
    crc = binascii.crc32(payload, crc) & 0xFFFFFFFF
    return struct.pack(">I", len(payload)) + chunk_type + payload + struct.pack(">I", crc)


def write_rgba_png(path: Path, width: int, height: int, rows: list[bytes]) -> None:
    stride = width * PNG_RGBA_BYTES_PER_PIXEL
    if len(rows) != height or any(len(row) != stride for row in rows):
        raise ValueError("RGBA row data does not match target dimensions")

    ihdr = struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)
    raw = b"".join(b"\x00" + row for row in rows)
    payload = (
        PNG_SIGNATURE
        + _png_chunk(b"IHDR", ihdr)
        + _png_chunk(b"IDAT", zlib.compress(raw))
        + _png_chunk(b"IEND", b"")
    )
    path.write_bytes(payload)


def pad_rgba_png(path: Path, target_width: int, target_height: int) -> tuple[int, int]:
    width, height, rows = decode_rgba_png(path)
    if target_width < width or target_height < height:
        raise ValueError("target canvas cannot be smaller than the PNG")
    if target_width == width and target_height == height:
        return width, height

    left = (target_width - width) // 2
    right = target_width - width - left
    top = (target_height - height) // 2
    bottom = target_height - height - top
    transparent = b"\x00\x00\x00\x00"
    blank_row = transparent * target_width
    padded_rows = [blank_row for _ in range(top)]
    padded_rows.extend(transparent * left + row + transparent * right for row in rows)
    padded_rows.extend(blank_row for _ in range(bottom))
    write_rgba_png(path, target_width, target_height, padded_rows)
    return target_width, target_height


def preserve_output_aspect(input_path: Path, output_path: Path) -> bool:
    source_width, source_height = read_image_dimensions(input_path)
    output_data = output_path.read_bytes()
    output_width, output_height = read_png_dimensions(output_data)
    target_width, target_height = aspect_canvas_for_output(
        source_width,
        source_height,
        output_width,
        output_height,
    )
    if (target_width, target_height) == (output_width, output_height):
        return False

    pad_rgba_png(output_path, target_width, target_height)
    print(
        "Aspect preserved: padded output canvas "
        f"{output_width}x{output_height} -> {target_width}x{target_height} "
        f"(input {source_width}x{source_height})",
        flush=True,
    )
    return True


def main() -> int:
    args = parse_args()
    repo = args.repo or default_repo_dir()
    repo = ensure_repo(repo, args.repo_url, args.ref, args.dry_run)
    command = build_command(args, repo)
    print(" ".join(f'"{part}"' if " " in part else part for part in command), flush=True)
    if args.dry_run:
        if args.preserve_aspect:
            print(
                "# After processing, the wrapper will pad the output PNG if needed "
                "to preserve the input aspect ratio.",
                flush=True,
            )
        return 0
    require_executable("cargo")
    subprocess.run(command, check=True)
    if args.preserve_aspect:
        input_path = Path(args.input).expanduser().resolve()
        output_path = Path(args.output).expanduser().resolve()
        try:
            preserve_output_aspect(input_path, output_path)
        except Exception as exc:  # noqa: BLE001 - report a clear CLI error.
            raise SystemExit(f"Failed to preserve output aspect ratio: {exc}") from exc
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except subprocess.CalledProcessError as exc:
        raise SystemExit(exc.returncode) from exc
