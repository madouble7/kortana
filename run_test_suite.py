#!/usr/bin/env python
"""Standalone test runner - run without terminal activation issues"""

import json
import os
import subprocess
import sys


def main():
    os.chdir(r"c:\kortana")

    # Path to venv python
    venv_python = r"c:\kortana\.kortana_config_test_env\Scripts\python.exe"

    if not os.path.exists(venv_python):
        print(f"ERROR: Virtual environment python not found at {venv_python}")
        return 1

    # Setup environment
    env = os.environ.copy()
    env["PYTHONPATH"] = r"c:\kortana\src"
    env["PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION"] = "python"

    print("=" * 70)
    print("KORTANA TEST SUITE EXECUTION")
    print("=" * 70)
    print(f"Python: {venv_python}")
    print(f"PYTHONPATH: {env['PYTHONPATH']}")
    print(f"Working Directory: {os.getcwd()}")
    print("=" * 70 + "\n")

    # Run pytest with json output for better parsing
    cmd = [
        venv_python,
        "-m",
        "pytest",
        "tests/",
        "-v",
        "--tb=short",
        "--json-report",
        "--json-report-file=test_report.json",
    ]

    print(f"Running: {' '.join(cmd)}\n")

    result = subprocess.run(cmd, env=env)

    # Try to read the report
    if os.path.exists("test_report.json"):
        print("\n" + "=" * 70)
        print("TEST REPORT SUMMARY")
        print("=" * 70)
        try:
            with open("test_report.json") as f:
                report = json.load(f)
                print(f"Total tests: {report.get('summary', {}).get('total', 'N/A')}")
                print(f"Passed: {report.get('summary', {}).get('passed', 'N/A')}")
                print(f"Failed: {report.get('summary', {}).get('failed', 'N/A')}")
                print(f"Skipped: {report.get('summary', {}).get('skipped', 'N/A')}")
        except Exception as e:
            print(f"Could not parse report: {e}")

    return result.returncode


if __name__ == "__main__":
    sys.exit(main())
