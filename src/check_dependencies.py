"""
Check Dependencies

This script checks for required dependencies and files for the Kor'tana system.
"""

import importlib
import os
from pathlib import Path

# Get the project root directory
PROJECT_ROOT = Path(__file__).parent.parent


def check_import(module_name):
    """Try to import a module and return success status."""
    try:
        module = importlib.import_module(module_name)
        print(f"✓ Successfully imported {module_name}")
        if hasattr(module, "__file__"):
            print(f"  Module location: {module.__file__}")
        return True
    except ImportError as e:
        print(f"✗ Failed to import {module_name}: {e}")
        return False
    except Exception as e:
        print(f"✗ Unexpected error importing {module_name}: {e}")
        return False


def check_file_exists(file_path):
    """Check if a file exists."""
    path = Path(file_path)
    if path.exists():
        print(f"✓ File exists: {path.absolute()}")
        return True
    else:
        print(f"✗ File not found: {path.absolute()}")
        return False


def main():
    """Check for dependencies and files."""
    print("\n=== Checking Required Dependencies ===\n")

    # Required imports
    required_imports = [
        "yaml",
        "apscheduler",
        "config",
        "config.schema",
        "src.dev_agent_stub",
        "src.kortana.agents.autonomous_agents",
        "src.kortana.core.covenant_enforcer",
        "src.kortana.memory.memory",
        "src.kortana.memory.memory_manager",
        "src.kortana.utils",
        "src.llm_clients.factory",
        "src.model_router",
        "src.sacred_trinity_router",
    ]

    import_results = {module: check_import(module) for module in required_imports}

    print("\n=== Checking Required Files ===\n")

    # Change to project root directory
    os.chdir(PROJECT_ROOT)
    print(f"Working in directory: {os.getcwd()}")

    # Required files
    required_files = [
        "config/persona.json",
        "config/identity.json",
        "config/models_config.json",
        "config/sacred_trinity_config.json",
        "config/covenant.yaml",
        "config/default.yaml",
    ]

    file_results = {file: check_file_exists(file) for file in required_files}

    # Summary
    print("\n=== Dependency Check Summary ===\n")

    print("Imports:")
    for module, result in import_results.items():
        print(f"  {'✓' if result else '✗'} {module}")

    print("\nFiles:")
    for file, result in file_results.items():
        print(f"  {'✓' if result else '✗'} {file}")

    # Overall result
    all_imports_ok = all(import_results.values())
    all_files_ok = all(file_results.values())

    if all_imports_ok and all_files_ok:
        print("\n✅ All dependencies and files are available.")
    else:
        print("\n❌ Some dependencies or files are missing. See above for details.")

        # Suggestions for fixing issues
        if not all_imports_ok:
            print("\nTo install missing packages:")
            print("pip install pyyaml apscheduler")

        if not all_files_ok:
            print("\nTo create missing files:")
            print("python src/setup_directories.py")


if __name__ == "__main__":
    main()
