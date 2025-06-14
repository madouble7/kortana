"""
Script to run pytest and save the output to a file.
"""

import os
import subprocess

# Output file path
output_file = os.path.join(os.getcwd(), "pytest_output_file.txt")

print(f"Running pytest and saving output to: {output_file}")

try:
    # Ensure the PYTHONPATH includes src directory
    env = os.environ.copy()
    env["PYTHONPATH"] = f"{os.getcwd()};{os.path.join(os.getcwd(), 'src')}"

    # Use the venv311 Python interpreter to run pytest
    python_exe = os.path.join(os.getcwd(), "venv311", "Scripts", "python.exe")

    # Command to run pytest
    command = [python_exe, "-m", "pytest", "tests/unit/", "-v"]

    # Run pytest and capture output
    result = subprocess.run(
        command, capture_output=True, text=True, env=env, check=False
    )

    # Write the output to the file
    with open(output_file, "w") as f:
        f.write("===== PYTEST STDOUT =====\n\n")
        f.write(result.stdout)
        f.write("\n\n===== PYTEST STDERR =====\n\n")
        f.write(result.stderr)
        f.write(f"\n\nExit code: {result.returncode}")

    print(f"Pytest output saved to: {output_file}")
    print(f"File size: {os.path.getsize(output_file)} bytes")
    print(f"Last modified: {os.path.getmtime(output_file)}")

except Exception as e:
    print(f"Error: {e}")
    with open(output_file, "w") as f:
        f.write(f"Error occurred while running pytest: {e}")
