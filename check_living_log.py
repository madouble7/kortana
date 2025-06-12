import subprocess
import sys

# Files that require Living Log update if changed
CORE_DIRS = ["src", "config", "data"]
BLUEPRINT = "KOR'TANA_BLUEPRINT.md"


def get_staged_files():
    result = subprocess.run(
        ["git", "diff", "--cached", "--name-only"], capture_output=True, text=True
    )
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def main():
    staged = get_staged_files()
    core_changed = any(f.startswith(tuple(CORE_DIRS)) for f in staged)
    blueprint_staged = any(f == BLUEPRINT for f in staged)
    if core_changed and not blueprint_staged:
        print("\n[PRE-COMMIT BLOCKED]")
        print("You are committing changes to core code/config/data files.")
        print(f"Please update and stage {BLUEPRINT} (Living Log) as per protocol.")
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
