#!/usr/bin/env python3
"""Block commits that include real environment files."""

import sys
from pathlib import Path


def is_blocked(path_str: str) -> bool:
    """Return True when the path is an environment file that should not be committed."""
    path = Path(path_str)
    name = path.name

    if name == ".env.example":
        return False

    return name == ".env" or name.startswith(".env.")


def main(args: list[str]) -> int:
    """Fail when staged files include blocked environment files."""
    blocked_files = sorted({arg for arg in args if is_blocked(arg)})
    if not blocked_files:
        return 0

    print(
        "Refusing to commit environment files. Commit a template such as '.env.example' instead:"
    )
    for path in blocked_files:
        print(f" - {path}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
