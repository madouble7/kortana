#!/usr/bin/env python
"""
Run All Diagnostics

This script runs all diagnostic tests and saves the results to files.
It does not attempt to fix any issues, only to collect information.
"""

import datetime
import subprocess
import sys
from pathlib import Path


def run_cmd(cmd, output_file=None, cwd=None):
    """Run a command and optionally save output to a file."""
    try:
        print(f"Running: {' '.join(cmd) if isinstance(cmd, list) else cmd}")

        result = subprocess.run(
            cmd, capture_output=True, text=True, cwd=cwd, shell=isinstance(cmd, str)
        )

        output = result.stdout.strip()

        if output_file:
            with open(output_file, "w") as f:
                f.write(output)
            print(f"Results saved to {output_file}")

        return output, result.returncode
    except Exception as e:
        error_msg = f"Error: {str(e)}"
        if output_file:
            with open(output_file, "w") as f:
                f.write(error_msg)
        return error_msg, 1


def main():
    """Run all diagnostic tests."""
    # Create diagnostics directory
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    diag_dir = Path("diagnostics_" + timestamp)
    diag_dir.mkdir(exist_ok=True)

    print(f"Running all diagnostics. Results will be saved to {diag_dir}")

    # Get current directory
    project_root = Path.cwd()

    # Step 1: Run basic execution test
    exec_result_file = diag_dir / "exec_result.txt"
    run_cmd([sys.executable, "test_exec.py"], exec_result_file, project_root)

    # Step 2: Run environment diagnostics
    diag_env_file = diag_dir / "diag_env_result.txt"
    run_cmd(
        [sys.executable, "scripts/diagnose_environment.py"], diag_env_file, project_root
    )

    # Step 3: Run config loading test
    config_load_file = diag_dir / "config_load_result.txt"
    run_cmd(
        [sys.executable, "scripts/test_config_loading.py"],
        config_load_file,
        project_root,
    )

    # Step 4: Run integrated test
    integrated_result_file = diag_dir / "integrated_result.txt"
    run_cmd(
        [sys.executable, "test_config_integrated.py"],
        integrated_result_file,
        project_root,
    )

    # Step 5: Run audit collection
    audit_file = diag_dir / "audit_result.txt"
    run_cmd([sys.executable, "scripts/audit.py"], audit_file, project_root)

    # Create a summary file
    summary_file = diag_dir / "diagnostic_summary.txt"
    with open(summary_file, "w") as f:
        f.write("Kor'tana Diagnostic Summary\n")
        f.write(
            f"Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        )

        # Write summary header
        f.write("=" * 80 + "\n")
        f.write("DIAGNOSTIC TESTS SUMMARY\n")
        f.write("=" * 80 + "\n\n")

        # List all result files
        f.write("Diagnostic results:\n")
        for result_file in sorted(diag_dir.glob("*.txt")):
            if result_file.name != "diagnostic_summary.txt":
                f.write(f"- {result_file.name}\n")

        # Execution environment
        f.write("\n" + "=" * 80 + "\n")
        f.write("EXECUTION ENVIRONMENT\n")
        f.write("=" * 80 + "\n\n")

        # Include basic execution results
        if exec_result_file.exists():
            with open(exec_result_file) as exec_f:
                f.write(exec_f.read() + "\n\n")

    print("\nAll diagnostics completed!")
    print(f"Results are available in the {diag_dir} directory")
    print(f"Summary file: {summary_file}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
