#!/usr/bin/env python
"""
Test script to diagnose issues with activate_kortana.py
"""

import os
import sys
import traceback
from pathlib import Path

# Add the project root to the Python path
sys.path.append(str(Path(__file__).parent))


def test_imports():
    """Test importing the required modules"""

    print("Testing imports...")

    try:
        print("Importing basic libraries...")
        import asyncio
        import json
        import logging
        import random
        import time
        from datetime import datetime
        from typing import Any, Dict, List, Optional, Tuple

        print("✓ Basic libraries imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import basic libraries: {e}")
        traceback.print_exc()
        return False

    try:
        print("\nImporting Kor'tana specific modules...")

        try:
            from kortana.config.schema import KortanaConfig

            print("✓ KortanaConfig imported")
        except ImportError as e:
            print(f"✗ Failed to import KortanaConfig: {e}")
            traceback.print_exc()

        try:
            from kortana.llm_clients.factory import LLMClientFactory

            print("✓ LLMClientFactory imported")
        except ImportError as e:
            print(f"✗ Failed to import LLMClientFactory: {e}")
            traceback.print_exc()

        try:
            from kortana.core.orchestrator import KorOrchestrator

            print("✓ KorOrchestrator imported")
        except ImportError as e:
            print(f"✗ Failed to import KorOrchestrator: {e}")
            traceback.print_exc()

        try:
            from kortana.modules.memory_core.services import MemoryCoreService

            print("✓ MemoryCoreService imported")
        except ImportError as e:
            print(f"✗ Failed to import MemoryCoreService: {e}")
            traceback.print_exc()

        try:
            from kortana.services.database import get_db_sync

            print("✓ get_db_sync imported")
        except ImportError as e:
            print(f"✗ Failed to import get_db_sync: {e}")
            traceback.print_exc()

        print("\nAll import tests complete.")

    except Exception as e:
        print(f"✗ Unexpected error during import tests: {e}")
        traceback.print_exc()
        return False

    return True


def test_config_paths():
    """Test if config paths exist and are accessible"""

    print("\nTesting config paths...")

    config_paths = [
        Path("config/models_config.json"),
        Path("../config/models_config.json"),
        Path(__file__).parent / "config" / "models_config.json",
    ]

    found_config = False
    for config_path in config_paths:
        print(f"Checking {config_path}...")
        if config_path.exists():
            print(f"✓ Config found at {config_path}")
            found_config = True
            try:
                import json

                with open(config_path) as f:
                    config_data = json.load(f)
                print(f"✓ Config loaded successfully, contains {len(config_data)} keys")
            except Exception as e:
                print(f"✗ Error loading config: {e}")
                traceback.print_exc()

    if not found_config:
        print("✗ No config file found at any of the expected paths")

    return found_config


def test_database():
    """Test database connection"""

    print("\nTesting database connection...")

    try:
        from kortana.services.database import get_db_sync

        print("Getting database session...")
        db_session = next(get_db_sync())
        print(f"✓ Database session obtained successfully: {db_session}")
        return True
    except Exception as e:
        print(f"✗ Failed to connect to database: {e}")
        traceback.print_exc()
        return False


def run_tests():
    """Run all tests"""

    print("=" * 50)
    print("ACTIVATE_KORTANA.PY DIAGNOSTIC SCRIPT")
    print("=" * 50)

    print("\nRunning in directory:", os.getcwd())
    print("Python version:", sys.version)
    print("Python executable:", sys.executable)
    print("Python path:", sys.path)

    print("\nRunning diagnostics...\n")

    imports_ok = test_imports()
    config_ok = test_config_paths()
    db_ok = test_database()

    print("\n" + "=" * 50)
    print("DIAGNOSTIC RESULTS")
    print("=" * 50)
    print(f"Imports: {'✓ OK' if imports_ok else '✗ FAIL'}")
    print(f"Config: {'✓ OK' if config_ok else '✗ FAIL'}")
    print(f"Database: {'✓ OK' if db_ok else '✗ FAIL'}")
    print("=" * 50)

    if imports_ok and config_ok and db_ok:
        print("\nAll diagnostics passed! You should be able to run activate_kortana.py")
    else:
        print(
            "\nSome diagnostics failed. Please fix the issues before running activate_kortana.py"
        )


if __name__ == "__main__":
    run_tests()
