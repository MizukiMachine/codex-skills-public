#!/usr/bin/env python3
"""Run Hugo-Dz/spritefusion-pixel-snapper on a local image."""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
from pathlib import Path


REPO_URL = "https://github.com/Hugo-Dz/spritefusion-pixel-snapper.git"
VERIFIED_REF = "9f1ccdf0496d0eb2e6b343b6385f4cb42cf36a36"
NO_REF_VALUES = {"", "none", "skip", "false", "no"}


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


def main() -> int:
    args = parse_args()
    repo = args.repo or default_repo_dir()
    repo = ensure_repo(repo, args.repo_url, args.ref, args.dry_run)
    command = build_command(args, repo)
    print(" ".join(f'"{part}"' if " " in part else part for part in command), flush=True)
    if args.dry_run:
        return 0
    require_executable("cargo")
    subprocess.run(command, check=True)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except subprocess.CalledProcessError as exc:
        raise SystemExit(exc.returncode) from exc
