#!/usr/bin/env python3
"""Inspect PNG frame batches for size, visible RGB colors, and alpha preservation."""

from __future__ import annotations

import argparse
import struct
import sys
import zlib
from collections import Counter
from pathlib import Path


PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


def paeth(a: int, b: int, c: int) -> int:
    p = a + b - c
    pa = abs(p - a)
    pb = abs(p - b)
    pc = abs(p - c)
    if pa <= pb and pa <= pc:
        return a
    if pb <= pc:
        return b
    return c


def read_png_stats(
    path: Path,
    *,
    collect_rgb: bool = True,
    stop_after_alpha_levels: int | None = None,
) -> dict[str, object]:
    data = path.read_bytes()
    if not data.startswith(PNG_SIGNATURE):
        raise ValueError(f"not a PNG: {path}")

    offset = len(PNG_SIGNATURE)
    width = height = bit_depth = color_type = interlace = None
    palette: list[tuple[int, int, int]] = []
    transparent: bytes = b""
    idat: list[bytes] = []

    while offset < len(data):
        length = struct.unpack(">I", data[offset : offset + 4])[0]
        chunk_type = data[offset + 4 : offset + 8]
        chunk = data[offset + 8 : offset + 8 + length]
        offset += 12 + length

        if chunk_type == b"IHDR":
            width, height, bit_depth, color_type, _, _, interlace = struct.unpack(
                ">IIBBBBB", chunk
            )
        elif chunk_type == b"PLTE":
            palette = [tuple(chunk[i : i + 3]) for i in range(0, len(chunk), 3)]
        elif chunk_type == b"tRNS":
            transparent = chunk
        elif chunk_type == b"IDAT":
            idat.append(chunk)
        elif chunk_type == b"IEND":
            break

    if bit_depth != 8 or interlace != 0:
        raise ValueError(
            f"unsupported PNG format: {path} "
            f"(bit_depth={bit_depth}, interlace={interlace})"
        )

    channels_by_type = {0: 1, 2: 3, 3: 1, 4: 2, 6: 4}
    if color_type not in channels_by_type:
        raise ValueError(f"unsupported PNG color type {color_type}: {path}")

    channels = channels_by_type[color_type]
    row_bytes = width * channels  # type: ignore[operator]
    raw = zlib.decompress(b"".join(idat))
    previous = bytearray(row_bytes)
    pos = 0

    visible_rgb: set[tuple[int, int, int]] = set()
    alpha_values: set[int] = set()
    visible_pixels = 0

    for _ in range(height):  # type: ignore[arg-type]
        filter_type = raw[pos]
        pos += 1
        row = bytearray(raw[pos : pos + row_bytes])
        pos += row_bytes

        for i, value in enumerate(row):
            left = row[i - channels] if i >= channels else 0
            up = previous[i]
            upper_left = previous[i - channels] if i >= channels else 0
            if filter_type == 1:
                row[i] = (value + left) & 255
            elif filter_type == 2:
                row[i] = (value + up) & 255
            elif filter_type == 3:
                row[i] = (value + ((left + up) // 2)) & 255
            elif filter_type == 4:
                row[i] = (value + paeth(left, up, upper_left)) & 255
            elif filter_type != 0:
                raise ValueError(f"bad PNG filter {filter_type}: {path}")

        if color_type == 6:
            for i in range(0, row_bytes, 4):
                r, g, b, a = row[i], row[i + 1], row[i + 2], row[i + 3]
                if a:
                    if collect_rgb:
                        visible_rgb.add((r, g, b))
                    alpha_values.add(a)
                    visible_pixels += 1
        elif color_type == 2:
            transparent_rgb = None
            if len(transparent) >= 6:
                transparent_rgb = struct.unpack(">HHH", transparent[:6])
            for i in range(0, row_bytes, 3):
                r, g, b = row[i], row[i + 1], row[i + 2]
                a = 0 if transparent_rgb == (r, g, b) else 255
                if a:
                    if collect_rgb:
                        visible_rgb.add((r, g, b))
                    alpha_values.add(a)
                    visible_pixels += 1
        elif color_type == 4:
            for i in range(0, row_bytes, 2):
                gray, a = row[i], row[i + 1]
                if a:
                    if collect_rgb:
                        visible_rgb.add((gray, gray, gray))
                    alpha_values.add(a)
                    visible_pixels += 1
        elif color_type == 0:
            transparent_gray = None
            if len(transparent) >= 2:
                transparent_gray = struct.unpack(">H", transparent[:2])[0]
            for gray in row:
                a = 0 if transparent_gray == gray else 255
                if a:
                    if collect_rgb:
                        visible_rgb.add((gray, gray, gray))
                    alpha_values.add(a)
                    visible_pixels += 1
        elif color_type == 3:
            for index in row:
                r, g, b = palette[index] if index < len(palette) else (0, 0, 0)
                a = transparent[index] if index < len(transparent) else 255
                if a:
                    if collect_rgb:
                        visible_rgb.add((r, g, b))
                    alpha_values.add(a)
                    visible_pixels += 1

        if (
            stop_after_alpha_levels is not None
            and len(alpha_values) >= stop_after_alpha_levels
        ):
            return {
                "size": (width, height),
                "visible_rgb_count": len(visible_rgb),
                "alpha_count": len(alpha_values),
                "visible_pixels": visible_pixels,
            }

        previous = row

    return {
        "size": (width, height),
        "visible_rgb_count": len(visible_rgb),
        "alpha_count": len(alpha_values),
        "visible_pixels": visible_pixels,
    }


def collect_pngs(
    root: Path,
    exclude_parts: set[str],
    exclude_suffixes: tuple[str, ...],
) -> list[Path]:
    paths = []
    for path in root.rglob("*.png"):
        if any(part in exclude_parts for part in path.parts):
            continue
        if path.name.endswith(exclude_suffixes):
            continue
        paths.append(path)
    return sorted(paths)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", required=True, type=Path)
    parser.add_argument("--source-root", type=Path)
    parser.add_argument(
        "--source-check-limit",
        type=int,
        default=8,
        help=(
            "Read the first N matching source files to detect whether the source "
            "set uses soft alpha. 0 reads all matching sources; this can be slow "
            "for large source frames."
        ),
    )
    parser.add_argument("--max-visible-rgb", type=int)
    parser.add_argument("--min-alpha-levels", type=int)
    parser.add_argument("--expected-count", type=int)
    parser.add_argument("--require-single-size", action="store_true")
    parser.add_argument("--allow-alpha-flatten", action="store_true")
    parser.add_argument("--exclude-part", action="append", default=["spritesheets"])
    parser.add_argument("--exclude-suffix", action="append", default=["_preview.png"])
    args = parser.parse_args()

    root = args.root.resolve()
    if not root.is_dir():
        raise SystemExit(f"not a directory: {root}")

    paths = collect_pngs(root, set(args.exclude_part), tuple(args.exclude_suffix))
    if not paths:
        raise SystemExit(f"no PNG files found: {root}")

    failures: list[str] = []
    size_counts: Counter[tuple[int, int]] = Counter()
    alpha_level_counts: Counter[int] = Counter()
    max_rgb = 0
    max_rgb_path = None
    source_soft_alpha_seen = False

    source_stats: dict[Path, dict[str, object]] = {}
    if args.source_root:
        source_root = args.source_root.resolve()
        source_paths = paths
        if args.source_check_limit > 0:
            source_paths = paths[: args.source_check_limit]
        for path in source_paths:
            rel = path.relative_to(root)
            source = source_root / rel
            if not source.exists():
                failures.append(f"{rel}: matching source PNG not found at {source}")
                continue
            source_stats[rel] = read_png_stats(
                source,
                collect_rgb=False,
                stop_after_alpha_levels=2,
            )
            if int(source_stats[rel]["alpha_count"]) > 1:
                source_soft_alpha_seen = True

    for path in paths:
        stats = read_png_stats(path)
        rel = path.relative_to(root)
        size_counts[stats["size"]] += 1  # type: ignore[index]
        alpha_level_counts[stats["alpha_count"]] += 1  # type: ignore[index]
        rgb_count = int(stats["visible_rgb_count"])
        if rgb_count > max_rgb:
            max_rgb = rgb_count
            max_rgb_path = rel

        if args.max_visible_rgb is not None and rgb_count > args.max_visible_rgb:
            failures.append(
                f"{rel}: visible RGB colors {rgb_count} > {args.max_visible_rgb}"
            )

        if (
            args.min_alpha_levels is not None
            and int(stats["visible_pixels"]) > 0
            and int(stats["alpha_count"]) < args.min_alpha_levels
        ):
            failures.append(
                f"{rel}: alpha levels {stats['alpha_count']} < {args.min_alpha_levels}"
            )

        if args.source_root and not args.allow_alpha_flatten:
            source = source_stats.get(rel)
            if source and int(source["alpha_count"]) > 1 and int(stats["alpha_count"]) <= 1:
                failures.append(
                    f"{rel}: source has soft alpha ({source['alpha_count']} levels) "
                    f"but output has {stats['alpha_count']} alpha level"
                )
            elif (
                source is None
                and source_soft_alpha_seen
                and int(stats["visible_pixels"]) > 0
                and int(stats["alpha_count"]) <= 1
            ):
                failures.append(
                    f"{rel}: source sample has soft alpha but output has "
                    f"{stats['alpha_count']} alpha level"
                )

    if args.expected_count is not None and len(paths) != args.expected_count:
        failures.append(f"file count {len(paths)} != expected {args.expected_count}")

    if args.require_single_size and len(size_counts) != 1:
        failures.append(f"unique sizes {len(size_counts)} != 1")

    print(f"files {len(paths)}")
    print("sizes")
    for size, count in sorted(size_counts.items()):
        print(f"  {size[0]}x{size[1]} {count}")
    print(f"max visible RGB colors {max_rgb}", end="")
    if max_rgb_path:
        print(f" ({max_rgb_path})")
    else:
        print()
    print("alpha-level counts")
    for alpha_count, count in sorted(alpha_level_counts.items()):
        print(f"  {alpha_count} alpha levels: {count}")

    if failures:
        sys.stdout.flush()
        print("failures", file=sys.stderr)
        for failure in failures:
            print(f"  {failure}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
