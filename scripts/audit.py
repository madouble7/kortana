#!/usr/bin/env python
"""
Collect audit artifacts for the Kor'tana project.
This script will collect all the required audit information.
"""

import subprocess
import sys
from datetime import datetime
from pathlib import Path


def run_cmd(cmd, cwd=None):
    """Run a command and return its output."""
    try:
        result = subprocess.run(
            cmd, cwd=cwd, capture_output=True, text=True, check=False
        )
        return result.stdout.strip(), result.returncode
    except Exception as e:
        return f"Error: {str(e)}", 1


def write_section(file, title):
    """Write a section header to the file."""
    separator = "=" * 80
    file.write(f"\n{separator}\n")
    file.write(f"# {title}\n")
    file.write(f"{separator}\n\n")


def main():
    """Run the audit collection process."""
    project_root = Path(__file__).parent.parent
    audit_file = project_root / "audit_log.txt"

    print("Collecting audit artifacts for Kor'tana...")
    print(f"Output will be saved to: {audit_file}")

    with open(audit_file, "w", encoding="utf-8") as f:
        # Header
        f.write("# Kor'tana Audit Log\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

        # 1. Branch and commit hash
        write_section(f, "BRANCH AND COMMIT HASH")

        branch, _ = run_cmd(["git", "rev-parse", "--abbrev-ref", "HEAD"], project_root)
        f.write(f"Current branch: {branch}\n\n")

        commit, _ = run_cmd(["git", "rev-parse", "HEAD"], project_root)
        f.write(f"Current commit hash: {commit}\n")

        # 2. List tracked files
        write_section(f, "TRACKED FILES")

        tracked_files, _ = run_cmd(["git", "ls-files"], project_root)
        f.write(tracked_files + "\n\n")

        # Check for problematic files
        f.write("Checking for problematic tracked files:\n")
        problem_patterns = ["venv", "cache", "data", ".env", "__pycache__", ".db"]
        problems_found = False

        for pattern in problem_patterns:
            matching_files = [
                file for file in tracked_files.split("\n") if pattern in file.lower()
            ]
            if matching_files:
                problems_found = True
                f.write(f"\n⚠️ Found files matching '{pattern}':\n")
                for file in matching_files:
                    f.write(f"  - {file}\n")

        if not problems_found:
            f.write("\n✅ No problematic files found in tracking\n")

        # 3. Install and import smoke test
        write_section(f, "INSTALL AND IMPORT TEST")

        f.write("Please run the following commands in a fresh shell:\n\n")
        f.write("```\n")
        f.write("python -m venv .venv && .\.venv\Scripts\activate\n")
        f.write("pip install -e .\n")
        f.write(
            "python -c \"import kortana, importlib, pkg_resources; print('kortana import ok:', kortana.__file__); print('console scripts:', [e.name for e in pkg_resources.iter_entry_points('console_scripts') if 'kortana' in e.name])\"\n"
        )
        f.write("```\n\n")

        # 4. Run pytest with coverage
        write_section(f, "TEST COVERAGE RESULTS")

        f.write("Running pytest with coverage:\n\n")
        test_output, _ = run_cmd(
            [sys.executable, "-m", "pytest", "-q", "--cov=kortana"], project_root
        )
        f.write(test_output + "\n")

        # 5. Config pipeline check
        write_section(f, "CONFIG PIPELINE CHECK")

        f.write("Checking config pipeline:\n\n")
        config_cmd = 'from config import load_config; cfg = load_config(); print("loaded env:", cfg.model_dump())'
        config_output, _ = run_cmd([sys.executable, "-c", config_cmd], project_root)
        f.write(config_output + "\n")

        # 6. Stray yaml read check
        write_section(f, "STRAY YAML READ CHECK")

        f.write("Checking for direct YAML reads:\n\n")

        # Handle different OS platforms
        if sys.platform == "win32":
            yaml_output, _ = run_cmd(
                ["findstr", "/spin", "/c:yaml.safe_load(", '/c:.yaml"', "src\\kortana"],
                project_root,
            )
        else:
            yaml_output, _ = run_cmd(
                ["grep", "-r", "yaml.safe_load\|\.yaml", "src/kortana"], project_root
            )

        if yaml_output:
            f.write("Found potential direct YAML reads:\n\n")
            f.write(yaml_output + "\n")
        else:
            f.write("✅ No direct YAML reads found in src/kortana\n")

        # Summary
        write_section(f, "SUMMARY")
        f.write("✅ All audit artifacts collected\n\n")
        f.write(
            "Please review this audit log and share it with the auditor as requested.\n"
        )

    print(f"\nDone! Audit artifacts collected in {audit_file}")
    print("\nPlease also run the installation test manually in a fresh shell:")
    print("python -m venv .venv && .\.venv\Scripts\\activate")
    print("pip install -e .")
    print(
        "python -c \"import kortana, importlib, pkg_resources; print('kortana import ok:', kortana.__file__); print('console scripts:', [e.name for e in pkg_resources.iter_entry_points('console_scripts') if 'kortana' in e.name])\""
    )


if __name__ == "__main__":
    main()
