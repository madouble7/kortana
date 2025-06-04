#!/usr/bin/env python
"""
Configuration Loading Test Script

This script tests the configuration loading mechanism in isolation,
helping diagnose any issues with the config module.

Run this script using:
python scripts/test_config_loading.py
"""

import json
import os
import sys
from pathlib import Path

import yaml


def print_section(title):
    """Print a section header."""
    print("\n" + "=" * 80)
    print(f"# {title}")
    print("=" * 80)


def inspect_yaml_file(file_path):
    """Inspect a YAML file and print its contents."""
    if not file_path.exists():
        print(f"❌ File not found: {file_path}")
        return

    print(f"File: {file_path}")
    print(f"Size: {file_path.stat().st_size} bytes")

    try:
        with open(file_path, "r") as f:
            content = f.read()

        print("\nRaw content:")
        print("-" * 40)
        print(content[:500] + "..." if len(content) > 500 else content)
        print("-" * 40)

        try:
            data = yaml.safe_load(content)
            print("\nParsed YAML:")
            print(
                json.dumps(data, indent=2)[:1000] + "..."
                if len(json.dumps(data, indent=2)) > 1000
                else json.dumps(data, indent=2)
            )
        except Exception as e:
            print(f"❌ Error parsing YAML: {str(e)}")

    except Exception as e:
        print(f"❌ Error reading file: {str(e)}")


def test_direct_yaml_loading():
    """Test direct YAML loading from files."""
    print_section("DIRECT YAML LOADING TEST")

    project_root = Path.cwd()
    config_dir = project_root / "config"

    if not config_dir.exists():
        print(f"❌ Config directory not found: {config_dir}")
        return

    # Check all yaml files in the config directory
    yaml_files = list(config_dir.glob("*.yaml"))
    if not yaml_files:
        print("❌ No YAML files found in config directory")
        return

    print(f"Found {len(yaml_files)} YAML files in config directory:")
    for yaml_file in yaml_files:
        print(f"\n-- {yaml_file.name} --")
        inspect_yaml_file(yaml_file)


def test_config_import():
    """Test importing the config module."""
    print_section("CONFIG MODULE IMPORT TEST")

    try:
        # Ensure project root is in path
        project_root = Path.cwd()
        if str(project_root) not in sys.path:
            sys.path.insert(0, str(project_root))
            print(f"Added {project_root} to sys.path")

        # Try to import the config module
        import config

        print("✅ Successfully imported config module")
        print(f"Config module file: {config.__file__}")
        print(f"Config module path: {os.path.dirname(config.__file__)}")

        # Check for load_config function
        if hasattr(config, "load_config"):
            print("✅ load_config function exists in config module")
            print(f"load_config type: {type(config.load_config)}")
        else:
            print("❌ load_config function NOT found in config module")
            print(f"Available attributes: {dir(config)}")

    except ImportError as e:
        print(f"❌ Error importing config module: {str(e)}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error importing config module: {str(e)}")
        return False

    return True


def test_config_load_function(test_env=None):
    """Test the config.load_config() function."""
    print_section(
        f"CONFIG LOAD FUNCTION TEST {'(ENV=' + test_env + ')' if test_env else ''}"
    )

    # Save current environment variables
    original_env = {}
    if "KORTANA_ENV" in os.environ:
        original_env["KORTANA_ENV"] = os.environ["KORTANA_ENV"]

    try:
        # Set test environment if specified
        if test_env:
            os.environ["KORTANA_ENV"] = test_env
            print(f"Set KORTANA_ENV={test_env}")
        elif "KORTANA_ENV" in os.environ:
            print(f"Using existing KORTANA_ENV={os.environ['KORTANA_ENV']}")
        else:
            print("KORTANA_ENV not set (will use default)")

        # Import and call load_config
        from config import load_config

        print("Calling load_config()...")
        config = load_config()

        print("✅ load_config() executed successfully!")

        # Print config details
        print(f"\nConfig type: {type(config).__name__}")

        # If Pydantic model, use model_dump
        if hasattr(config, "model_dump"):
            try:
                dump = config.model_dump()
                print("\nConfig dump:")
                print(
                    json.dumps(dump, indent=2)[:1000] + "..."
                    if len(json.dumps(dump, indent=2)) > 1000
                    else json.dumps(dump, indent=2)
                )
            except Exception as e:
                print(f"❌ Error dumping config: {str(e)}")
                # Try direct __dict__ access
                if hasattr(config, "__dict__"):
                    print(f"Config __dict__: {config.__dict__}")
        else:
            # If not a Pydantic model, use __dict__
            print(f"Config attributes: {dir(config)}")
            if hasattr(config, "__dict__"):
                print(f"Config __dict__: {config.__dict__}")

    except Exception as e:
        print(f"❌ Error testing load_config: {str(e)}")
        import traceback

        traceback.print_exc()

    finally:
        # Restore original environment
        if "KORTANA_ENV" in original_env:
            os.environ["KORTANA_ENV"] = original_env["KORTANA_ENV"]
        elif "KORTANA_ENV" in os.environ:
            del os.environ["KORTANA_ENV"]


def test_specific_yaml_paths():
    """Test specific YAML file paths that might be used in config loading."""
    print_section("YAML PATHS TEST")

    project_root = Path.cwd()

    # Possible config directories
    config_dirs = [
        project_root / "config",
        project_root / "src" / "config",
    ]

    # Possible YAML file paths
    yaml_paths = []
    for config_dir in config_dirs:
        if config_dir.exists():
            yaml_paths.extend(
                [
                    config_dir / "default.yaml",
                    config_dir / "development.yaml",
                    config_dir / "production.yaml",
                    config_dir / "test.yaml",
                    # Check other yaml files in the directory
                    *config_dir.glob("*.yaml"),
                ]
            )

    # Check each path
    for path in sorted(set(yaml_paths)):
        if path.exists():
            print(f"✅ Found YAML file: {path}")
        else:
            print(f"❌ Missing YAML file: {path}")


def main():
    """Run all tests."""
    print("=" * 80)
    print("KORTANA CONFIG LOADING TEST")
    print(f"Run at: {os.path.abspath(__file__)}")
    print("=" * 80)

    try:
        test_specific_yaml_paths()
        test_direct_yaml_loading()

        if test_config_import():
            # Only test load_config if import succeeded
            test_config_load_function()  # Test with default env
            test_config_load_function("development")  # Test with development env
            test_config_load_function("production")  # Test with production env

        print("\n" + "=" * 80)
        print("CONFIG LOADING TESTS COMPLETE")
        print("=" * 80)

        return 0
    except Exception as e:
        print(f"\nError in test: {str(e)}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
