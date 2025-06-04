#!/usr/bin/env python
"""
Environment Report Generator

This script generates a standardized report of the current Python environment,
including virtual environment information, sys.path, and installed packages.
"""

import datetime
import os
import platform
import site
import subprocess
import sys
from pathlib import Path


def run_cmd(cmd, shell=False):
    """Run a command and return its output."""
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, shell=shell, check=False
        )
        return result.stdout.strip()
    except Exception as e:
        return f"Error: {str(e)}"


def print_section(title, file=None):
    """Print a section header."""
    separator = "=" * 80
    if file:
        file.write(f"\n{separator}\n")
        file.write(f"# {title}\n")
        file.write(f"{separator}\n\n")
    else:
        print(f"\n{separator}")
        print(f"# {title}")
        print(f"{separator}\n")


def generate_report(output_file=None):
    """Generate an environment report."""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if output_file:
        f = open(output_file, "w")
    else:
        f = None

    try:
        # Header
        if f:
            f.write("Kor'tana Environment Report\n")
            f.write(f"Generated: {timestamp}\n")
        else:
            print("Kor'tana Environment Report")
            print(f"Generated: {timestamp}")

        # System Information
        print_section("SYSTEM INFORMATION", f)

        system_info = {
            "Platform": platform.platform(),
            "Python Version": platform.python_version(),
            "Python Implementation": platform.python_implementation(),
            "Python Executable": sys.executable,
            "Current Working Directory": os.getcwd(),
        }

        for key, value in system_info.items():
            if f:
                f.write(f"{key}: {value}\n")
            else:
                print(f"{key}: {value}")

        # Virtual Environment
        print_section("VIRTUAL ENVIRONMENT", f)

        venv_path = os.environ.get("VIRTUAL_ENV")
        if venv_path:
            venv_info = f"Active Virtual Environment: {venv_path}"
            if f:
                f.write(f"{venv_info}\n")
            else:
                print(venv_info)

            # Check site-packages
            site_packages = [p for p in site.getsitepackages() if venv_path in p]
            if site_packages:
                if f:
                    f.write("\nVirtual Environment Site Packages:\n")
                else:
                    print("\nVirtual Environment Site Packages:")

                for pkg in site_packages:
                    if f:
                        f.write(f"  - {pkg}\n")
                    else:
                        print(f"  - {pkg}")
        else:
            no_venv = "No active virtual environment detected"
            if f:
                f.write(f"{no_venv}\n")
            else:
                print(no_venv)

        # sys.path
        print_section("PYTHON PATH", f)

        if f:
            f.write("sys.path entries:\n")
        else:
            print("sys.path entries:")

        for i, path in enumerate(sys.path):
            if f:
                f.write(f"  [{i}] {path}\n")
            else:
                print(f"  [{i}] {path}")

        # Environment Variables
        print_section("ENVIRONMENT VARIABLES", f)

        relevant_vars = [
            "PYTHONPATH",
            "KORTANA_ENV",
            "DOTENV_PATH",
            "VIRTUAL_ENV",
            "KORTANA_CONFIG_DIR",
        ]

        if f:
            f.write("Relevant environment variables:\n")
        else:
            print("Relevant environment variables:")

        for var in relevant_vars:
            value = os.environ.get(var, "Not set")
            if f:
                f.write(f"  {var}: {value}\n")
            else:
                print(f"  {var}: {value}")

        # Installed Packages
        print_section("INSTALLED PACKAGES", f)

        pip_output = run_cmd([sys.executable, "-m", "pip", "list"])

        if f:
            f.write("Installed packages (pip list):\n\n")
            f.write(pip_output + "\n")
        else:
            print("Installed packages (pip list):\n")
            print(pip_output)

        # Config Directory
        print_section("CONFIGURATION FILES", f)

        project_root = Path.cwd()
        config_dir = project_root / "config"

        if config_dir.exists():
            if f:
                f.write(f"Config directory: {config_dir}\n\n")
                f.write("YAML files:\n")
            else:
                print(f"Config directory: {config_dir}\n")
                print("YAML files:")

            yaml_files = list(config_dir.glob("*.yaml"))
            if yaml_files:
                for yaml_file in yaml_files:
                    if f:
                        f.write(f"  - {yaml_file.name}\n")
                        f.write(f"    Size: {yaml_file.stat().st_size} bytes\n")
                        f.write(
                            f"    Last modified: {datetime.datetime.fromtimestamp(yaml_file.stat().st_mtime)}\n"
                        )
                    else:
                        print(f"  - {yaml_file.name}")
                        print(f"    Size: {yaml_file.stat().st_size} bytes")
                        print(
                            f"    Last modified: {datetime.datetime.fromtimestamp(yaml_file.stat().st_mtime)}"
                        )
            else:
                if f:
                    f.write("  No YAML files found\n")
                else:
                    print("  No YAML files found")
        else:
            if f:
                f.write(f"Config directory not found: {config_dir}\n")
            else:
                print(f"Config directory not found: {config_dir}")

        # Test Execution
        print_section("TEST EXECUTION", f)

        test_cmd = 'import sys; print("Python executable:", sys.executable); print("sys.path[0]:", sys.path[0])'
        test_output = run_cmd([sys.executable, "-c", test_cmd])

        if f:
            f.write("Simple Python test execution:\n\n")
            f.write(test_output + "\n")
        else:
            print("Simple Python test execution:\n")
            print(test_output)

        # Summary
        print_section("SUMMARY", f)

        if f:
            f.write("Environment report complete.\n")
            f.write("\nIMPORTANT: Do NOT proceed with config code or env refactors\n")
            f.write("until sanctuary (matt) has reviewed and confirmed a stable,\n")
            f.write("reproducible environment based on these diagnostic results.\n")
        else:
            print("Environment report complete.")
            print("\nIMPORTANT: Do NOT proceed with config code or env refactors")
            print("until sanctuary (matt) has reviewed and confirmed a stable,")
            print("reproducible environment based on these diagnostic results.")

    finally:
        if f:
            f.close()
            print(f"\nEnvironment report saved to: {output_file}")


if __name__ == "__main__":
    output_dir = "diagnostic_results"
    os.makedirs(output_dir, exist_ok=True)

    output_file = os.path.join(output_dir, "environment_report.txt")
    generate_report(output_file)

    print("\nEnvironment report generation complete.")
    print(f"Report saved to: {output_file}")
    print("\nReview the report and share it with sanctuary (matt) for analysis.")
    print("Do NOT proceed with any config changes until after review.")
