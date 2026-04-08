"""Fail when Git history contains blobs at or above the configured size limit."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def _run_git(repo_root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=repo_root,
        check=True,
        capture_output=True,
        text=True,
    )


def find_large_blobs(repo_root: Path, limit_bytes: int) -> list[tuple[int, str, str]]:
    object_map: dict[str, str] = {}
    rev_list = _run_git(repo_root, "rev-list", "--objects", "--all")
    for line in rev_list.stdout.splitlines():
        if not line:
            continue
        object_id, *rest = line.split(" ", 1)
        object_map.setdefault(object_id, rest[0] if rest else "")

    batch_input = "".join(f"{object_id}\n" for object_id in object_map)
    batch = subprocess.run(
        ["git", "cat-file", "--batch-check=%(objectname) %(objecttype) %(objectsize)"],
        cwd=repo_root,
        input=batch_input,
        check=True,
        capture_output=True,
        text=True,
    )

    offenders: list[tuple[int, str, str]] = []
    for line in batch.stdout.splitlines():
        object_id, object_type, size_raw = line.split(" ", 2)
        if object_type != "blob":
            continue
        size = int(size_raw)
        if size >= limit_bytes:
            offenders.append((size, object_id, object_map.get(object_id, "")))

    offenders.sort(reverse=True)
    return offenders


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Check Git history for blobs that exceed the size limit."
    )
    parser.add_argument(
        "--limit-mb",
        type=int,
        default=100,
        help="Blob size limit in megabytes. Default: 100",
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path(__file__).resolve().parents[2],
        help="Repository root. Defaults to the repo containing this script.",
    )
    args = parser.parse_args()

    repo_root = args.repo_root.resolve()
    limit_bytes = args.limit_mb * 1024 * 1024

    try:
        offenders = find_large_blobs(repo_root, limit_bytes)
    except subprocess.CalledProcessError as exc:
        sys.stderr.write(exc.stderr or exc.stdout or str(exc))
        return exc.returncode or 1

    if not offenders:
        print(
            f"Git history blob size check passed: no blobs >= {args.limit_mb} MB."
        )
        return 0

    print(
        f"Git history contains blobs >= {args.limit_mb} MB. Remove them before pushing:"
    )
    for size, object_id, path in offenders:
        size_mb = round(size / (1024 * 1024), 2)
        print(f"- {size_mb:>7} MB  {object_id}  {path or '<no path>'}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
