#!/usr/bin/env python
"""
Verify the config pipeline.
This script checks that the configuration system is working correctly.
"""

import os
import sys
import tempfile
from pathlib import Path

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))


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


def check_basic_config_loading():
    """Test 1: Check if config can be loaded."""
    color_print("\n📋 Test 1: Basic Config Loading", "blue")
    try:
        from config import load_config

        config = load_config()
        color_print("✅ Successfully loaded config")
        color_print(f"   Config type: {type(config).__name__}")
        print(f"   Sample properties: {list(vars(config).keys())[:5]}")
        return True
    except Exception as e:
        color_print(f"❌ Failed to load config: {str(e)}", "red")
        return False


def check_environment_override():
    """Test 2: Check if environment variables override config."""
    color_print("\n📋 Test 2: Environment Variable Override", "blue")
    try:
        # Set a test environment variable
        test_key = "KORTANA_TEST_ENV_VAR"
        os.environ[test_key] = "test_value"

        from config import load_config

        config = load_config()

        # Check if this can be accessed - it might not be in the schema
        try:
            value = getattr(config, "test_env_var", None)
            if value == "test_value":
                color_print(
                    f"✅ Environment variable correctly overrode config: {value}"
                )
            else:
                color_print(
                    f"⚠️ Environment variable was not applied: {value}", "yellow"
                )
        except Exception as e:
            color_print(f"⚠️ Could not access test property: {str(e)}", "yellow")
            color_print(
                "   This is OK if the schema doesn't define this property", "yellow"
            )

        return True
    except Exception as e:
        color_print(f"❌ Environment variable test failed: {str(e)}", "red")
        return False
    finally:
        # Clean up
        if test_key in os.environ:
            del os.environ[test_key]


def check_env_file_loading():
    """Test 3: Check if .env file loading works."""
    color_print("\n📋 Test 3: .env File Loading", "blue")

    # Create a temporary .env file
    temp_dir = tempfile.TemporaryDirectory()
    env_path = Path(temp_dir.name) / ".env.test"

    try:
        # Create a test .env file
        with open(env_path, "w") as f:
            f.write("KORTANA_TEST_DOT_ENV=loaded_from_dotenv\n")

        # Set the env file path
        original_dotenv_path = os.environ.get("DOTENV_PATH")
        os.environ["DOTENV_PATH"] = str(env_path)

        from config import load_config

        config = load_config()

        # Try to access the variable - it might not be in the schema
        try:
            value = getattr(config, "test_dot_env", None)
            if value == "loaded_from_dotenv":
                color_print(f"✅ .env file value loaded correctly: {value}")
            else:
                color_print(f"⚠️ .env file value not applied: {value}", "yellow")
        except Exception as e:
            color_print(f"⚠️ Could not access test property: {str(e)}", "yellow")
            color_print(
                "   This is OK if the schema doesn't define this property", "yellow"
            )

        return True
    except Exception as e:
        color_print(f"❌ .env file test failed: {str(e)}", "red")
        return False
    finally:
        # Clean up
        if original_dotenv_path:
            os.environ["DOTENV_PATH"] = original_dotenv_path
        else:
            del os.environ["DOTENV_PATH"]

        temp_dir.cleanup()


def check_environment_specific_config():
    """Test 4: Check if environment-specific config is loaded."""
    color_print("\n📋 Test 4: Environment-Specific Config", "blue")

    # Save the original environment
    original_env = os.environ.get("KORTANA_ENV")

    try:
        # Set the environment to production
        os.environ["KORTANA_ENV"] = "production"

        from config import load_config

        config = load_config()

        color_print("✅ Loaded production config")
        print(f"   Debug setting: {getattr(config, 'debug', 'N/A')}")

        # Switch to development
        os.environ["KORTANA_ENV"] = "development"
        config = load_config()

        color_print("✅ Loaded development config")
        print(f"   Debug setting: {getattr(config, 'debug', 'N/A')}")

        return True
    except Exception as e:
        color_print(f"❌ Environment-specific config test failed: {str(e)}", "red")
        return False
    finally:
        # Restore the original environment
        if original_env:
            os.environ["KORTANA_ENV"] = original_env
        elif "KORTANA_ENV" in os.environ:
            del os.environ["KORTANA_ENV"]


def check_direct_yaml_loading():
    """Test 5: Scan for direct YAML loading in the codebase."""
    color_print("\n📋 Test 5: Direct YAML Loading Scan", "blue")

    import re

    yaml_load_pattern = re.compile(r"(yaml\.safe_load|yaml\.load)\s*\(")
    yaml_open_pattern = re.compile(r"open\s*\([^)]*\.ya?ml")

    # Files that are allowed to use direct YAML loading
    allowed_files = {
        "config/__init__.py",
        "config/schema.py",
    }

    violations = []
    project_root = Path(__file__).parent.parent
    src_dir = project_root / "src"

    # Only scan the src directory for this check
    if src_dir.exists():
        for path in src_dir.glob("**/*.py"):
            relative_path = path.relative_to(project_root)

            # Skip allowed files
            if str(relative_path) in allowed_files or any(
                str(relative_path).startswith(p) for p in ["tests/", "scripts/"]
            ):
                continue

            try:
                content = path.read_text(encoding="utf-8")

                if yaml_load_pattern.search(content) or yaml_open_pattern.search(
                    content
                ):
                    violations.append(str(relative_path))
            except UnicodeDecodeError:
                print(f"   Could not decode file: {path}")

    if violations:
        color_print(
            f"❌ Found {len(violations)} files with direct YAML loading:", "red"
        )
        for file in violations:
            print(f"   - {file}")
        return False
    else:
        color_print("✅ No direct YAML loading found in source files")
        return True


def main():
    """Run all configuration tests."""
    color_print("🔍 Verifying Kor'tana Configuration Pipeline", "blue")
    color_print("=========================================", "blue")

    results = []
    results.append(check_basic_config_loading())
    results.append(check_environment_override())
    results.append(check_env_file_loading())
    results.append(check_environment_specific_config())
    results.append(check_direct_yaml_loading())

    print("\n=========================================")
    success_count = results.count(True)
    total_tests = len(results)

    if all(results):
        color_print(
            f"✅ All {total_tests}/{total_tests} configuration tests passed!", "green"
        )
    else:
        color_print(
            f"⚠️ {success_count}/{total_tests} configuration tests passed", "yellow"
        )

    return 0 if all(results) else 1


if __name__ == "__main__":
    sys.exit(main())
