"""
Script to fix VS Code Python interpreter configuration.
This script ensures VS Code correctly recognizes the virtual environment.
"""

import json
import subprocess
import sys
from pathlib import Path


def fix_vscode_interpreter():
    """Fix VS Code interpreter configuration for the project"""
    print("\n=== VS Code Python Interpreter Fix ===")
    print(f"Current Python: {sys.executable}")
    print(f"Python Version: {sys.version}")

    # Identify project paths
    project_dir = Path("C:/project-kortana")
    src_dir = project_dir / "src"
    vscode_dir = project_dir / ".vscode"
    src_vscode_dir = src_dir / ".vscode"

    # Ensure .vscode directories exist
    vscode_dir.mkdir(exist_ok=True)
    src_vscode_dir.mkdir(exist_ok=True)

    # Check for virtual environments
    venv_dir = project_dir / "venv311"
    alt_venv_dir = project_dir / ".venv"

    # Find the best Python interpreter to use
    venv_python = None
    venv_name = None

    # Check venv311 first (preferred)
    if venv_dir.exists():
        venv_python_path = venv_dir / "Scripts" / "python.exe"
        if venv_python_path.exists():
            venv_python = venv_python_path
            venv_name = "venv311"
            print(f"\nFound primary virtual environment: {venv_python}")

    # Check .venv as fallback
    if venv_python is None and alt_venv_dir.exists():
        alt_venv_python_path = alt_venv_dir / "Scripts" / "python.exe"
        if alt_venv_python_path.exists():
            venv_python = alt_venv_python_path
            venv_name = ".venv"
            print(f"\nFound alternative virtual environment: {venv_python}")

    # If no venv found, notify user
    if venv_python is None:
        print("\nNo valid virtual environment found!")
        print("Expected locations:")
        print(f"  - {venv_dir / 'Scripts' / 'python.exe'}")
        print(f"  - {alt_venv_dir / 'Scripts' / 'python.exe'}")
        sys.exit(1)

    # Get the Python version from the venv
    try:
        result = subprocess.run(
            [str(venv_python), "-V"], capture_output=True, text=True, check=True
        )
        python_version = result.stdout.strip()
        print(f"Interpreter version: {python_version}")
    except subprocess.CalledProcessError as e:
        print(f"Warning: Could not determine Python version: {e}")
        python_version = "Unknown"

    # Update root settings.json
    root_settings_path = vscode_dir / "settings.json"
    root_settings = {}

    if root_settings_path.exists():
        try:
            with open(root_settings_path, "r") as f:
                root_settings = json.load(f)
        except json.JSONDecodeError:
            print("Warning: Existing root settings.json is invalid, creating new file")

    # Update Python settings
    venv_path_str = str(venv_python).replace("\\", "\\\\")
    root_settings["python.defaultInterpreterPath"] = venv_path_str
    root_settings["python.terminal.activateEnvironment"] = True
    root_settings["python.terminal.activateEnvInCurrentTerminal"] = True

    # Update file exclusions
    if "files.exclude" not in root_settings:
        root_settings["files.exclude"] = {}

    root_settings["files.exclude"].update(
        {"**/__pycache__": True, "**/*.pyc": True, "**/.pytest_cache": True}
    )

    # Ensure venv folders are visible
    root_settings["files.exclude"][f"**/{venv_name}"] = False

    # Update search exclusions
    if "search.exclude" not in root_settings:
        root_settings["search.exclude"] = {}

    root_settings["search.exclude"][f"**/{venv_name}"] = False

    # Add Python extra paths
    root_settings["python.analysis.extraPaths"] = [".", "src"]

    # Add testing configuration
    root_settings["python.testing.pytestEnabled"] = True

    # Write updated root settings
    with open(root_settings_path, "w") as f:
        json.dump(root_settings, f, indent=4)

    print(f"\nUpdated VS Code settings at: {root_settings_path}")

    # Update src directory settings.json
    src_settings_path = src_vscode_dir / "settings.json"
    src_settings = {}

    if src_settings_path.exists():
        try:
            with open(src_settings_path, "r") as f:
                src_settings = json.load(f)
        except json.JSONDecodeError:
            print("Warning: Existing src settings.json is invalid, creating new file")

    # Configure src directory settings
    src_settings["python.defaultInterpreterPath"] = venv_path_str
    src_settings["python.terminal.activateEnvironment"] = True
    src_settings["python.terminal.activateEnvInCurrentTerminal"] = True

    if "files.exclude" not in src_settings:
        src_settings["files.exclude"] = {}

    src_settings["files.exclude"].update(
        {"**/__pycache__": True, "**/*.pyc": True, "**/.pytest_cache": True}
    )

    src_settings["files.exclude"][f"**/{venv_name}"] = False

    if "search.exclude" not in src_settings:
        src_settings["search.exclude"] = {}

    src_settings["search.exclude"][f"**/{venv_name}"] = False

    src_settings["python.analysis.extraPaths"] = [".", ".."]

    # Write updated src settings
    with open(src_settings_path, "w") as f:
        json.dump(src_settings, f, indent=4)

    print(f"Updated src directory settings at: {src_settings_path}")

    # Update workspace file if it exists
    workspace_files = list(project_dir.glob("*.code-workspace"))
    if workspace_files:
        workspace_file = workspace_files[0]
        try:
            with open(workspace_file, "r") as f:
                workspace_data = json.load(f)

            if "settings" not in workspace_data:
                workspace_data["settings"] = {}

            workspace_data["settings"]["python.defaultInterpreterPath"] = venv_path_str
            workspace_data["settings"]["python.pythonPath"] = (
                venv_path_str  # For backward compatibility
            )

            # Update workspace settings
            workspace_settings = workspace_data["settings"]

            if "files.exclude" not in workspace_settings:
                workspace_settings["files.exclude"] = {}

            workspace_settings["files.exclude"].update(
                {"**/__pycache__": True, "**/*.pyc": True, "**/.pytest_cache": True}
            )

            workspace_settings["files.exclude"][f"**/{venv_name}"] = False

            if "search.exclude" not in workspace_settings:
                workspace_settings["search.exclude"] = {}

            workspace_settings["search.exclude"][f"**/{venv_name}"] = False

            # Write updated workspace file
            with open(workspace_file, "w") as f:
                json.dump(workspace_data, f, indent=4)

            print(f"Updated workspace file at: {workspace_file}")
        except Exception as e:
            print(f"Error updating workspace file: {e}")

    # Create an interpreter info file to help VS Code detect the environment
    interpreter_info_path = vscode_dir / "interpreter-info.json"
    interpreter_info = {
        "path": venv_path_str,
        "version": python_version,
        "envName": venv_name,
    }

    with open(interpreter_info_path, "w") as f:
        json.dump(interpreter_info, f, indent=4)

    print(f"Created interpreter info file at: {interpreter_info_path}")

    # Create .env file at project root
    env_file_path = project_dir / ".env"
    with open(env_file_path, "w") as f:
        f.write(f"PYTHONPATH=.;{project_dir};{src_dir}\n")

    print(f"Updated environment file at: {env_file_path}")

    # Final instructions
    print("\n=== Instructions ===")
    print("1. Close all VS Code windows completely")
    print("2. Reopen VS Code with the project at C:\\project-kortana")
    print("3. Use Command Palette (Ctrl+Shift+P) and type 'Python: Select Interpreter'")
    print(f"4. Choose the interpreter at {venv_python}")
    print("\nIf the interpreter is still not showing up:")
    print("1. Close VS Code completely")
    print("2. Open VS Code from the command line with: code C:\\project-kortana")
    print("3. Try the 'Python: Select Interpreter' command again")


if __name__ == "__main__":
    fix_vscode_interpreter()
    fix_vscode_interpreter()
