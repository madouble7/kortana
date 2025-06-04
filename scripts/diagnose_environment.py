#!/usr/bin/env python
"""
Environment and Configuration Diagnostic Script

This script performs a comprehensive diagnosis of:
1. The Python environment currently being used
2. The configuration loading process
3. The import paths and module resolution

Run this script using:
python scripts/diagnose_environment.py
"""

import importlib
import importlib.util
import inspect
import os
import platform
import site
import sys
from pathlib import Path


def print_section(title):
    """Print a section header."""
    print("\n" + "=" * 80)
    print(f"# {title}")
    print("=" * 80)


def diagnose_environment():
    """Diagnose the current Python environment."""
    print_section("ENVIRONMENT DIAGNOSIS")

    # Basic Python information
    print(f"Python Version: {platform.python_version()}")
    print(f"Python Implementation: {platform.python_implementation()}")
    print(f"Python Executable: {sys.executable}")
    print(f"Current Working Directory: {os.getcwd()}")

    # Environment variables
    print("\nRelevant Environment Variables:")
    env_vars = [
        "PYTHONPATH",
        "KORTANA_ENV",
        "DOTENV_PATH",
        "VIRTUAL_ENV",
        "KORTANA_CONFIG_DIR",
    ]
    for var in env_vars:
        print(f"  {var}: {os.environ.get(var, 'Not set')}")

    # sys.path
    print("\nPYTHONPATH (sys.path):")
    for i, path in enumerate(sys.path):
        print(f"  [{i}] {path}")

    # Check virtual environment
    venv_path = os.environ.get("VIRTUAL_ENV")
    if venv_path:
        print(f"\nActive Virtual Environment: {venv_path}")
        site_packages = [p for p in site.getsitepackages() if venv_path in p]
        if site_packages:
            print("Virtual Environment Site Packages:")
            for pkg in site_packages:
                print(f"  - {pkg}")
    else:
        print("\nNo active virtual environment detected")


def check_import(module_name, show_details=True):
    """Try to import a module and show details about it."""
    try:
        module = importlib.import_module(module_name)
        if show_details:
            print(f"Successfully imported: {module_name}")
            print(f"  Module file: {module.__file__}")

            # Module details
            try:
                spec = importlib.util.find_spec(module_name)
                if spec:
                    print(f"  Module origin: {spec.origin}")
                    print(
                        f"  Module submodule search locations: {spec.submodule_search_locations}"
                    )
            except Exception as e:
                print(f"  Error getting module spec: {str(e)}")
        return True, module
    except ImportError as e:
        print(f"Failed to import {module_name}: {str(e)}")
        return False, None
    except Exception as e:
        print(f"Unexpected error importing {module_name}: {str(e)}")
        return False, None


def diagnose_imports():
    """Diagnose imports of key modules."""
    print_section("IMPORTS DIAGNOSIS")

    # Check key modules
    modules = ["config", "kortana"]
    for module_name in modules:
        success, _ = check_import(module_name)

    # Special check for config
    print("\nDetailed config module diagnosis:")
    success, config_module = check_import("config", show_details=False)

    if success:
        print(f"Config module file: {config_module.__file__}")
        print(f"Config module path: {os.path.dirname(config_module.__file__)}")

        # Check if load_config exists
        if hasattr(config_module, "load_config"):
            print("load_config function exists in config module")

            # Try to get source code of load_config
            try:
                source = inspect.getsource(config_module.load_config)
                print("\nload_config source code:")
                print("-" * 40)
                print(
                    source[:500] + "..." if len(source) > 500 else source
                )  # Show first 500 chars only
                print("-" * 40)
            except Exception as e:
                print(f"Could not get source code: {str(e)}")
        else:
            print("load_config function does NOT exist in config module")


def diagnose_config_loading():
    """Diagnose the config loading process."""
    print_section("CONFIG LOADING DIAGNOSIS")

    # Try to import config
    success, config_module = check_import("config", show_details=False)

    if success and hasattr(config_module, "load_config"):
        # Set up test environment variables
        original_env = {}
        test_vars = {
            "KORTANA_ENV": "test",
            "DOTENV_PATH": ".env.example" if Path(".env.example").exists() else None,
        }

        # Save original env vars
        for var in test_vars:
            if var in os.environ:
                original_env[var] = os.environ[var]

        # Set test env vars
        for var, value in test_vars.items():
            if value is not None:
                os.environ[var] = value

        try:
            print("Attempting to load configuration...")
            config = config_module.load_config()
            print("✅ Configuration loaded successfully!")

            # Check config properties
            print("\nConfiguration properties:")
            if hasattr(config, "model_dump"):
                try:
                    dump = config.model_dump()
                    print("Config dump (first 1000 chars):")
                    print(
                        str(dump)[:1000] + "..." if len(str(dump)) > 1000 else str(dump)
                    )
                except Exception as e:
                    print(f"Error dumping config: {str(e)}")
            else:
                print(f"Config type: {type(config).__name__}")
                if hasattr(config, "__dict__"):
                    print(f"Config attributes: {list(config.__dict__.keys())}")

        except Exception as e:
            print(f"❌ Error loading configuration: {str(e)}")
            import traceback

            traceback.print_exc()

        # Restore original env vars
        for var in test_vars:
            if var in original_env:
                os.environ[var] = original_env[var]
            elif var in os.environ:
                del os.environ[var]


def check_filesystem():
    """Check filesystem structure and important files."""
    print_section("FILESYSTEM CHECK")

    # Project root
    project_root = Path.cwd()
    print(f"Project Root: {project_root}")

    # Check important directories
    directories = ["config", "src", "venv311", ".venv", "tests"]
    for directory in directories:
        path = project_root / directory
        exists = path.exists()
        print(f"{directory}: {'✅ Exists' if exists else '❌ Missing'}")

        if exists and directory == "config":
            # List yaml files in config directory
            yaml_files = list(path.glob("*.yaml"))
            print("  YAML files in config directory:")
            for yaml_file in yaml_files:
                print(f"    - {yaml_file.name}")

    # Check .env files
    env_files = [".env", ".env.example", ".env.template"]
    for env_file in env_files:
        path = project_root / env_file
        if path.exists():
            print(f"{env_file}: ✅ Exists")
        else:
            print(f"{env_file}: ❌ Missing")


def main():
    """Run all diagnostic functions."""
    print("=" * 80)
    print("KORTANA ENVIRONMENT AND CONFIG DIAGNOSTIC")
    print(f"Run at: {os.path.abspath(__file__)}")
    print("=" * 80)

    try:
        # Add project root to path if not already there
        project_root = str(Path(__file__).parent.parent)
        if project_root not in sys.path:
            sys.path.insert(0, project_root)
            print(f"Added {project_root} to sys.path")

        diagnose_environment()
        check_filesystem()
        diagnose_imports()
        diagnose_config_loading()

        print("\n" + "=" * 80)
        print("DIAGNOSTIC COMPLETE")
        print("=" * 80)

        return 0
    except Exception as e:
        print(f"\nError in diagnostic: {str(e)}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
