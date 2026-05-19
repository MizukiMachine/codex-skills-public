#!/usr/bin/env python3
"""Unit tests for the Sprite Fusion Pixel Snapper wrapper."""

from __future__ import annotations

import argparse
import contextlib
import io
import importlib.util
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock


SCRIPT_PATH = Path(__file__).with_name("pixel_snapper.py")

spec = importlib.util.spec_from_file_location("pixel_snapper", SCRIPT_PATH)
assert spec and spec.loader
pixel_snapper = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pixel_snapper)


class PixelSnapperWrapperTests(unittest.TestCase):
    def test_aspect_canvas_preserves_square_sources(self) -> None:
        self.assertEqual(
            pixel_snapper.aspect_canvas_for_output(64, 64, 24, 25),
            (25, 25),
        )
        self.assertEqual(
            pixel_snapper.aspect_canvas_for_output(64, 64, 25, 24),
            (25, 25),
        )

    def test_aspect_canvas_preserves_wide_sources(self) -> None:
        self.assertEqual(
            pixel_snapper.aspect_canvas_for_output(1920, 1080, 31, 18),
            (32, 18),
        )

    def test_aspect_canvas_preserves_non_square_sources_exactly(self) -> None:
        cases = [
            ((3, 2, 10, 7), (12, 8)),
            ((2, 3, 7, 10), (8, 12)),
            ((4, 3, 10, 8), (12, 9)),
            ((5, 4, 6, 5), (10, 8)),
        ]

        for (source_width, source_height, output_width, output_height), expected in cases:
            with self.subTest(case=(source_width, source_height, output_width, output_height)):
                target_width, target_height = pixel_snapper.aspect_canvas_for_output(
                    source_width,
                    source_height,
                    output_width,
                    output_height,
                )

                self.assertEqual((target_width, target_height), expected)
                self.assertGreaterEqual(target_width, output_width)
                self.assertGreaterEqual(target_height, output_height)
                self.assertEqual(source_width * target_height, source_height * target_width)

    def test_preserve_output_aspect_pads_rgba_png(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            input_path = root / "input.png"
            output_path = root / "output.png"
            red = bytes([255, 0, 0, 255])
            transparent = bytes([0, 0, 0, 0])

            pixel_snapper.write_rgba_png(input_path, 10, 10, [red * 10 for _ in range(10)])
            pixel_snapper.write_rgba_png(output_path, 2, 3, [red * 2 for _ in range(3)])

            with contextlib.redirect_stdout(io.StringIO()):
                changed = pixel_snapper.preserve_output_aspect(input_path, output_path)

            width, height, rows = pixel_snapper.decode_rgba_png(output_path)
            self.assertTrue(changed)
            self.assertEqual((width, height), (3, 3))
            self.assertEqual(rows, [red * 2 + transparent for _ in range(3)])

    def test_preserve_output_aspect_leaves_matching_ratio_alone(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            input_path = root / "input.png"
            output_path = root / "output.png"
            red = bytes([255, 0, 0, 255])

            pixel_snapper.write_rgba_png(input_path, 10, 10, [red * 10 for _ in range(10)])
            pixel_snapper.write_rgba_png(output_path, 3, 3, [red * 3 for _ in range(3)])

            changed = pixel_snapper.preserve_output_aspect(input_path, output_path)

            width, height = pixel_snapper.read_image_dimensions(output_path)
            self.assertFalse(changed)
            self.assertEqual((width, height), (3, 3))

    def test_main_fails_when_aspect_preservation_fails(self) -> None:
        args = argparse.Namespace(
            input="input.webp",
            output="output.png",
            colors=8,
            pixel_size=None,
            repo=None,
            repo_url=pixel_snapper.REPO_URL,
            ref="none",
            dry_run=False,
            debug=False,
            preserve_aspect=True,
        )

        with mock.patch.object(pixel_snapper, "parse_args", return_value=args):
            with mock.patch.object(pixel_snapper, "ensure_repo", return_value=Path("/repo")):
                with mock.patch.object(pixel_snapper, "build_command", return_value=["cargo"]):
                    with mock.patch.object(pixel_snapper, "require_executable"):
                        with mock.patch.object(pixel_snapper.subprocess, "run"):
                            with mock.patch.object(
                                pixel_snapper,
                                "preserve_output_aspect",
                                side_effect=ValueError("unsupported image format"),
                            ):
                                with contextlib.redirect_stdout(io.StringIO()):
                                    with self.assertRaisesRegex(
                                        SystemExit,
                                        "Failed to preserve output aspect ratio",
                                    ):
                                        pixel_snapper.main()

    def test_build_command_uses_upstream_cli_order(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            args = argparse.Namespace(
                input=str(root / "source image.png"),
                output=str(root / "out" / "result.png"),
                colors=8,
                pixel_size=4.0,
                dry_run=True,
                debug=False,
            )

            command = pixel_snapper.build_command(args, root / "repo")

        self.assertEqual(
            command,
            [
                "cargo",
                "run",
                "--release",
                "--manifest-path",
                str((root / "repo" / "Cargo.toml").resolve()),
                "--",
                str((root / "source image.png").resolve()),
                str((root / "out" / "result.png").resolve()),
                "8",
                "--pixel-size",
                "4.0",
            ],
        )

    def test_dry_run_does_not_create_output_directory(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            output_dir = root / "missing"
            args = argparse.Namespace(
                input=str(root / "source.png"),
                output=str(output_dir / "result.png"),
                colors=None,
                pixel_size=None,
                dry_run=True,
                debug=False,
            )

            pixel_snapper.build_command(args, root / "repo")

            self.assertFalse(output_dir.exists())

    def test_nonempty_broken_repo_path_fails_clearly(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "repo"
            repo.mkdir()
            (repo / "partial-file").write_text("not a cargo checkout", encoding="utf-8")

            with self.assertRaisesRegex(SystemExit, "Cargo.toml is missing"):
                pixel_snapper.ensure_repo(
                    repo,
                    pixel_snapper.REPO_URL,
                    pixel_snapper.VERIFIED_REF,
                    dry_run=False,
                )

    def test_dry_run_ignores_broken_repo_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "repo"
            repo.mkdir()
            (repo / "partial-file").write_text("not a cargo checkout", encoding="utf-8")

            resolved = pixel_snapper.ensure_repo(
                repo,
                pixel_snapper.REPO_URL,
                pixel_snapper.VERIFIED_REF,
                dry_run=True,
            )

            self.assertEqual(resolved, repo.resolve())

    def test_existing_repo_checks_out_verified_ref(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "repo"
            repo.mkdir()
            (repo / "Cargo.toml").write_text("[package]\n", encoding="utf-8")

            completed = subprocess.CompletedProcess(args=[], returncode=0)
            with mock.patch.object(pixel_snapper.shutil, "which", return_value="/usr/bin/git"):
                with mock.patch.object(
                    pixel_snapper.subprocess, "run", return_value=completed
                ) as run:
                    pixel_snapper.ensure_repo(
                        repo,
                        pixel_snapper.REPO_URL,
                        pixel_snapper.VERIFIED_REF,
                        dry_run=False,
                    )

            calls = [call.args[0] for call in run.call_args_list]
            self.assertIn(
                [
                    "git",
                    "-C",
                    str(repo.resolve()),
                    "checkout",
                    "--quiet",
                    pixel_snapper.VERIFIED_REF,
                ],
                calls,
            )

    def test_ref_none_skips_checkout_for_existing_repo(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "repo"
            repo.mkdir()
            (repo / "Cargo.toml").write_text("[package]\n", encoding="utf-8")

            with mock.patch.object(pixel_snapper.subprocess, "run") as run:
                pixel_snapper.ensure_repo(
                    repo,
                    pixel_snapper.REPO_URL,
                    "none",
                    dry_run=False,
                )

            run.assert_not_called()


if __name__ == "__main__":
    unittest.main()
