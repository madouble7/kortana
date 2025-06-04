"""
Run a test collection and save the output to a file.
"""

import os
import subprocess
import sys

# Add src to path
sys.path.insert(0, os.path.abspath("src"))

# Output file
output_file = "test_collection_output.txt"

# Attempt to run pytest collection
try:
    # Use subprocess to capture the output
    result = subprocess.run(
        [".test_env\\Scripts\\python", "-m", "pytest", "--collect-only", "-v", "tests"],
        capture_output=True,
        text=True,
        check=False,
    )

    # Save output to file
    with open(output_file, "w") as f:
        f.write("=== STDOUT ===\n")
        f.write(result.stdout)
        f.write("\n\n=== STDERR ===\n")
        f.write(result.stderr)
        f.write(f"\n\nExit code: {result.returncode}\n")

    print(f"Test collection output saved to {output_file}")

except Exception as e:
    # Write error to file
    with open(output_file, "w") as f:
        f.write(f"Error running tests: {e}")
    print(f"Error: {e}")
