#!/usr/bin/env python3
"""Run the bundled fixed-canvas pixelation tool."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path


def main() -> int:
    if shutil.which("cargo") is None:
        raise SystemExit("Required executable not found on PATH: cargo")

    script_dir = Path(__file__).resolve().parent
    manifest = script_dir / "fixed_canvas_pixelate" / "Cargo.toml"
    if not manifest.exists():
        raise SystemExit(f"Missing fixed-canvas tool manifest: {manifest}")

    cache_target = (
        Path(os.environ.get("CARGO_TARGET_DIR", ""))
        if os.environ.get("CARGO_TARGET_DIR")
        else Path.home() / ".cache" / "codex" / "fixed-canvas-pixelate-target"
    )
    command = [
        "cargo",
        "run",
        "--release",
        "--manifest-path",
        str(manifest),
        "--target-dir",
        str(cache_target),
        "--",
        *sys.argv[1:],
    ]
    return subprocess.run(command, check=False).returncode


if __name__ == "__main__":
    raise SystemExit(main())
