"""Create local environment files from checked-in examples when missing."""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path(__file__).resolve().parents[2],
        help="Repository root containing the example env files.",
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    repo_root = args.repo_root.resolve()
    created = 0

    for source_name, target_name in (
        (".env.example", ".env"),
        (".env.prod.example", ".env.prod"),
    ):
        source = repo_root / source_name
        target = repo_root / target_name

        if not source.exists():
            print(f"[skip] Missing template: {source}")
            continue

        if target.exists():
            print(f"[keep] Exists already: {target}")
            continue

        shutil.copyfile(source, target)
        created += 1
        print(f"[create] {target} <- {source}")

    if created == 0:
        print("[done] No files needed to be created")
    else:
        print(f"[done] Created {created} environment file(s)")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
