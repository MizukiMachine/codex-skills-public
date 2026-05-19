#!/usr/bin/env python3
"""Build a PNG sprite sheet from a directory of PNG frame images."""

from __future__ import annotations

import argparse
import json
import math
import re
import struct
import zlib
from dataclasses import dataclass
from pathlib import Path


PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
SUPPORTED_COLOR_TYPES = {0, 2, 3, 4, 6}


@dataclass(frozen=True)
class PngImage:
    width: int
    height: int
    pixels: bytearray


@dataclass(frozen=True)
class FramePlacement:
    index: int
    path: Path
    sheet_x: int
    sheet_y: int
    source_width: int
    source_height: int
    offset_x: int
    offset_y: int
    cell_x: int
    cell_y: int
    cell_width: int
    cell_height: int


def natural_key(path: Path) -> list[object]:
    return [int(part) if part.isdigit() else part.lower() for part in re.split(r"(\d+)", path.name)]


def parse_color(value: str) -> tuple[int, int, int, int]:
    if value == "transparent":
        return (0, 0, 0, 0)
    text = value.strip()
    if text.startswith("#"):
        text = text[1:]
    if len(text) == 6:
        text += "ff"
    if len(text) != 8 or not re.fullmatch(r"[0-9a-fA-F]{8}", text):
        raise SystemExit("--background must be 'transparent', #RRGGBB, or #RRGGBBAA")
    return tuple(int(text[i : i + 2], 16) for i in range(0, 8, 2))  # type: ignore[return-value]


def read_chunks(data: bytes) -> tuple[dict[str, object], list[bytes], list[tuple[bytes, bytes]]]:
    if not data.startswith(PNG_SIGNATURE):
        raise ValueError("not a PNG file")
    pos = len(PNG_SIGNATURE)
    ihdr: dict[str, object] | None = None
    idat_parts: list[bytes] = []
    ancillary: list[tuple[bytes, bytes]] = []

    while pos < len(data):
        if pos + 8 > len(data):
            raise ValueError("truncated PNG chunk header")
        length = struct.unpack(">I", data[pos : pos + 4])[0]
        chunk_type = data[pos + 4 : pos + 8]
        pos += 8
        chunk_data = data[pos : pos + length]
        pos += length
        if pos + 4 > len(data):
            raise ValueError("truncated PNG chunk CRC")
        pos += 4

        if chunk_type == b"IHDR":
            width, height, bit_depth, color_type, compression, filter_method, interlace = struct.unpack(
                ">IIBBBBB", chunk_data
            )
            ihdr = {
                "width": width,
                "height": height,
                "bit_depth": bit_depth,
                "color_type": color_type,
                "compression": compression,
                "filter_method": filter_method,
                "interlace": interlace,
            }
        elif chunk_type == b"IDAT":
            idat_parts.append(chunk_data)
        elif chunk_type == b"IEND":
            break
        else:
            ancillary.append((chunk_type, chunk_data))

    if ihdr is None:
        raise ValueError("PNG is missing IHDR")
    return ihdr, idat_parts, ancillary


def paeth_predictor(left: int, up: int, up_left: int) -> int:
    p = left + up - up_left
    pa = abs(p - left)
    pb = abs(p - up)
    pc = abs(p - up_left)
    if pa <= pb and pa <= pc:
        return left
    if pb <= pc:
        return up
    return up_left


