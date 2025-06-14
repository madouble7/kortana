#!/usr/bin/env python
"""
Environment Check

A minimal script to verify the current environment before proceeding with refactoring.
This will help ensure we have the correct information about paths and imports.
"""

import importlib
import os
import sys
from pathlib import Path


def check_import(module_name):
    """Try to import a module and return success status."""
    try:
        module = importlib.import_module(module_name)
        print(f"✓ Successfully imported {module_name}")
        print(f"  Module location: {module.__file__}")
        return True, module
    except ImportError as e:
        print(f"✗ Failed to import {module_name}: {e}")
        return False, None
    except Exception as e:
        print(f"✗ Unexpected error importing {module_name}: {e}")
        return False, None


def check_file_exists(file_path):
    """Check if a file exists."""
    path = Path(file_path)
    if path.exists():
        print(f"✓ File exists: {path.absolute()}")
        print(f"  Size: {path.stat().st_size} bytes")
        return True
    else:
        print(f"✗ File not found: {path.absolute()}")
        return False


def main():
    print("\n=== Environment Check ===\n")

    # Print Python and path info
    print(f"Python: {sys.version}")
    print(f"Executable: {sys.executable}")
    print(f"Current directory: {os.getcwd()}")
    print(f"sys.path[0]: {sys.path[0]}")

    print("\n=== Checking Critical Imports ===\n")

    # Check critical imports
    modules_to_check = [
        "config",
        "src.kortana.core.brain",
        "src.llm_clients.factory",
        "src.model_router",
        "src.kortana.memory.memory_manager",
        "src.kortana.memory.memory",
        "src.kortana.core.covenant_enforcer",
        "src.kortana.agents.autonomous_agents",
    ]

    for module in modules_to_check:
        check_import(module)

    print("\n=== Checking Critical Files ===\n")

    # Check critical files
    files_to_check = [
        "config/__init__.py",
        "config/schema.py",
        "config/default.yaml",
        "src/kortana/core/brain.py",
        "src/llm_clients/factory.py",
        "src/model_router.py",
        "src/kortana/memory/memory_manager.py",
        "src/kortana/memory/memory.py",
        "src/kortana/core/covenant_enforcer.py",
        "src/kortana/agents/autonomous_agents.py",
    ]

    for file in files_to_check:
        check_file_exists(file)

    # Try to load config
    print("\n=== Testing Config Loading ===\n")
    try:
        from config import load_config

        print("Attempting to load configuration...")
        cfg = load_config()
        print("✓ Configuration loaded successfully!")

        # Check for paths in config
        if hasattr(cfg, "paths"):
            print("✓ Found paths configuration")
            paths = cfg.paths if hasattr(cfg, "paths") else {}
            for key, value in (
                paths.__dict__.items() if hasattr(paths, "__dict__") else {}
            ):
                print(f"  - {key}: {value}")
    except Exception as e:
        print(f"✗ Error loading configuration: {e}")

    print("\n=== Environment Check Complete ===\n")


if __name__ == "__main__":
    main()
