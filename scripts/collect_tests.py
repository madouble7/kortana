"""
Script to collect (but not run) pytest tests and save the collection report.
"""

import os
import subprocess


def main():
    """Run pytest collection and save the output."""
    print(f"Current directory: {os.getcwd()}")
    print("Collecting pytest tests...")

    # Set up environment variables
    env = os.environ.copy()
    env["PYTHONPATH"] = f"{os.getcwd()};{os.path.join(os.getcwd(), 'src')}"

    # Path to Python interpreter in venv311
    python_exe = os.path.join(os.getcwd(), "venv311", "Scripts", "python.exe")

    # Command to collect tests only
    command = [python_exe, "-m", "pytest", "--collect-only", "-v", "tests/unit/"]

    # Run the command
    try:
        print(f"Running command: {' '.join(command)}")
        process = subprocess.run(command, capture_output=True, text=True, env=env)

        # Get the output
        stdout = process.stdout
        stderr = process.stderr
        returncode = process.returncode

        # Save to file
        output_file = "pytest_collection.txt"
        with open(output_file, "w") as f:
            f.write("===== PYTEST COLLECTION STDOUT =====\n\n")
            f.write(stdout)
            f.write("\n\n===== PYTEST COLLECTION STDERR =====\n\n")
            f.write(stderr)
            f.write(f"\n\nExit code: {returncode}")

        # Print summary
        print(f"Pytest collection completed with exit code: {returncode}")
        print(f"Output saved to: {output_file}")

        # If there's output, show a sample
        if stdout:
            print("\nSample of stdout (first 5 lines):")
            for i, line in enumerate(stdout.splitlines()[:5]):
                print(f"{i + 1}: {line}")

    except Exception as e:
        print(f"Error running pytest collection: {e}")
        with open("pytest_collection_error.txt", "w") as f:
            f.write(f"Error running pytest collection: {e}")


if __name__ == "__main__":
    main()
    main()
