#!/usr/bin/env python
"""
Script to find direct YAML loading in the codebase.
This helps enforce the rule that all config loading should go through config.load_config().
"""

import os
import re
from pathlib import Path


def scan_for_yaml_loading(root_dir):
    """Scan the codebase for direct YAML loading calls."""
    yaml_load_pattern = re.compile(r"(yaml\.safe_load|yaml\.load)\s*\(")
    yaml_open_pattern = re.compile(r"open\s*\([^)]*\.ya?ml")

    exceptions = [
        "config/__init__.py",  # The config loader itself is allowed to use yaml.safe_load
        "config/schema.py",
        "test_",  # Test files are allowed to use yaml.safe_load
        "scripts/",  # Scripts are allowed to use yaml.safe_load
    ]

    results = []

    for root, dirs, files in os.walk(root_dir):
        # Skip venv and hidden directories
        dirs[:] = [
            d
            for d in dirs
            if not d.startswith(".") and not d == "venv" and not d == "venv311"
        ]

        for file in files:
            if not file.endswith(".py"):
                continue

            filepath = os.path.join(root, file)
            relative_path = os.path.relpath(filepath, root_dir)

            # Check if this file is in the exceptions list
            if any(
                relative_path.startswith(exc) or exc in relative_path
                for exc in exceptions
            ):
                continue

            with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                try:
                    content = f.read()

                    yaml_load_matches = yaml_load_pattern.findall(content)
                    yaml_open_matches = yaml_open_pattern.findall(content)

                    if yaml_load_matches or yaml_open_matches:
                        results.append(
                            {
                                "file": relative_path,
                                "yaml_load": bool(yaml_load_matches),
                                "yaml_open": bool(yaml_open_matches),
                            }
                        )
                except Exception as e:
                    print(f"Error reading {filepath}: {str(e)}")

    return results


if __name__ == "__main__":
    root_directory = str(Path(__file__).parent.parent)
    print(f"Scanning for direct YAML loading in {root_directory}...")

    results = scan_for_yaml_loading(root_directory)

    if not results:
        print("✅ No direct YAML loading found outside of allowed files.")
    else:
        print(f"❌ Found {len(results)} files with direct YAML loading:")
        for result in results:
            issues = []
            if result["yaml_load"]:
                issues.append("yaml.load/yaml.safe_load")
            if result["yaml_open"]:
                issues.append("open(...yaml)")

            print(f"  - {result['file']}: {', '.join(issues)}")
        print("\nAll configuration loading should go through config.load_config()")
