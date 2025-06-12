#!/usr/bin/env python
"""
Simplified test script to verify that config.load_config() correctly loads covenant.yaml.
This script focuses specifically on:
1. Loading default.yaml correctly
2. Finding and loading covenant.yaml using settings.paths.covenant_file_path
3. Making settings.covenant_rules available with the expected content
4. Resolving its own imports (like yaml and omegaconf)
"""

import importlib
import sys
from pathlib import Path

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))


def print_section(title):
    """Print a section header"""
    print("\n" + "=" * 50)
    print(f" {title} ".center(50, "="))
    print("=" * 50)


def check_dependencies():
    """Check if required dependencies are installed"""
    print_section("Dependency Check")

    dependencies = [("yaml", "PyYAML"), ("omegaconf", "omegaconf")]

    all_passed = True

    for module_name, package_name in dependencies:
        try:
            module = importlib.import_module(module_name)
            print(
                f"✅ {module_name} module is available (version: {getattr(module, '__version__', 'unknown')})"
            )
        except ImportError:
            print(
                f"❌ {module_name} module is NOT available. Install with: pip install {package_name}"
            )
            all_passed = False
        except Exception as e:
            print(f"❌ Error checking {module_name}: {str(e)}")
            all_passed = False

    return all_passed


def test_config_loading():
    """Test that config.load_config() works correctly"""
    print_section("Config Loading Test")

    try:
        print("Importing load_config from config module...")
        from config import load_config

        print("✅ Successfully imported load_config")

        print("\nLoading configuration...")
        settings = load_config()
        print("✅ Successfully loaded configuration")

        # Check basic config properties
        print("\nVerifying basic configuration properties:")
        if hasattr(settings, "app") and hasattr(settings.app, "name"):
            print(f"✅ Basic config loaded: app.name = {settings.app.name}")
        else:
            print("❌ Failed to load basic configuration properties")
            return False

        # Check covenant_rules
        print("\nVerifying covenant_rules:")
        if hasattr(settings, "covenant_rules"):
            if settings.covenant_rules is None:
                print("❌ settings.covenant_rules is None")
                return False
            else:
                print("✅ settings.covenant_rules is available")

                # Check for expected keys in covenant_rules
                expected_keys = [
                    "sacred_principles",
                    "protected_files",
                    "human_approval_required",
                ]
                found_keys = []
                missing_keys = []

                for key in expected_keys:
                    if key in settings.covenant_rules:
                        found_keys.append(key)
                    else:
                        missing_keys.append(key)

                if missing_keys:
                    print(f"❌ Missing expected keys in covenant_rules: {missing_keys}")
                    return False
                else:
                    print(f"✅ All expected keys found in covenant_rules: {found_keys}")

                # Print some covenant_rules content for verification
                print("\nSample covenant_rules content:")
                for key in list(settings.covenant_rules.keys())[:5]:
                    print(f"  - {key}: {type(settings.covenant_rules[key])}")
        else:
            print("❌ settings.covenant_rules is not available")
            return False

        # Check covenant_file_path
        print("\nVerifying covenant_file_path:")
        if hasattr(settings, "paths") and hasattr(settings.paths, "covenant_file_path"):
            covenant_path = settings.paths.covenant_file_path
            print(f"✅ settings.paths.covenant_file_path = {covenant_path}")

            # Check if the file exists
            root_dir = Path(__file__).parent.parent
            full_path = root_dir / covenant_path
            if full_path.exists():
                print(f"✅ Covenant file exists at: {full_path}")
            else:
                print(f"❌ Covenant file NOT found at: {full_path}")
                # Check if it exists in the root directory
                alt_path = root_dir / "covenant.yaml"
                if alt_path.exists():
                    print(f"  But found at alternative location: {alt_path}")
        else:
            print("❌ settings.paths.covenant_file_path is not available")
            return False

        return True
    except Exception as e:
        print(f"❌ Error during config loading test: {str(e)}")
        import traceback

        traceback.print_exc()
        return False


def main():
    """Main function"""
    print_section("Covenant Loading Test")
    print("This script tests if config.load_config() correctly loads covenant.yaml")

    # Check dependencies first
    deps_ok = check_dependencies()
    if not deps_ok:
        print("\n⚠️ Some dependencies are missing. Tests may fail.")

    # Test config loading
    config_ok = test_config_loading()

    # Print summary
    print_section("Test Summary")
    if deps_ok and config_ok:
        print("✅ All tests PASSED!")
        print("The config system is correctly loading covenant.yaml")
        return 0
    else:
        print("❌ Some tests FAILED!")
        if not deps_ok:
            print("- Missing dependencies need to be installed")
        if not config_ok:
            print("- Configuration loading has issues")
        return 1


if __name__ == "__main__":
    sys.exit(main())
