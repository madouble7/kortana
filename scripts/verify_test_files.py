"""
Verify test file creation and contents.
"""

import os


def check_file_exists_and_print(file_path):
    """Check if a file exists and print its contents if it does."""
    print(f"Checking file: {file_path}")
    if os.path.exists(file_path):
        print(f"✅ File exists: {file_path}")
        try:
            with open(file_path) as f:
                content = f.read()
            print(f"File content (first 300 chars):\n{content[:300]}...")
            print(f"File size: {len(content)} bytes")
            return True
        except Exception as e:
            print(f"❌ Error reading file: {e}")
            return False
    else:
        print(f"❌ File does not exist: {file_path}")
        return False


def check_test_files():
    """Check the test files we've created."""
    base_dir = os.getcwd()
    print(f"Current working directory: {base_dir}")

    # Define test files to check
    test_files = [
        os.path.join(base_dir, "tests", "unit", "core", "test_brain.py"),
        os.path.join(base_dir, "tests", "unit", "memory", "test_memory_manager.py"),
        os.path.join(base_dir, "tests", "unit", "core", "__init__.py"),
        os.path.join(base_dir, "tests", "unit", "memory", "__init__.py"),
    ]

    # Check each file
    for file_path in test_files:
        check_file_exists_and_print(file_path)

    # Check if the directories exist
    dirs_to_check = [
        os.path.join(base_dir, "tests"),
        os.path.join(base_dir, "tests", "unit"),
        os.path.join(base_dir, "tests", "unit", "core"),
        os.path.join(base_dir, "tests", "unit", "memory"),
    ]

    for dir_path in dirs_to_check:
        if os.path.isdir(dir_path):
            print(f"✅ Directory exists: {dir_path}")
            try:
                contents = os.listdir(dir_path)
                print(f"   Contents: {contents}")
            except Exception as e:
                print(f"❌ Error listing directory: {e}")
        else:
            print(f"❌ Directory does not exist: {dir_path}")


if __name__ == "__main__":
    check_test_files()
    check_test_files()
