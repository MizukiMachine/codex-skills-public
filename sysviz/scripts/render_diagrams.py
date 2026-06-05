#!/usr/bin/env python3
"""
Mermaid diagram renderer - converts .mmd files to high-resolution PNG images.
Usage: python render_diagrams.py <input_dir> [--output <output_dir>] [--scale 4]
"""

import argparse
import subprocess
import sys
from pathlib import Path


def render_mmd_to_png(
    mmd_path: Path,
    output_path: Path,
    width: int = 2400,
    height: int = 1600,
    scale: int = 4,
    background: str = "white"
) -> bool:
    """Render a single Mermaid file to PNG."""
    cmd = [
        "mmdc",
        "-i", str(mmd_path),
        "-o", str(output_path),
        "-b", background,
        "-w", str(width),
        "-H", str(height),
        "--scale", str(scale)
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        if result.returncode == 0:
            print(f"[OK] Generated: {output_path.name}")
            return True
        else:
            print(f"[ERROR] Error rendering {mmd_path.name}: {result.stderr}", file=sys.stderr)
            return False
    except FileNotFoundError:
        print("Error: 'mmdc' (mermaid-cli) not found. Install with: npm install -g @mermaid-js/mermaid-cli", file=sys.stderr)
        sys.exit(1)
    except subprocess.TimeoutExpired:
        print(f"[ERROR] Timeout rendering {mmd_path.name}", file=sys.stderr)
        return False


def render_all_diagrams(
    input_dir: Path,
    output_dir: Path,
    scale: int = 4,
    width: int = 2400,
    height: int = 1600,
) -> tuple[int, int]:
    """Render all .mmd files in directory to PNG. Returns (success_count, total_count)."""
    if not input_dir.exists():
        print(f"Error: Input directory '{input_dir}' not found", file=sys.stderr)
        sys.exit(1)

    output_dir.mkdir(parents=True, exist_ok=True)

    mmd_files = sorted(input_dir.glob("*.mmd"))
    if not mmd_files:
        print(f"No .mmd files found in {input_dir}")
        return 0, 0

    print(f"Found {len(mmd_files)} Mermaid files to render...\n")

    success = 0
    for mmd_path in mmd_files:
        png_path = output_dir / f"{mmd_path.stem}.png"
        if render_mmd_to_png(
            mmd_path,
            png_path,
            width=width,
            height=height,
            scale=scale,
        ):
            success += 1

    print(f"\nCompleted: {success}/{len(mmd_files)} diagrams rendered")
    return success, len(mmd_files)


def main():
    parser = argparse.ArgumentParser(
        description="Render Mermaid diagrams to high-resolution PNG images"
    )
    parser.add_argument("input_dir", type=Path, help="Directory containing .mmd files")
    parser.add_argument("--output", "-o", type=Path, help="Output directory (default: same as input)")
    parser.add_argument("--scale", "-s", type=int, default=4, help="Scale factor (default: 4)")
    parser.add_argument("--width", "-W", type=int, default=2400, help="Width in pixels (default: 2400)")
    parser.add_argument("--height", "-H", type=int, default=1600, help="Height in pixels (default: 1600)")

    args = parser.parse_args()
    output_dir = args.output or args.input_dir

    success, total = render_all_diagrams(
        args.input_dir,
        output_dir,
        scale=args.scale,
        width=args.width,
        height=args.height,
    )
    sys.exit(0 if success == total else 1)


if __name__ == "__main__":
    main()
