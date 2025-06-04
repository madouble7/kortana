#!/usr/bin/env python
"""
Integrated Environment and Config Test

This script tests both the Python environment and config loading
in an integrated fashion, saving the results to a file.

It doesn't rely on external imports beyond the standard library
until it tries to import the config module for testing.

Run this script using:
python test_config_integrated.py
"""

import datetime
import json
import os
import platform
import sys
import traceback
from pathlib import Path


def print_and_log(message, file=None):
    """Print message and optionally log it to a file."""
    print(message)
    if file:
        file.write(message + "\n")


def print_section(title, file=None):
    """Print a section header."""
    separator = "=" * 80
    print_and_log("\n" + separator, file)
    print_and_log(f"# {title}", file)
    print_and_log(separator, file)


def run_test():
    """Run the integrated test."""
    # Create output file
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"config_test_{timestamp}.txt"

    with open(output_file, "w", encoding="utf-8") as f:
        print_and_log("KORTANA INTEGRATED ENVIRONMENT AND CONFIG TEST", f)
        print_and_log(
            f"Timestamp: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", f
        )
        print_and_log(f"Output file: {output_file}", f)

        # Environment information
        print_section("ENVIRONMENT INFORMATION", f)

        print_and_log(f"Python Version: {platform.python_version()}", f)
        print_and_log(f"Python Executable: {sys.executable}", f)
        print_and_log(f"Current Working Directory: {os.getcwd()}", f)

        # Virtual environment
        venv_path = os.environ.get("VIRTUAL_ENV")
        if venv_path:
            print_and_log(f"Active Virtual Environment: {venv_path}", f)
        else:
            print_and_log("No active virtual environment detected", f)

        # sys.path
        print_and_log("\nPYTHONPATH (sys.path):", f)
        for i, path in enumerate(sys.path):
            print_and_log(f"  [{i}] {path}", f)

        # Environment variables
        print_and_log("\nRelevant Environment Variables:", f)
        for var in [
            "PYTHONPATH",
            "KORTANA_ENV",
            "DOTENV_PATH",
            "VIRTUAL_ENV",
            "KORTANA_CONFIG_DIR",
        ]:
            print_and_log(f"  {var}: {os.environ.get(var, 'Not set')}", f)

        # File system check
        print_section("FILE SYSTEM CHECK", f)

        project_root = Path.cwd()
        print_and_log(f"Project Root: {project_root}", f)

        # Check important directories
        directories = ["config", "src", "venv311", ".venv", "tests"]
        for directory in directories:
            path = project_root / directory
            exists = path.exists()
            print_and_log(f"{directory}: {'✅ Exists' if exists else '❌ Missing'}", f)

        # Check YAML files
        config_dir = project_root / "config"
        if config_dir.exists():
            yaml_files = list(config_dir.glob("*.yaml"))
            print_and_log("\nYAML files in config directory:", f)
            for yaml_file in yaml_files:
                print_and_log(f"  - {yaml_file.name}", f)

        # Config import test
        print_section("CONFIG IMPORT TEST", f)

        try:
            # Ensure project root is in path
            if str(project_root) not in sys.path:
                sys.path.insert(0, str(project_root))
                print_and_log(f"Added {project_root} to sys.path", f)

            # Try to import config module
            print_and_log("Attempting to import config module...", f)
            import config

            print_and_log("✅ Config module imported successfully!", f)
            print_and_log(f"Config module file: {config.__file__}", f)

            # Check for load_config function
            if hasattr(config, "load_config"):
                print_and_log("✅ load_config function found in config module", f)

                # Try to call load_config
                print_section("CONFIG LOADING TEST", f)
                try:
                    print_and_log("Calling load_config()...", f)
                    settings = config.load_config()
                    print_and_log("✅ Configuration loaded successfully!", f)

                    # Print config details
                    print_and_log(f"Config type: {type(settings).__name__}", f)

                    # Try different ways to extract config data
                    if hasattr(settings, "model_dump"):
                        try:
                            dump = settings.model_dump()
                            print_and_log("\nConfig dump:", f)
                            formatted_dump = json.dumps(dump, indent=2)
                            print_and_log(
                                formatted_dump[:1000] + "..."
                                if len(formatted_dump) > 1000
                                else formatted_dump,
                                f,
                            )
                        except Exception as e:
                            print_and_log(f"Error dumping config: {str(e)}", f)

                    elif hasattr(settings, "__dict__"):
                        print_and_log("\nConfig attributes:", f)
                        for key, value in settings.__dict__.items():
                            print_and_log(f"  {key}: {value}", f)

                    else:
                        print_and_log(
                            "\nConfig object has no __dict__ or model_dump method", f
                        )
                        print_and_log(f"Available attributes: {dir(settings)}", f)

                except Exception as e:
                    print_and_log(f"❌ Error loading configuration: {str(e)}", f)
                    print_and_log(traceback.format_exc(), f)
            else:
                print_and_log("❌ load_config function NOT found in config module", f)
                print_and_log(f"Available attributes: {dir(config)}", f)

        except ImportError as e:
            print_and_log(f"❌ Error importing config module: {str(e)}", f)

        except Exception as e:
            print_and_log(f"❌ Unexpected error: {str(e)}", f)
            print_and_log(traceback.format_exc(), f)

        # Summary
        print_section("TEST SUMMARY", f)
        print_and_log("Test completed. See above for results.", f)
        print_and_log(f"Full results saved to: {output_file}", f)

    print(f"\nTest completed. Results saved to: {output_file}")
    return output_file


if __name__ == "__main__":
    output_file = run_test()
    print(f"\nTo view the test results, run: type {output_file}")
