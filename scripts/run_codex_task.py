import subprocess
import sys


def get_default_branch():
    try:
        # Try to get the default branch name (main or master)
        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
            cwd=".",  # Run in current directory (project root)
        )
        current_branch = result.stdout.strip()
        if current_branch == "HEAD":  # Detached HEAD state
            result = subprocess.run(
                ["git", "branch", "--show-current"],
                capture_output=True,
                text=True,
                check=True,
                cwd=".",
            )
            current_branch = result.stdout.strip()

        # Check if current branch is main or master, otherwise assume main
        if current_branch in ["main", "master"]:
            return current_branch
        else:
            # If not on main or master, try to find the default remote branch
            result = subprocess.run(
                ["git", "remote", "show", "origin"],
                capture_output=True,
                text=True,
                check=True,
                cwd=".",
            )
            remote_info = result.stdout
            for line in remote_info.splitlines():
                if "HEAD branch" in line:
                    return line.split(":", 1)[1].strip()

            # Fallback if unable to determine default branch
            print("Warning: Could not determine default git branch. Assuming 'main'.")
            return "main"

    except subprocess.CalledProcessError as e:
        print(f"Error determining default branch: {e.stderr}")
        return "main"  # Default to 'main' on error
    except FileNotFoundError:
        print("Error: git command not found. Ensure git is installed and in PATH.")
        sys.exit(1)


def run_codex_task(task_name):
    default_branch = get_default_branch()
    if not default_branch:
        print("Error: Could not determine default git branch.")
        sys.exit(1)

    branch_name = f"codex/{task_name}"
    print(
        f"Attempting to create and checkout branch: {branch_name} from {default_branch}"
    )

    try:
        # Ensure we are on the default branch before creating a new one
        subprocess.run(["git", "checkout", default_branch], check=True, cwd=".")
        # Create and checkout the new branch
        subprocess.run(["git", "checkout", "-b", branch_name], check=True, cwd=".")
        print(f"Successfully created and checked out branch: {branch_name}")

        # Run the actual codex_runner.py script
        print(f"Running codex_runner.py for task: {task_name}")
        subprocess.run(
            [sys.executable, "tools/codex/codex_runner.py", task_name],
            check=True,
            cwd=".",
        )
        print(f"Codex task '{task_name}' executed successfully.")

    except subprocess.CalledProcessError as e:
        print(f"Error executing git or codex_runner: {e.stderr}")
        sys.exit(1)
    except FileNotFoundError:
        print(
            "Error: Ensure 'tools/codex/codex_runner.py' exists and is in the correct path."
        )
        sys.exit(1)
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        sys.exit(1)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python run_codex_task.py <task_name>")
        sys.exit(1)

    task_name = sys.argv[1]
    run_codex_task(task_name)
