# C:\project-kortana\arch_test_script.py
import os
import sys

output_lines = []
output_lines.append("--- arch_test_script.py execution start ---")
output_lines.append(f"Python Executable Used by This Script: {sys.executable}")
output_lines.append(f"Python Version Used by This Script: {sys.version.split()[0]}")
output_lines.append(f"Script's Current Working Directory: {os.getcwd()}")
output_lines.append("sys.path contents for this script's execution:")
for i, pth in enumerate(sys.path):
    output_lines.append(f"  [{i}] {pth}")
output_lines.append("--- arch_test_script.py execution end ---")

output_file_path = r"C:\project-kortana\arch_test_script_output.txt"

try:
    # Ensure a clean slate for the output file
    if os.path.exists(output_file_path):
        os.remove(output_file_path)

    with open(output_file_path, "w", encoding="utf-8") as f:
        for line in output_lines:
            f.write(line + "\n")
    # This message below will go to standard output when the script is run
    print(
        f"ARCH_TEST_SCRIPT_MSG: Successfully wrote diagnostic output to {output_file_path}"
    )
except Exception as e:
    # This message below will go to standard output (or standard error) if an exception occurs
    print(f"ARCH_TEST_SCRIPT_ERROR: Failed to write to {output_file_path}. Error: {e}")
