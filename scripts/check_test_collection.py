"""
Simple script to run pytest collection on our test stubs.
"""

import os
import subprocess
import sys


def main():
    """Main function to run pytest collection."""
    print("Running pytest collection on test stubs...")

    # Path to test directory
    test_path = os.path.join(os.getcwd(), "tests", "unit")
    print(f"Test path: {test_path}")

    # Use current Python interpreter
    python_exe = sys.executable
    print(f"Using Python interpreter: {python_exe}")

    # Set environment variable for imports
    env = os.environ.copy()
    env["PYTHONPATH"] = f"{os.getcwd()};{os.path.join(os.getcwd(), 'src')}"
    print(f"PYTHONPATH: {env['PYTHONPATH']}")

    # Command to run pytest collect only
    cmd = [python_exe, "-m", "pytest", "--collect-only", "-v", test_path]
    print(f"Command: {' '.join(cmd)}")

    try:
        # Run the command
        print("\nRunning pytest collection...")
        proc = subprocess.run(cmd, capture_output=True, text=True, env=env)

        # Print output
        print("\nSTDOUT:")
        print(proc.stdout)

        print("\nSTDERR:")
        print(proc.stderr)

        print(f"\nExit code: {proc.returncode}")

        # Create a file with the output
        with open("simple_test_collection.log", "w") as f:
            f.write("===== STDOUT =====\n")
            f.write(proc.stdout)
            f.write("\n\n===== STDERR =====\n")
            f.write(proc.stderr)
            f.write(f"\n\nExit code: {proc.returncode}")

        print("\nOutput saved to simple_test_collection.log")

    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()
    main()