def unfilter_scanlines(raw: bytes, width: int, height: int, channels: int) -> list[bytearray]:
    stride = width * channels
    bpp = channels
    pos = 0
    previous = bytearray(stride)
    rows: list[bytearray] = []

    for _ in range(height):
        if pos >= len(raw):
            raise ValueError("truncated PNG scanline data")
        filter_type = raw[pos]
        pos += 1
        row = bytearray(raw[pos : pos + stride])
        pos += stride
        if len(row) != stride:
            raise ValueError("truncated PNG scanline data")

        for i, value in enumerate(row):
            left = row[i - bpp] if i >= bpp else 0
            up = previous[i]
            up_left = previous[i - bpp] if i >= bpp else 0
            if filter_type == 0:
                recon = value
            elif filter_type == 1:
                recon = value + left
            elif filter_type == 2:
                recon = value + up
            elif filter_type == 3:
                recon = value + ((left + up) // 2)
            elif filter_type == 4:
                recon = value + paeth_predictor(left, up, up_left)
            else:
                raise ValueError(f"unsupported PNG filter type: {filter_type}")
            row[i] = recon & 0xFF

        rows.append(row)
        previous = row

    return rows


def palette_from_chunks(ancillary: list[tuple[bytes, bytes]]) -> tuple[list[tuple[int, int, int]], bytes]:
    palette: list[tuple[int, int, int]] = []
    transparency = b""
    for chunk_type, chunk_data in ancillary:
        if chunk_type == b"PLTE":
            palette = [
                tuple(chunk_data[i : i + 3])  # type: ignore[misc]
                for i in range(0, len(chunk_data), 3)
                if len(chunk_data[i : i + 3]) == 3
            ]
        elif chunk_type == b"tRNS":
            transparency = chunk_data
    return palette, transparency


def read_png_rgba(path: Path) -> PngImage:
    ihdr, idat_parts, ancillary = read_chunks(path.read_bytes())
    width = int(ihdr["width"])
    height = int(ihdr["height"])
    bit_depth = int(ihdr["bit_depth"])
    color_type = int(ihdr["color_type"])
    interlace = int(ihdr["interlace"])

    if bit_depth != 8:
        raise ValueError(f"{path} uses unsupported PNG bit depth {bit_depth}; expected 8")
    if color_type not in SUPPORTED_COLOR_TYPES:
        raise ValueError(f"{path} uses unsupported PNG color type {color_type}")
    if interlace != 0:
        raise ValueError(f"{path} uses interlaced PNG, which is not supported")

    channels_by_type = {0: 1, 2: 3, 3: 1, 4: 2, 6: 4}
    channels = channels_by_type[color_type]
    raw = zlib.decompress(b"".join(idat_parts))
    rows = unfilter_scanlines(raw, width, height, channels)
    palette, transparency = palette_from_chunks(ancillary)

    pixels = bytearray(width * height * 4)
    out = 0
    for row in rows:
        for x in range(width):
            src = x * channels
            if color_type == 0:
                gray = row[src]
                rgba = (gray, gray, gray, 255)
            elif color_type == 2:
                rgba = (row[src], row[src + 1], row[src + 2], 255)
            elif color_type == 3:
                index = row[src]
                if index >= len(palette):
                    raise ValueError(f"{path} references missing palette index {index}")
                r, g, b = palette[index]
                a = transparency[index] if index < len(transparency) else 255
                rgba = (r, g, b, a)
            elif color_type == 4:
                gray = row[src]
                rgba = (gray, gray, gray, row[src + 1])
            else:
                rgba = (row[src], row[src + 1], row[src + 2], row[src + 3])
            pixels[out : out + 4] = bytes(rgba)
            out += 4

    return PngImage(width=width, height=height, pixels=pixels)


def png_chunk(chunk_type: bytes, chunk_data: bytes) -> bytes:
    crc = zlib.crc32(chunk_type)
    crc = zlib.crc32(chunk_data, crc) & 0xFFFFFFFF
    return struct.pack(">I", len(chunk_data)) + chunk_type + chunk_data + struct.pack(">I", crc)


def write_png_rgba(path: Path, image: PngImage) -> None:
    rows = bytearray()
    stride = image.width * 4
    for y in range(image.height):
        rows.append(0)
        start = y * stride
        rows.extend(image.pixels[start : start + stride])

    ihdr = struct.pack(">IIBBBBB", image.width, image.height, 8, 6, 0, 0, 0)
    output = bytearray(PNG_SIGNATURE)
    output.extend(png_chunk(b"IHDR", ihdr))
    output.extend(png_chunk(b"IDAT", zlib.compress(bytes(rows), level=9)))
    output.extend(png_chunk(b"IEND", b""))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(output)


def discover_frames(input_dir: Path, pattern: str, order: str) -> list[Path]:
    frames = [path for path in input_dir.glob(pattern) if path.is_file()]
    if order == "natural":
        frames.sort(key=natural_key)
    elif order == "lex":
        frames.sort()
    else:
        raise SystemExit("--order must be natural or lex")
    if not frames:
        raise SystemExit(f"No frames matched {pattern!r} in {input_dir}")
    return frames


def grid_for_count(frame_count: int, columns: int | None, rows: int | None) -> tuple[int, int]:
    if columns is not None and columns <= 0:
        raise SystemExit("--columns must be greater than 0")
    if rows is not None and rows <= 0:
        raise SystemExit("--rows must be greater than 0")
    if columns is None and rows is None:
        columns = math.ceil(math.sqrt(frame_count))
        rows = math.ceil(frame_count / columns)
    elif columns is None:
        columns = math.ceil(frame_count / rows)  # type: ignore[arg-type]
    elif rows is None:
        rows = math.ceil(frame_count / columns)
    if columns * rows < frame_count:
        raise SystemExit("--columns x --rows is too small for the number of frames")
    return columns, rows


def alignment_offset(align: str, cell_width: int, cell_height: int, frame_width: int, frame_height: int) -> tuple[int, int]:
    horizontal, vertical = {
        "top-left": ("left", "top"),
        "top-center": ("center", "top"),
        "top-right": ("right", "top"),
        "center-left": ("left", "center"),
        "center": ("center", "center"),
        "center-right": ("right", "center"),
        "bottom-left": ("left", "bottom"),
        "bottom-center": ("center", "bottom"),
        "bottom-right": ("right", "bottom"),
    }.get(align, (None, None))
    if horizontal is None:
        raise SystemExit(f"Unsupported --align value: {align}")

    if horizontal == "left":
        offset_x = 0
    elif horizontal == "center":
        offset_x = (cell_width - frame_width) // 2
    else:
        offset_x = cell_width - frame_width

    if vertical == "top":
        offset_y = 0
    elif vertical == "center":
        offset_y = (cell_height - frame_height) // 2
    else:
        offset_y = cell_height - frame_height
    return offset_x, offset_y


def alpha_blend_pixel(dst: bytearray, offset: int, src: bytearray, src_offset: int) -> None:
    sr, sg, sb, sa = src[src_offset : src_offset + 4]
    if sa == 0:
        return
    if sa == 255:
        dst[offset : offset + 4] = src[src_offset : src_offset + 4]
        return

    dr, dg, db, da = dst[offset : offset + 4]
    inv = 255 - sa
    out_a = sa + ((da * inv + 127) // 255)
    if out_a == 0:
        dst[offset : offset + 4] = b"\x00\x00\x00\x00"
        return

    def blend_channel(source: int, dest: int) -> int:
        numerator = source * sa * 255 + dest * da * inv
        return min(255, (numerator + (out_a * 255 // 2)) // (out_a * 255))

    dst[offset : offset + 4] = bytes(
        (blend_channel(sr, dr), blend_channel(sg, dg), blend_channel(sb, db), out_a)
    )


def paste_frame(canvas: PngImage, frame: PngImage, x: int, y: int) -> None:
    for row in range(frame.height):
        dst_y = y + row
        if dst_y < 0 or dst_y >= canvas.height:
            continue
        for col in range(frame.width):
            dst_x = x + col
            if dst_x < 0 or dst_x >= canvas.width:
                continue
            src_offset = (row * frame.width + col) * 4
            dst_offset = (dst_y * canvas.width + dst_x) * 4
            alpha_blend_pixel(canvas.pixels, dst_offset, frame.pixels, src_offset)


def build_spritesheet(
    frame_paths: list[Path],
    columns: int | None,
    rows: int | None,
    cell_width: int | None,
    cell_height: int | None,
    align: str,
    margin: int,
    spacing: int,
    background: tuple[int, int, int, int],
) -> tuple[PngImage, list[FramePlacement], tuple[int, int]]:
    if margin < 0:
        raise SystemExit("--margin must be 0 or greater")
    if spacing < 0:
        raise SystemExit("--spacing must be 0 or greater")

    frames = [(path, read_png_rgba(path)) for path in frame_paths]
    max_width = max(image.width for _, image in frames)
    max_height = max(image.height for _, image in frames)
    cell_width = cell_width or max_width
    cell_height = cell_height or max_height
    if cell_width <= 0 or cell_height <= 0:
        raise SystemExit("--cell-width and --cell-height must be greater than 0")
    if cell_width < max_width or cell_height < max_height:
        raise SystemExit(
            f"Cell size {cell_width}x{cell_height} is too small for max frame {max_width}x{max_height}"
        )

    columns, rows = grid_for_count(len(frames), columns, rows)
    sheet_width = margin * 2 + columns * cell_width + (columns - 1) * spacing
    sheet_height = margin * 2 + rows * cell_height + (rows - 1) * spacing
    canvas = PngImage(
        width=sheet_width,
        height=sheet_height,
        pixels=bytearray(background * (sheet_width * sheet_height)),
    )

    placements: list[FramePlacement] = []
    for index, (path, image) in enumerate(frames):
        row = index // columns
        column = index % columns
        cell_x = margin + column * (cell_width + spacing)
        cell_y = margin + row * (cell_height + spacing)
        offset_x, offset_y = alignment_offset(align, cell_width, cell_height, image.width, image.height)
        sheet_x = cell_x + offset_x
        sheet_y = cell_y + offset_y
        paste_frame(canvas, image, sheet_x, sheet_y)
        placements.append(
            FramePlacement(
                index=index,
                path=path,
                sheet_x=sheet_x,
                sheet_y=sheet_y,
                source_width=image.width,
                source_height=image.height,
                offset_x=offset_x,
                offset_y=offset_y,
                cell_x=cell_x,
                cell_y=cell_y,
                cell_width=cell_width,
                cell_height=cell_height,
            )
        )

    return canvas, placements, (columns, rows)


def metadata_payload(
    output: Path,
    sheet: PngImage,
    placements: list[FramePlacement],
    grid: tuple[int, int],
    align: str,
    margin: int,
    spacing: int,
) -> dict[str, object]:
    columns, rows = grid
    return {
        "image": output.name,
        "width": sheet.width,
        "height": sheet.height,
        "columns": columns,
        "rows": rows,
        "align": align,
        "margin": margin,
        "spacing": spacing,
        "frames": [
            {
                "index": placement.index,
                "name": placement.path.name,
                "x": placement.sheet_x,
                "y": placement.sheet_y,
                "w": placement.source_width,
                "h": placement.source_height,
                "cell": {
                    "x": placement.cell_x,
                    "y": placement.cell_y,
                    "w": placement.cell_width,
                    "h": placement.cell_height,
                },
                "offset": {"x": placement.offset_x, "y": placement.offset_y},
            }
            for placement in placements
        ],
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Combine PNG frames into a sprite sheet.")
    parser.add_argument("--input-dir", "-i", required=True, type=Path, help="Directory containing frame PNGs.")
    parser.add_argument("--output", "-o", required=True, type=Path, help="Output sprite sheet PNG path.")
    parser.add_argument("--pattern", default="*.png", help="Input glob pattern relative to --input-dir.")
    parser.add_argument("--columns", "-c", type=int, default=None, help="Number of columns. Default: square-ish grid.")
    parser.add_argument("--rows", "-r", type=int, default=None, help="Number of rows. Default: enough rows for frames.")
    parser.add_argument("--cell-width", type=int, default=None, help="Cell width. Default: max frame width.")
    parser.add_argument("--cell-height", type=int, default=None, help="Cell height. Default: max frame height.")
    parser.add_argument(
        "--align",
        default="bottom-center",
        choices=[
            "top-left",
            "top-center",
            "top-right",
            "center-left",
            "center",
            "center-right",
            "bottom-left",
            "bottom-center",
            "bottom-right",
        ],
        help="Frame alignment inside each cell. Default: bottom-center.",
    )
    parser.add_argument("--margin", type=int, default=0, help="Outer transparent margin in pixels.")
    parser.add_argument("--spacing", type=int, default=0, help="Spacing between cells in pixels.")
    parser.add_argument(
        "--background",
        default="transparent",
        help="Background color: transparent, #RRGGBB, or #RRGGBBAA. Default: transparent.",
    )
    parser.add_argument("--order", choices=["natural", "lex"], default="natural", help="Frame sort order.")
    parser.add_argument(
        "--metadata",
        nargs="?",
        const="auto",
        default=None,
        help="Write JSON metadata. Use without value for <output>.json, or pass an explicit path.",
    )
    parser.add_argument("--dry-run", action="store_true", help="Print the planned sheet without writing files.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    input_dir = args.input_dir.expanduser().resolve()
    output = args.output.expanduser().resolve()
    if not input_dir.is_dir():
        raise SystemExit(f"Input directory does not exist: {input_dir}")

    frame_paths = discover_frames(input_dir, args.pattern, args.order)
    background = parse_color(args.background)
    sheet, placements, grid = build_spritesheet(
        frame_paths=frame_paths,
        columns=args.columns,
        rows=args.rows,
        cell_width=args.cell_width,
        cell_height=args.cell_height,
        align=args.align,
        margin=args.margin,
        spacing=args.spacing,
        background=background,
    )
    columns, rows = grid
    print(
        f"{len(frame_paths)} frames -> {output} "
        f"({sheet.width}x{sheet.height}, {columns}x{rows}, cell {placements[0].cell_width}x{placements[0].cell_height})"
    )
    if args.dry_run:
        return 0

    write_png_rgba(output, sheet)
    if args.metadata is not None:
        metadata_path = output.with_suffix(".json") if args.metadata == "auto" else Path(args.metadata).expanduser().resolve()
        metadata_path.parent.mkdir(parents=True, exist_ok=True)
        metadata_path.write_text(
            json.dumps(
                metadata_payload(output, sheet, placements, grid, args.align, args.margin, args.spacing),
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        print(f"metadata -> {metadata_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
