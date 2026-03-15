"""
Test script to verify that the covenant_rules are correctly loaded from covenant.yaml
through the centralized configuration system in config.load_config()
"""

import os
import sys
from pathlib import Path

# Add the parent directory to Python path to make imports work
# This should be done before other project imports if test_config_loading.py is run as a script
current_dir = Path(__file__).resolve().parent  # Use resolve() for a canonical path
project_root = current_dir  # Assuming this test file is in the project root
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Now import from the config module (assuming it's in the project root or src)
from src.kortana.config import load_config


def test_covenant_loading():
    """Test that covenant.yaml is loaded into settings.covenant_rules"""
    print("Testing configuration loading with covenant.yaml...")
    settings = load_config()

    print(f"\nConfiguration loaded for environment: {settings.app.environment}")
    print(f"Project name: {settings.app.name}")

    # Check if covenant_rules exists and has content
    if hasattr(settings, "covenant_rules"):
        if settings.covenant_rules:
            print("\n✅ SUCCESS: settings.covenant_rules is populated!")
            print(
                f"Covenant version: {settings.covenant_rules.get('covenant_version', 'Not found')}"
            )

            # Print some sample covenant rules to verify content
            sacred_principles = settings.covenant_rules.get("sacred_principles", {})
            if sacred_principles:
                print("\nSacred Principles:")
                for key, value in sacred_principles.items():
                    print(f"  - {key}: {value}")

            protected_files = settings.covenant_rules.get("protected_files", [])
            if protected_files:
                print("\nSome protected files:")
                for file in protected_files[:3]:  # Show up to 3 protected files
                    print(f"  - {file}")
                if len(protected_files) > 3:
                    print(f"  - ... and {len(protected_files) - 3} more")

            # Verify the path used to load covenant
            print(
                f"\nCovenant file path from settings: {settings.paths.covenant_file_path}"
            )

            covenant_file = Path(settings.paths.covenant_file_path)
            if not covenant_file.is_absolute():
                # If relative path, it should be relative to the config directory
                covenant_abs_path = Path(settings.paths.config_dir) / covenant_file
                print(f"Absolute path used for loading: {covenant_abs_path}")
            else:
                print(f"Absolute path used for loading: {covenant_file}")

            return True
        else:
            print("\n❌ ERROR: settings.covenant_rules exists but is empty!")
            return False
    else:
        print("\n❌ ERROR: settings object has no 'covenant_rules' attribute!")
        return False


def debug_config_loading():
    """Print more detailed information about the config loading process"""
    print("\n--- Debug Configuration Loading ---")

    # Check for .env file
    env_path = Path(".env")
    print(f".env file exists: {env_path.exists()}")

    # Check for covenant.yaml file
    covenant_path = Path("covenant.yaml")
    print(f"covenant.yaml exists in root dir: {covenant_path.exists()}")

    # Check for covenant.yaml file in config dir
    config_covenant_path = Path("config") / "covenant.yaml"
    print(f"covenant.yaml exists in config dir: {config_covenant_path.exists()}")

    # Print environment variables
    print("\nRelevant environment variables:")
    for var in [
        "KORTANA_ENV",
        "KORTANA_CONFIG_DIR",
        "KORTANA_PATHS__COVENANT_FILE_PATH",
    ]:
        print(f"  {var}: {os.environ.get(var, 'Not set')}")


if __name__ == "__main__":
    success = test_covenant_loading()

    if not success:
        print("\nRunning debug diagnostics...")
        debug_config_loading()
        print("\nExiting with error status")
        sys.exit(1)
