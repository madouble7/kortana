"""
Test script to verify that the covenant_rules are correctly loaded from covenant.yaml
through the centralized configuration system in config.load_config()
"""

import os
import sys
from pathlib import Path

import yaml

# Add the parent directory to Python path to make imports work
current_dir = Path(__file__).parent
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

try:
    from config import load_config

    def test_covenant_loading():
        """Test that covenant.yaml is loaded into settings.covenant_rules"""
        print("Testing configuration loading with covenant.yaml...")

        try:
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
                    sacred_principles = settings.covenant_rules.get(
                        "sacred_principles", {}
                    )
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
                        covenant_abs_path = (
                            Path(settings.paths.config_dir) / covenant_file
                        )
                        print(f"Relative path resolved to: {covenant_abs_path}")
                    else:
                        print(f"Using absolute path: {covenant_file}")

                    return True
                else:
                    print("\n❌ ERROR: settings.covenant_rules exists but is empty!")
                    return False
            else:
                print("\n❌ ERROR: settings object has no 'covenant_rules' attribute!")
                return False

        except Exception as e:
            print(f"\n❌ ERROR: Exception while loading config: {str(e)}")
            import traceback

            traceback.print_exc()
            return False

    def read_covenant_directly():
        """Read covenant.yaml directly to verify it exists and can be loaded"""
        print("\n--- Checking covenant.yaml directly ---")

        # Try root directory
        root_covenant = Path("covenant.yaml")
        if root_covenant.exists():
            print(f"covenant.yaml found in root directory: {root_covenant.absolute()}")
            try:
                with open(root_covenant, "r") as f:
                    covenant_data = yaml.safe_load(f) or {}
                print(
                    f"Successfully loaded covenant.yaml from root, version: {covenant_data.get('covenant_version', 'Not found')}"
                )
            except Exception as e:
                print(f"Error loading root covenant.yaml: {str(e)}")
        else:
            print("covenant.yaml NOT found in root directory")

        # Try config directory
        config_covenant = Path("config") / "covenant.yaml"
        if config_covenant.exists():
            print(
                f"covenant.yaml found in config directory: {config_covenant.absolute()}"
            )
            try:
                with open(config_covenant, "r") as f:
                    covenant_data = yaml.safe_load(f) or {}
                print(
                    f"Successfully loaded covenant.yaml from config dir, version: {covenant_data.get('covenant_version', 'Not found')}"
                )
            except Exception as e:
                print(f"Error loading config dir covenant.yaml: {str(e)}")
        else:
            print("covenant.yaml NOT found in config directory")

    def debug_config_loading():
        """Print more detailed information about the config loading process"""
        print("\n--- Debug Configuration Loading ---")

        # Check for .env file
        env_path = Path(".env")
        print(f".env file exists: {env_path.exists()}")

        # Print current working directory
        print(f"Current working directory: {os.getcwd()}")

        # Check for covenant.yaml file
        covenant_path = Path("covenant.yaml")
        print(f"covenant.yaml exists in root dir: {covenant_path.exists()}")
        if covenant_path.exists():
            print(f"covenant.yaml absolute path: {covenant_path.absolute()}")

        # Check for covenant.yaml file in config dir
        config_covenant_path = Path("config") / "covenant.yaml"
        print(f"covenant.yaml exists in config dir: {config_covenant_path.exists()}")
        if config_covenant_path.exists():
            print(
                f"config/covenant.yaml absolute path: {config_covenant_path.absolute()}"
            )

        # Print environment variables
        print("\nRelevant environment variables:")
        for var in [
            "KORTANA_ENV",
            "KORTANA_CONFIG_DIR",
            "KORTANA_PATHS__COVENANT_FILE_PATH",
        ]:
            print(f"  {var}: {os.environ.get(var, 'Not set')}")

        # Check paths in schema
        try:
            from config.schema import PathsConfig

            paths = PathsConfig()
            print(f"\nDefault covenant_file_path in schema: {paths.covenant_file_path}")
        except Exception as e:
            print(f"Error checking schema: {str(e)}")

except ImportError as e:
    print(f"Error importing from config module: {str(e)}")
    import traceback

    traceback.print_exc()

if __name__ == "__main__":
    print("\n=== Kortana Configuration Test ===")
    print("Testing if covenant.yaml is correctly loaded into settings.covenant_rules")

    # Try to read covenant.yaml directly first
    read_covenant_directly()

    # Run debug diagnostics
    debug_config_loading()

    # Test actual config loading
    success = test_covenant_loading()

    if not success:
        print("\nExiting with error status")
        sys.exit(1)
    else:
        print("\nConfiguration test passed successfully!")
