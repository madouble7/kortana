"""
Simple script to verify that our test files exist.
"""

import os
import sys


def print_with_border(message):
    """Print a message with a border for visibility."""
    border = "=" * 80
    print(border)
    print(message)
    print(border)


# Current directory
current_dir = os.getcwd()
print_with_border(f"Current directory: {current_dir}")

# List of test files we expect to have created
expected_files = [
    os.path.join("tests", "unit", "core", "test_brain.py"),
    os.path.join("tests", "unit", "memory", "test_memory_manager.py"),
    os.path.join("tests", "unit", "core", "__init__.py"),
    os.path.join("tests", "unit", "memory", "__init__.py"),
]

# Check each file
all_exist = True
for file_path in expected_files:
    full_path = os.path.join(current_dir, file_path)
    if os.path.exists(full_path):
        print(f"✅ File exists: {file_path}")
    else:
        print(f"❌ File NOT found: {file_path}")
        all_exist = False

# Summary
if all_exist:
    print_with_border("SUCCESS: All expected test files were found!")
else:
    print_with_border("ERROR: Some test files are missing!")

print("\nAttempting to run basic pytest collection...")

# Try running pytest directly
try:
    # Add the src directory to Python path
    sys.path.insert(0, os.path.join(current_dir, "src"))

    # Try importing pytest
    import pytest

    print("✅ Successfully imported pytest")

    # Call pytest directly to collect tests
    print("\nRunning pytest collection:")
    result = pytest.main(["--collect-only", "-v", os.path.join(current_dir, "tests")])
    print(f"\nPytest collection result code: {result}")

except ImportError:
    print("❌ Failed to import pytest - make sure it's installed")
except Exception as e:
    print(f"❌ Error running pytest: {e}")

print("\nTest verification completed.")
print("\nTest verification completed.")
