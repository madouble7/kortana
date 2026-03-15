#!/usr/bin/env python
"""
Collect audit artifacts for the repository.

This script runs all the verification steps and collects the results
into a single audit_log.txt file.
"""

import datetime
import os
import subprocess
import sys
from pathlib import Path


def run_command(cmd, cwd=None, env=None):
    """Run a command and return the output."""
    try:
        if env is None:
            env = os.environ.copy()

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=cwd,
            env=env,
            shell=isinstance(cmd, str),
        )
        return result.stdout.strip(), result.returncode
    except Exception as e:
        return f"Error: {str(e)}", 1


def print_section(file, title):
    """Print a section header to the file."""
    file.write("\n" + "=" * 80 + "\n")
    file.write(f"# {title}\n")
    file.write("=" * 80 + "\n\n")


def main():
    """Collect audit artifacts."""
    project_root = Path(__file__).parent.parent
    audit_log = project_root / "audit_log.txt"
    diagnostics_dir = project_root / "diagnostics"

    # Create diagnostics directory if it doesn't exist
    diagnostics_dir.mkdir(exist_ok=True)

    with open(audit_log, "w") as f:
        # Header
        f.write("# Kor'tana Audit Log\n")
        f.write(
            f"Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        )

        # 1. Capture branch and commit hash
        print_section(f, "BRANCH AND COMMIT HASH")

        branch_output, _ = run_command(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=project_root
        )
        f.write(f"Current branch: {branch_output}\n\n")

        commit_output, _ = run_command(["git", "rev-parse", "HEAD"], cwd=project_root)
        f.write(f"Current commit hash: {commit_output}\n\n")

        # 2. List all tracked files
        print_section(f, "TRACKED FILES")

        tracked_files, _ = run_command(["git", "ls-files"], cwd=project_root)
        f.write(tracked_files + "\n\n")

        # Check for problematic files
        f.write("Checking for problematic tracked files:\n")
        problem_patterns = ["venv", "cache", "data", ".env", "__pycache__", ".db"]
        problems_found = False

        for pattern in problem_patterns:
            files_with_pattern = [
                file for file in tracked_files.split("\n") if pattern in file.lower()
            ]
            if files_with_pattern:
                problems_found = True
                f.write(f"⚠️ Found files matching '{pattern}':\n")
                for file in files_with_pattern:
                    f.write(f"  - {file}\n")

        if not problems_found:
            f.write("✅ No problematic files found in tracking\n\n")

        # 3. Install and import smoke test
        print_section(f, "INSTALL AND IMPORT TEST")

        f.write(
            "Note: For this section, manually run the following commands in a fresh shell:\n\n"
        )
        f.write("```\n")
        f.write("python -m venv .venv && .\\.venv\\Scripts\activate\n")
        f.write("pip install -e .\n")
        f.write(
            "python -c \"import kortana, importlib, pkg_resources; print('kortana import ok:', kortana.__file__); print('console scripts:', [e.name for e in pkg_resources.iter_entry_points('console_scripts') if 'kortana' in e.name])\"\n"
        )
        f.write("```\n\n")

        # Try to run the import test in the current environment
        f.write(
            "Attempting in current environment (may not be accurate, refer to manual test):\n\n"
        )
        import_test_cmd = 'import kortana, importlib, pkg_resources; print("kortana import ok:", kortana.__file__); print("console scripts:", [e.name for e in pkg_resources.iter_entry_points("console_scripts") if "kortana" in e.name])'
        import_output, import_status = run_command(
            [sys.executable, "-c", import_test_cmd], cwd=project_root
        )

        if import_status == 0:
            f.write(import_output + "\n\n")
        else:
            f.write(
                "Import test failed in current environment. Please run manually.\n\n"
            )

        # 4. Environment diagnostic
        print_section(f, "ENVIRONMENT DIAGNOSTIC")

        f.write("Python environment information:\n\n")
        env_cmd = 'import sys, os, platform; print(f"Python {platform.python_version()} ({sys.executable})")'
        env_output, _ = run_command([sys.executable, "-c", env_cmd], cwd=project_root)
        f.write(env_output + "\n\n")

        # Add diagnostic info from test_exec.py
        exec_output, _ = run_command([sys.executable, "test_exec.py"], cwd=project_root)
        f.write("Output from test_exec.py:\n\n")
        f.write(exec_output + "\n\n")

        f.write("PYTHONPATH entries:\n")
        path_cmd = (
            'import sys; [print(f"  [{i}] {path}") for i, path in enumerate(sys.path)]'
        )
        path_output, _ = run_command([sys.executable, "-c", path_cmd], cwd=project_root)
        f.write(path_output + "\n\n")

        # Save diagnostics from other scripts
        run_command(
            [sys.executable, "scripts/diagnose_environment.py"],
            cwd=project_root,
            env=dict(os.environ, PYTHONPATH=str(project_root)),
        )
        f.write(
            "Full environment diagnostics saved to: diagnostics_dir/diag_env_result.txt\n\n"
        )

        run_command(
            [sys.executable, "test_config_integrated.py"],
            cwd=project_root,
            env=dict(os.environ, PYTHONPATH=str(project_root)),
        )
        f.write("Integrated test results saved to: config_test_*.txt\n\n")

        # 5. Run full test/CI suite
        print_section(f, "TEST COVERAGE RESULTS")

        f.write("Running pytest with coverage:\n\n")
        test_output, _ = run_command(
            [sys.executable, "-m", "pytest", "-q", "--cov=kortana"], cwd=project_root
        )
        f.write(test_output + "\n\n")

        # 6. Config pipeline check
        print_section(f, "CONFIG PIPELINE CHECK")

        f.write("Checking config pipeline:\n\n")
        config_cmd = 'from kortana.config import load_config; cfg = load_config(); print("loaded env:", cfg.model_dump())'
        config_output, config_status = run_command(
            [sys.executable, "-c", config_cmd], cwd=project_root
        )

        if config_status == 0:
            f.write(config_output + "\n\n")
        else:
            f.write("Config pipeline check failed. Error:\n")
            f.write(config_output + "\n\n")

        # Run config loading test and save results
        run_command(
            [sys.executable, "scripts/test_config_loading.py"],
            cwd=project_root,
            env=dict(os.environ, PYTHONPATH=str(project_root)),
        )
        f.write(
            "Detailed config loading test results saved to: config_load_result.txt\n\n"
        )

        # 7. Stray yaml read grep
        print_section(f, "STRAY YAML READ CHECK")

        f.write("Checking for direct YAML reads:\n\n")
        grep_output, _ = run_command(
            ["findstr", "/spin", "/c:yaml.safe_load(", '/c:.yaml"', "src\\kortana"],
            cwd=project_root,
        )

        if not grep_output:
            f.write("✅ No direct YAML reads found in src/kortana\n\n")
        else:
            f.write("Found potential direct YAML reads:\n")
            f.write(grep_output + "\n\n")

        # 8. Run the comprehensive diagnostics
        print_section(f, "COMPREHENSIVE DIAGNOSTICS")

        f.write("Running comprehensive diagnostics...\n\n")
        run_command(
            [sys.executable, "scripts/run_all_diagnostics.py"], cwd=project_root
        )
        f.write("Comprehensive diagnostics saved to: diagnostics_* directory\n")

        # Summary
        print_section(f, "SUMMARY")
        f.write("✅ All audit artifacts collected\n")
        f.write("✅ Additional diagnostics saved to separate files\n")
        f.write(
            "\nPlease review the audit_log.txt file and diagnostic files, and share them with the auditor as requested.\n"
        )
        f.write(
            "\nIMPORTANT: No changes to configuration code should be made until sanctuary (matt) has reviewed these results.\n"
        )

    print(f"Audit artifacts collected in {audit_log}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
