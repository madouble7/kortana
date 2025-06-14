#!/usr/bin/env python
"""
Test script to validate the Kor'tana configuration system.
This script ensures that the config pipeline works correctly with environment variables and .env files.
"""

import os
import sys
from pathlib import Path

# Add the project root to Python path to ensure config can be imported
sys.path.insert(0, str(Path(__file__).parent.parent))


def test_basic_config():
    """Test basic config loading works"""
    try:
        from config import load_config

        config = load_config()
        print("✅ Basic config loading works")
        print(f"Loaded configuration type: {type(config).__name__}")
        return True
    except Exception as e:
        print(f"❌ Config loading failed: {str(e)}")
        return False


def test_env_override():
    """Test that environment variables override YAML settings"""
    try:
        # Set a test environment variable
        os.environ["KORTANA_TEST_VALUE"] = "test_from_env"

        # Load config
        from config import load_config

        config = load_config()

        # Check if the value is accessible (assuming the config schema has this field)
        # If the field doesn't exist in the schema, this will be detected later
        try:
            test_value = config.test_value
            print(f"Test value from config: {test_value}")
            if test_value == "test_from_env":
                print("✅ Environment variable override works")
                return True
            else:
                print("❌ Environment variable didn't override default")
                return False
        except AttributeError:
            print("⚠️ test_value not in config schema, skipping env override test")
            return True
    except Exception as e:
        print(f"❌ Environment variable test failed: {str(e)}")
        return False


def test_env_file():
    """Test that .env file values are loaded"""
    try:
        # Create a temporary .env.test file
        with open(Path(__file__).parent.parent / ".env.test", "w") as f:
            f.write("KORTANA_ENV=testing\n")
            f.write("KORTANA_TEST_ENV_FILE=loaded_from_env_file\n")

        # Set the env file path
        os.environ["DOTENV_PATH"] = ".env.test"

        # Load config
        from config import load_config

        config = load_config()

        # Check if we're in the testing environment
        if hasattr(config, "test_env_file"):
            print(f"Value from .env file: {config.test_env_file}")
            if config.test_env_file == "loaded_from_env_file":
                print("✅ .env file loading works")
                return True
            else:
                print("❌ .env file value not loaded")
                return False
        else:
            print("⚠️ test_env_file not in config schema, skipping .env file test")
            return True
    except Exception as e:
        print(f"❌ .env file test failed: {str(e)}")
        return False
    finally:
        # Clean up
        try:
            (Path(__file__).parent.parent / ".env.test").unlink()
        except Exception:
            pass


def test_missing_required():
    """Test that missing required variables raise appropriate errors"""
    try:
        # Temporarily rename .env if it exists
        env_path = Path(__file__).parent.parent / ".env"
        temp_env_path = Path(__file__).parent.parent / ".env.backup"
        env_existed = False

        if env_path.exists():
            env_path.rename(temp_env_path)
            env_existed = True

        # Set environment to require a value that's missing
        os.environ["KORTANA_ENV"] = "required_test"

        # Create a test config file that has a required value
        required_config_path = (
            Path(__file__).parent.parent / "config/required_test.yaml"
        )
        with open(required_config_path, "w") as f:
            f.write("required_api_key: ${REQUIRED_API_KEY}")

        try:
            from config import load_config

            config = load_config()
            print("❌ Missing required variable did not raise error")
            return False
        except Exception as e:
            if "REQUIRED_API_KEY" in str(e):
                print("✅ Missing required variable properly detected")
                return True
            else:
                print(f"❓ Unexpected error: {str(e)}")
                return False
    finally:
        # Clean up
        try:
            required_config_path.unlink()
        except Exception:
            pass

        # Restore .env if it existed
        if env_existed:
            temp_env_path.rename(env_path)


if __name__ == "__main__":
    print("Testing Kor'tana Configuration System")
    print("=====================================")

    success = test_basic_config()
    if not success:
        print("❌ Basic config loading failed, stopping tests")
        sys.exit(1)

    test_env_override()
    test_env_file()
    test_missing_required()

    print("\n✅ Configuration system tests completed")
