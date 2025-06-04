"""
Organize Scripts

This script moves utility scripts from the root directory to the scripts directory.
"""

import os
import shutil
from pathlib import Path


def move_scripts():
    """Move scripts from root to scripts directory."""
    # Get the project root directory
    project_root = Path(__file__).parent.parent.parent
    os.chdir(project_root)
    print(f"Working in directory: {os.getcwd()}")

    # Create scripts directory if it doesn't exist
    os.makedirs("scripts", exist_ok=True)

    # List of scripts to move
    scripts_to_move = [
        "setup_directories.py",
        "check_dependencies.py",
        "fix_permissions.py",
        "fix_syntax.py",
        "fix_brain.py",
        "fix_indentation.py",
        "run_with_output.py",
        "admin_setup.py",
        "simple_kortana.py",
        "ultra_simple.py",
        "run_fixed.py",
        "quick_run.py",
    ]

    # Move scripts from root to scripts directory
    for script in scripts_to_move:
        if os.path.exists(script):
            dest = f"scripts/{script}"
            try:
                shutil.copy2(script, dest)
                print(f"Copied {script} to {dest}")

                # Optionally remove the original
                # os.remove(script)
                # print(f"Removed {script} from root directory")
            except Exception as e:
                print(f"Error copying {script}: {e}")

    # Move scripts from src/ to scripts/ directory
    src_scripts = [
        "src/setup_directories.py",
        "src/check_dependencies.py",
        "src/fix_permissions.py",
        "src/fix_syntax.py",
        "src/fix_brain.py",
        "src/run_with_output.py",
    ]

    for script in src_scripts:
        if os.path.exists(script):
            base_name = os.path.basename(script)
            dest = f"scripts/{base_name}"
            try:
                shutil.copy2(script, dest)
                print(f"Copied {script} to {dest}")

                # Optionally remove the original
                # os.remove(script)
                # print(f"Removed {script}")
            except Exception as e:
                print(f"Error copying {script}: {e}")

    print("Script organization complete!")


if __name__ == "__main__":
    move_scripts()
