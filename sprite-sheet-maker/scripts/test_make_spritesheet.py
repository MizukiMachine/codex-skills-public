#!/usr/bin/env python3
"""Unit tests for make_spritesheet.py."""

from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT_PATH = Path(__file__).with_name("make_spritesheet.py")

spec = importlib.util.spec_from_file_location("make_spritesheet", SCRIPT_PATH)
assert spec and spec.loader
make_spritesheet = importlib.util.module_from_spec(spec)
sys.modules["make_spritesheet"] = make_spritesheet
spec.loader.exec_module(make_spritesheet)


def solid_image(width: int, height: int, color: tuple[int, int, int, int]) -> object:
    return make_spritesheet.PngImage(
        width=width,
        height=height,
        pixels=bytearray(color * (width * height)),
    )


def pixel_at(image: object, x: int, y: int) -> tuple[int, int, int, int]:
    offset = (y * image.width + x) * 4
    return tuple(image.pixels[offset : offset + 4])


class SpriteSheetTests(unittest.TestCase):
    def test_natural_order_sorts_numbered_frames(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for name in ["frame_10.png", "frame_2.png", "frame_1.png"]:
                make_spritesheet.write_png_rgba(root / name, solid_image(1, 1, (255, 0, 0, 255)))

            names = [path.name for path in make_spritesheet.discover_frames(root, "*.png", "natural")]

        self.assertEqual(names, ["frame_1.png", "frame_2.png", "frame_10.png"])

    def test_bottom_center_alignment_uses_max_cell_size(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            small = root / "frame_0001.png"
            large = root / "frame_0002.png"
            make_spritesheet.write_png_rgba(small, solid_image(2, 2, (255, 0, 0, 255)))
            make_spritesheet.write_png_rgba(large, solid_image(4, 3, (0, 255, 0, 255)))

            sheet, placements, grid = make_spritesheet.build_spritesheet(
                frame_paths=[small, large],
                columns=2,
                rows=None,
                cell_width=None,
                cell_height=None,
                align="bottom-center",
                margin=0,
                spacing=0,
                background=(0, 0, 0, 0),
            )

        self.assertEqual((sheet.width, sheet.height), (8, 3))
        self.assertEqual(grid, (2, 1))
        self.assertEqual((placements[0].offset_x, placements[0].offset_y), (1, 1))
        self.assertEqual(pixel_at(sheet, 1, 1), (255, 0, 0, 255))
        self.assertEqual(pixel_at(sheet, 0, 0), (0, 0, 0, 0))
        self.assertEqual(pixel_at(sheet, 4, 0), (0, 255, 0, 255))

    def test_metadata_contains_cell_and_source_rectangles(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            frame = root / "frame_0001.png"
            output = root / "sheet.png"
            make_spritesheet.write_png_rgba(frame, solid_image(2, 3, (0, 0, 255, 255)))
            sheet, placements, grid = make_spritesheet.build_spritesheet(
                frame_paths=[frame],
                columns=None,
                rows=None,
                cell_width=None,
                cell_height=None,
                align="bottom-center",
                margin=1,
                spacing=0,
                background=(0, 0, 0, 0),
            )

            payload = make_spritesheet.metadata_payload(output, sheet, placements, grid, "bottom-center", 1, 0)

        self.assertEqual(payload["width"], 4)
        self.assertEqual(payload["height"], 5)
        self.assertEqual(payload["frames"][0]["name"], "frame_0001.png")
        self.assertEqual(payload["frames"][0]["cell"], {"x": 1, "y": 1, "w": 2, "h": 3})
        json.dumps(payload)

    def test_cell_smaller_than_frame_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            frame = root / "frame.png"
            make_spritesheet.write_png_rgba(frame, solid_image(3, 3, (255, 255, 255, 255)))

            with self.assertRaisesRegex(SystemExit, "too small"):
                make_spritesheet.build_spritesheet(
                    frame_paths=[frame],
                    columns=1,
                    rows=1,
                    cell_width=2,
                    cell_height=3,
                    align="center",
                    margin=0,
                    spacing=0,
                    background=(0, 0, 0, 0),
                )


if __name__ == "__main__":
    unittest.main()
