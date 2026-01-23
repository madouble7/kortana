import os
import shutil
from pathlib import Path

def cleanup():
    root = Path("c:/kortana")
    target = root / "archive" / "cleanup_2026_01_22"
    target.mkdir(parents=True, exist_ok=True)
    
    keep_files = {
        ".gitignore", "pyproject.toml", "requirements.txt",
        "alembic.ini", "pytest.ini", "mypy.ini", ".python-version",
        "config.yaml", "covenant.yaml", "TASKS.md", "README.md",
        "kortana.yaml", "kortana.code-workspace", "alembic", "archive",
        "config", "data", "demos", "discord", "docs", "examples",
        "kortana.core", "kortana.team", "lobechat-frontend", "notebooks",
        "queues", "relays", "scripts", "src", "state", "tests", "tools",
        "voice", ".kortana_config_test_env", ".venv", ".git", ".github",
        ".vscode", ".mypy_cache", ".pytest_cache", ".ruff_cache", ".benchmarks",
        ".cacheme", ".continue", ".ruff.toml"
    }
    
    for item in root.iterdir():
        if item.name not in keep_files and not item.name.startswith("archive"):
            try:
                print(f"Moving {item.name} to cleanup folder...")
                shutil.move(str(item), str(target / item.name))
            except Exception as e:
                print(f"Failed to move {item.name}: {e}")

if __name__ == "__main__":
    cleanup()
