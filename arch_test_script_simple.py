# C:\project-kortana\arch_test_script_simple.py
import os
import sys

# Write output to a file in the workspace root
try:
    output_file_path = r"C:\project-kortana\simple_test_output.txt"
    with open(output_file_path, "w") as f:
        f.write("This is a simple test to check if file writing works.\n")
        f.write(f"Python executable: {sys.executable}\n")
        f.write(f"Current working directory: {os.getcwd()}\n")
    print(f"File written successfully to {output_file_path}")
except Exception as e:
    print(f"Error writing file: {e}")
