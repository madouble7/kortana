#!/usr/bin/env python
"""
Test script to verify covenant_enforcer.py and covenant.py integration with the config system.
This script ensures that:
1. Both files are free of syntax errors
2. The methods utilizing settings.covenant_rules are logically sound
3. config.load_config() correctly loads covenant.yaml
"""

import importlib
import logging
import sys
from pathlib import Path

# Add the project root to Python path to ensure imports work correctly
sys.path.insert(0, str(Path(__file__).parent.parent))

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def color_print(message, color="green"):
    """Print colored messages to the console."""
    colors = {
        "reset": "\033[0m",
        "green": "\033[92m",
        "yellow": "\033[93m",
        "red": "\033[91m",
        "blue": "\033[94m",
    }
    print(f"{colors.get(color, '')}{message}{colors['reset']}")


def test_syntax_errors():
    """Test 1: Check for syntax errors in covenant_enforcer.py and covenant.py"""
    color_print("\n📋 Test 1: Syntax Error Check", "blue")

    files_to_check = ["kortana.core.covenant_enforcer", "kortana.core.covenant"]

    all_passed = True

    for module_name in files_to_check:
        try:
            # Try to import the module
            module = importlib.import_module(module_name)
            color_print(f"✅ {module_name} imports successfully with no syntax errors")
        except SyntaxError as e:
            color_print(f"❌ Syntax error in {module_name}: {str(e)}", "red")
            all_passed = False
        except ImportError as e:
            color_print(f"❌ Import error for {module_name}: {str(e)}", "red")
            all_passed = False
        except Exception as e:
            color_print(f"❌ Unexpected error importing {module_name}: {str(e)}", "red")
            all_passed = False

    return all_passed


def test_config_loading():
    """Test 2: Verify config.load_config() loads default.yaml and covenant.yaml correctly"""
    color_print("\n📋 Test 2: Config Loading Test", "blue")

    try:
        from config import load_config

        # Load the configuration
        settings = load_config()

        # Check if default.yaml was loaded
        if not hasattr(settings, "app") or not hasattr(settings.app, "name"):
            color_print(
                "❌ Failed to load basic configuration from default.yaml", "red"
            )
            return False

        color_print(
            f"✅ Successfully loaded default.yaml (app.name: {settings.app.name})"
        )

        # Check if covenant_rules were loaded
        if not hasattr(settings, "covenant_rules") or settings.covenant_rules is None:
            color_print("❌ settings.covenant_rules is missing or None", "red")
            return False

        # Check if covenant.yaml content is loaded into covenant_rules
        covenant_rules = settings.covenant_rules
        required_keys = [
            "sacred_principles",
            "protected_files",
            "human_approval_required",
        ]

        missing_keys = [key for key in required_keys if key not in covenant_rules]
        if missing_keys:
            color_print(
                f"❌ covenant_rules is missing expected keys: {missing_keys}", "red"
            )
            return False

        color_print("✅ Successfully loaded covenant.yaml into settings.covenant_rules")
        print(f"   Found keys: {list(covenant_rules.keys())[:5]}...")

        # Check covenant_file_path
        if not hasattr(settings, "paths") or not hasattr(
            settings.paths, "covenant_file_path"
        ):
            color_print("❌ settings.paths.covenant_file_path is missing", "red")
            return False

        covenant_path = settings.paths.covenant_file_path
        color_print(f"✅ settings.paths.covenant_file_path is set to: {covenant_path}")

        return True
    except Exception as e:
        color_print(f"❌ Config loading test failed: {str(e)}", "red")
        return False


def test_covenant_enforcer_integration():
    """Test 3: Verify CovenantEnforcer correctly uses settings.covenant_rules"""
    color_print("\n📋 Test 3: CovenantEnforcer Integration Test", "blue")

    try:
        # Import the CovenantEnforcer class from covenant_enforcer.py
        from kortana.core.covenant_enforcer import CovenantEnforcer

        # Create an instance of CovenantEnforcer
        enforcer = CovenantEnforcer()

        # Check if covenant rules were loaded
        if not hasattr(enforcer, "covenant") or not enforcer.covenant:
            color_print("❌ CovenantEnforcer failed to load covenant rules", "red")
            return False

        color_print("✅ CovenantEnforcer successfully loaded covenant rules")

        # Test a method that uses covenant rules
        test_response = "This is a test response that should not violate any rules."
        result = enforcer.check_output(test_response)

        color_print(f"✅ enforcer.check_output() executed successfully: {result}")

        # Check if the covenant_path was correctly set
        if not hasattr(enforcer, "covenant_path") or not enforcer.covenant_path:
            color_print("⚠️ CovenantEnforcer.covenant_path is not set", "yellow")
        else:
            color_print(
                f"✅ CovenantEnforcer.covenant_path is set to: {enforcer.covenant_path}"
            )

        return True
    except Exception as e:
        color_print(f"❌ CovenantEnforcer integration test failed: {str(e)}", "red")
        return False


def test_covenant_class_integration():
    """Test 4: Verify the CovenantEnforcer class in covenant.py correctly uses settings.covenant_rules"""
    color_print("\n📋 Test 4: covenant.py CovenantEnforcer Integration Test", "blue")

    try:
        # Import the CovenantEnforcer class from covenant.py
        from kortana.core.covenant import CovenantEnforcer as CovenantEnforcerAlt

        # Create an instance of CovenantEnforcer
        enforcer = CovenantEnforcerAlt()

        # Check if covenant rules were loaded
        if not hasattr(enforcer, "rules") or not enforcer.rules:
            color_print(
                "❌ covenant.py CovenantEnforcer failed to load covenant rules", "red"
            )
            return False

        color_print(
            "✅ covenant.py CovenantEnforcer successfully loaded covenant rules"
        )

        # Test a method that uses covenant rules
        test_response = "This is a test response that should not violate any rules."
        result = enforcer.check_output(test_response)

        color_print(
            f"✅ covenant.py enforcer.check_output() executed successfully: {result}"
        )

        return True
    except Exception as e:
        color_print(
            f"❌ covenant.py CovenantEnforcer integration test failed: {str(e)}", "red"
        )
        return False


def test_dependency_resolution():
    """Test 5: Verify that required dependencies (yaml, omegaconf) are available"""
    color_print("\n📋 Test 5: Dependency Resolution Test", "blue")

    dependencies = [("yaml", "PyYAML"), ("omegaconf", "omegaconf")]

    all_passed = True

    for module_name, package_name in dependencies:
        try:
            module = importlib.import_module(module_name)
            color_print(f"✅ Successfully imported {module_name} module")
        except ImportError:
            color_print(
                f"❌ Failed to import {module_name}. Make sure {package_name} is installed.",
                "red",
            )
            all_passed = False
        except Exception as e:
            color_print(f"❌ Unexpected error importing {module_name}: {str(e)}", "red")
            all_passed = False

    return all_passed


def main():
    """Run all tests"""
    color_print("🔍 Verifying Covenant Configuration Integration", "blue")
    color_print("=========================================", "blue")

    results = []
    results.append(test_syntax_errors())
    results.append(test_config_loading())
    results.append(test_covenant_enforcer_integration())
    results.append(test_covenant_class_integration())
    results.append(test_dependency_resolution())

    print("\n=========================================")
    success_count = results.count(True)
    total_tests = len(results)

    if all(results):
        color_print(f"✅ All {total_tests}/{total_tests} tests passed!", "green")
    else:
        color_print(f"⚠️ {success_count}/{total_tests} tests passed", "yellow")

    return 0 if all(results) else 1


if __name__ == "__main__":
    sys.exit(main())
