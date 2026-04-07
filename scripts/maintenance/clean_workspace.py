"""Cross-platform cleanup for common Kor'tana build and cache artifacts."""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path


def _remove_path(path: Path) -> None:
    if path.is_dir():
        shutil.rmtree(path, ignore_errors=True)
    elif path.exists():
        path.unlink(missing_ok=True)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path(__file__).resolve().parents[2],
        help="Repository root to clean.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Report what would be removed without mutating the workspace.",
    )
    return parser.parse_args()


def _remove_or_print(path: Path, *, dry_run: bool) -> None:
    if not dry_run:
        _remove_path(path)


def _within_any(path: Path, parents: set[Path]) -> bool:
    return any(parent in path.parents for parent in parents)


def main() -> int:
    args = _parse_args()
    repo_root = args.repo_root.resolve()

    removable_dirs = {
        "__pycache__",
        ".pytest_cache",
        ".mypy_cache",
        ".ruff_cache",
        ".hypothesis",
    }

    fixed_targets = [
        repo_root / "backend" / "dist",
        repo_root / "backend" / "build",
        repo_root / "frontend" / "build",
        repo_root / "frontend" / "dist",
    ]

    targets: list[Path] = []

    for target in fixed_targets:
        if target.exists():
            targets.append(target)

    for egg_info in (repo_root / "backend").glob("*.egg-info"):
        targets.append(egg_info)

    removable_dir_paths: set[Path] = set()
    for path in repo_root.rglob("*"):
        if path.name in removable_dirs:
            removable_dir_paths.add(path)
            targets.append(path)

    for path in repo_root.rglob("*.pyc"):
        if not _within_any(path, removable_dir_paths):
            targets.append(path)

    removed = 0
    for target in sorted(set(targets)):
        _remove_or_print(target, dry_run=args.dry_run)
        removed += 1
        print(f"[remove] {target}")

    print(f"[done] Removed {removed} artifact(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
