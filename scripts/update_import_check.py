#!/usr/bin/env python3
"""Create or update the audit package and check imports."""

import subprocess
import sys

# First, try fixing imports
try:
    subprocess.run([sys.executable, "fix_imports.py"], check=True)
except FileNotFoundError:
    print("Warning: fix_imports.py not found, skipping import fixes")
except subprocess.CalledProcessError as e:
    print(f"Warning: fix_imports.py failed with exit code {e.returncode}")

# Then run an updated import check
sys.path.insert(0, "src")

try:
    import kortana

    print(f"kortana imported from: {kortana.__file__}")

    import pkg_resources

    console_scripts = [
        e.name
        for e in pkg_resources.iter_entry_points("console_scripts")
        if "kortana" in e.name
    ]
    print(f"console scripts: {console_scripts}")
except Exception as e:
    print(f"Error importing kortana: {e}")
    print(f"sys.path: {sys.path}")

if __name__ == "__main__":
    pass
