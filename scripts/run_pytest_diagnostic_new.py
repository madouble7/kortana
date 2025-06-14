# C:\project-kortana\run_pytest_diagnostic_new.py
import os
import subprocess
import sys

# Setup logging to file
log_file = open("pytest_diagnostic_output.txt", "w")


def log(message):
    print(message)
    log_file.write(message + "\n")
    log_file.flush()


log(f"--- Starting pytest diagnostic run from: {os.getcwd()} ---")
log(f"Python executable running this script: {sys.executable}")

# Define paths carefully
project_root = r"C:\project-kortana"  # Ensure this is correct
venv_scripts_path = os.path.join(project_root, "venv311", "Scripts")
# Try to find pytest within the venv first, then fall back to just 'pytest' (if on PATH)
pytest_exe_candidate1 = os.path.join(venv_scripts_path, "pytest.exe")
pytest_exe_candidate2 = os.path.join(
    venv_scripts_path, "pytest"
)  # For non-Windows venv or if .exe is implicit
pytest_executable = "pytest"  # Fallback if full path isn't found or needed

if os.path.exists(pytest_exe_candidate1):
    pytest_executable = pytest_exe_candidate1
elif os.path.exists(pytest_exe_candidate2):
    pytest_executable = pytest_exe_candidate2

tests_directory_relative = "tests"  # Relative to project_root
tests_directory_absolute = os.path.join(project_root, tests_directory_relative)

log(f"Attempting to use pytest executable: {pytest_executable}")
log(f"Target tests directory: {tests_directory_absolute}")

# Verify executable and directory before running
if not os.path.exists(pytest_executable):
    # Try a simpler check if pytest is on PATH from activated venv
    if subprocess.run(
        ["where", "pytest"],
        capture_output=True,
        text=True,
        shell=True,
        cwd=project_root,
    ).stdout.strip():
        log(
            "'pytest.exe' not found at specified venv path, but 'pytest' found on PATH. Will attempt to use 'pytest'."
        )
        pytest_executable = "pytest"  # Rely on PATH
    else:
        log(
            f"ERROR: Pytest executable not found at {pytest_exe_candidate1} or {pytest_exe_candidate2}, and not found on PATH."
        )
        log_file.close()
        sys.exit(1)

if not os.path.isdir(tests_directory_absolute):
    log(f"ERROR: Tests directory not found at {tests_directory_absolute}")
    log_file.close()
    sys.exit(1)

command = [
    pytest_executable,
    tests_directory_relative,
    "-v",
    "-rA",
]  # -v for verbose, -rA for all output
log(f"Executing command: {' '.join(command)} from CWD: {project_root}")

try:
    # Execute pytest from the project root directory
    process = subprocess.run(
        command,
        cwd=project_root,
        capture_output=True,
        text=True,
        check=False,
        shell=False,
    )  # shell=False is safer

    log("\n--- Pytest STDOUT ---")
    log(process.stdout if process.stdout.strip() else "<No STDOUT>")

    log("\n--- Pytest STDERR ---")
    log(process.stderr if process.stderr.strip() else "<No STDERR>")

    log(f"\n--- Pytest Return Code: {process.returncode} ---")

except FileNotFoundError as fnf_error:
    log(
        f"CRITICAL ERROR: Pytest command could not be run. FileNotFoundError: {fnf_error}"
    )
    log(
        f"Ensure '{pytest_executable}' is correct and on your system PATH if not using full path, and that venv is active if relying on PATH."
    )
except Exception as e:
    log(f"CRITICAL ERROR: Exception during pytest execution: {e}")
    import traceback

    log(traceback.format_exc())

log("--- End of pytest diagnostic run ---")
log_file.close()
