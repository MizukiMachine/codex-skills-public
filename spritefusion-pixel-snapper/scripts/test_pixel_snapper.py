#!/usr/bin/env python3
"""Unit tests for the Sprite Fusion Pixel Snapper wrapper."""

from __future__ import annotations

import argparse
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
