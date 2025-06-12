#!/usr/bin/env python3
"""
Codex Task Runner for Kortana

This script executes Codex tasks safely within the established CI pipeline.
Integrates with Phase 1 infrastructure (ruff, mypy, pytest) and ensures
all generated code passes quality gates before integration.
"""

import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import openai

print("DEBUG: codex_runner.py script execution started.")  # New top-level print


class CodexTaskRunner:
    """Execute Codex tasks with CI integration and quality validation."""

    def __init__(self, project_root: str | None = None):  # Type hint corrected
        """Initialize the Codex task runner.

        Args:
            project_root: Path to the project root directory
        """
        self.project_root = (
            Path(project_root) if project_root else Path(__file__).parent.parent.parent
        )
        self.codex_dir = self.project_root / "tools" / "codex"
        self.tasks_dir = self.codex_dir / "tasks"
        self.prompts_dir = self.codex_dir / "prompts"
        self.logs_dir = self.codex_dir / "logs"
        self.output_dir = self.codex_dir / "output"

        # DIAGNOSTIC PRINTS
        print(f"DEBUG: self.project_root = {str(self.project_root)}")
        print(f"DEBUG: self.codex_dir = {str(self.codex_dir)}")
        print(f"DEBUG: self.tasks_dir = {str(self.tasks_dir)}")

        # Ensure directories exist
        self.logs_dir.mkdir(exist_ok=True)
        self.output_dir.mkdir(exist_ok=True)

        # Initialize OpenAI client
        self.client = None
        self._init_openai()

    def _init_openai(self) -> None:
        """Initialize OpenAI client with API key validation."""
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError(
                "OPENAI_API_KEY environment variable required. "
                "Set it with: set OPENAI_API_KEY=your_key_here"
            )

        self.client = openai.OpenAI(api_key=api_key)
        print("[SUCCESS] OpenAI client initialized")

    def load_task(self, task_name: str) -> dict[str, Any]:
        """Load a task configuration from JSON file.

        Args:
            task_name: Name of the task (without .json extension)

        Returns:
            Task configuration dictionary
        """
        task_file = self.tasks_dir / f"{task_name}.json"
        # DIAGNOSTIC PRINT
        print(f"DEBUG: task_file in load_task = {str(task_file)}")
        if not task_file.exists():
            raise FileNotFoundError(f"Task file not found: {task_file}")

        with open(task_file, encoding="utf-8") as f:
            return json.load(f)

    def load_prompt(self, prompt_file: str) -> str:
        """Load prompt content from markdown file.

        Args:
            prompt_file: Path to prompt file (relative to project root)

        Returns:
            Prompt content as string
        """
        # DIAGNOSTIC PRINTS
        print(f"DEBUG: load_prompt received prompt_file = {repr(prompt_file)}")
        print(f"DEBUG: load_prompt self.project_root = {repr(str(self.project_root))}")

        prompt_path = self.project_root / prompt_file

        # DIAGNOSTIC PRINT
        print(f"DEBUG: load_prompt constructed prompt_path = {repr(str(prompt_path))}")

        if not prompt_path.exists():
            # DIAGNOSTIC PRINT
            print(f"DEBUG: prompt_path.exists() is False for {repr(str(prompt_path))}")
            raise FileNotFoundError(f"Prompt file not found: {prompt_path}")
        with open(prompt_path, encoding="utf-8") as f:
            return f.read()

    def create_branch(self, branch_name: str) -> bool:
        """Create and checkout a new git branch.

        Args:
            branch_name: Name of the branch to create

        Returns:
            True if successful, False otherwise
        """
        try:
            # Determine the main branch (main or master)
            main_branch_candidates = ["main", "master"]
            current_main_branch = None

            for candidate in main_branch_candidates:
                try:
                    # Check if branch exists locally or remotely before trying to checkout
                    # Check local branches
                    local_check_cmd = [
                        "git",
                        "show-ref",
                        "--verify",
                        f"refs/heads/{candidate}",
                    ]
                    local_exists = (
                        subprocess.run(
                            local_check_cmd,
                            cwd=self.project_root,
                            capture_output=True,
                            text=True,
                            check=False,
                        ).returncode
                        == 0
                    )

                    # Check remote branches (common for CI environments)
                    remote_check_cmd = [
                        "git",
                        "show-ref",
                        "--verify",
                        f"refs/remotes/origin/{candidate}",
                    ]
                    remote_exists = (
                        subprocess.run(
                            remote_check_cmd,
                            cwd=self.project_root,
                            capture_output=True,
                            text=True,
                            check=False,
                        ).returncode
                        == 0
                    )

                    if local_exists or remote_exists:
                        print(
                            f"[INFO] Attempting to checkout existing main branch candidate: {candidate}"
                        )
                        # Change check=True to check=False and manually check returncode
                        checkout_result = subprocess.run(
                            ["git", "checkout", candidate],
                            cwd=self.project_root,
                            check=False,  # Allow failure to check other candidates
                            capture_output=True,
                            text=True,
                        )
                        if checkout_result.returncode == 0:
                            print(
                                f"[SUCCESS] Successfully checked out main branch: {candidate}"
                            )
                            current_main_branch = candidate
                            break  # Found and checked out a main branch
                        else:
                            print(
                                f"[INFO] Failed to checkout branch '{candidate}'. Error: {checkout_result.stderr.strip()}"
                            )

                    else:
                        print(
                            f"[INFO] Main branch candidate '{candidate}' not found locally or on origin."
                        )
                except Exception as e:
                    print(
                        f"[INFO] An unexpected error occurred while checking out branch '{candidate}'. Error: {e}"
                    )

            if not current_main_branch:
                print(
                    "[FAILURE] Failed to checkout 'main' or 'master' branch. Please ensure your repository has one of these branches."
                )
                print(
                    "[FAILURE] Critical: Failed to determine a main branch ('main' or 'master') to branch from."
                )
                return False

            # Create and checkout new branch from the determined main branch
            print(
                f"[INFO] Creating new branch '{branch_name}' from '{current_main_branch}'..."
            )
            subprocess.run(
                ["git", "checkout", "-b", branch_name, current_main_branch],
                cwd=self.project_root,
                check=True,  # Will raise error if this fails
                capture_output=True,
                text=True,
            )
            print(
                f"[SUCCESS] Created and switched to new branch: {branch_name} (from {current_main_branch})"
            )
            return True
        except subprocess.CalledProcessError as e:
            print(
                f"[FAILURE] Failed to create or switch to branch '{branch_name}'. Git command failed. Error: {e.stderr.strip()}"
            )
            # Attempt to switch back to the original main branch if possible
            if (
                current_main_branch and current_main_branch != branch_name
            ):  # only if current_main_branch was set and is not the failed branch_name
                try:
                    subprocess.run(
                        ["git", "checkout", current_main_branch],
                        cwd=self.project_root,
                        check=False,
                        capture_output=True,
                    )
                    print(f"[INFO] Attempted to switch back to {current_main_branch}.")
                except Exception as revert_e:
                    print(
                        f"[WARNING] Failed to switch back to {current_main_branch} after error: {revert_e}"
                    )
            return False
        except Exception as e:
            print(
                f"[FAILURE] An unexpected error occurred during branch creation for '{branch_name}': {e}"
            )
            return False

    def run_ci_checks(self, checks: list[str]) -> bool:
        """Run CI checks as specified in task configuration.

        Args:
            checks: List of commands to run

        Returns:
            True if all checks pass, False otherwise
        """
        print("Running CI checks...")

        for check in checks:
            print(f"  Running: {check}")
            try:
                # Handle Windows cmd commands properly
                if check.startswith("ruff"):
                    subprocess.run(
                        check.split(),
                        cwd=self.project_root,
                        check=True,
                        capture_output=True,
                        text=True,
                    )
                elif check.startswith("mypy"):
                    subprocess.run(
                        check.split(),
                        cwd=self.project_root,
                        check=True,
                        capture_output=True,
                        text=True,
                    )
                elif check.startswith("pytest"):
                    subprocess.run(
                        check.split(),
                        cwd=self.project_root,
                        check=True,
                        capture_output=True,
                        text=True,
                    )
                else:
                    # Generic command
                    subprocess.run(
                        check,
                        shell=True,
                        cwd=self.project_root,
                        check=True,
                        capture_output=True,
                        text=True,
                    )

                print(f"  [SUCCESS] {check} passed")

            except subprocess.CalledProcessError as e:
                print(f"  [FAILURE] {check} failed:")
                print(f"    stdout: {e.stdout}")
                print(f"    stderr: {e.stderr}")
                return False

        print("[SUCCESS] All CI checks passed!")
        return True

    def generate_code(self, prompt: str, task_config: dict[str, Any]) -> str:
        """Generate code using OpenAI Codex.

        Args:
            prompt: The prompt to send to Codex
            task_config: Task configuration dictionary

        Returns:
            Generated code as string
        """
        print("Generating code with OpenAI...")

        try:
            response = self.client.chat.completions.create(
                model="gpt-4",  # Using GPT-4 for better code generation
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are an expert Python developer working on the Kortana project. "
                            "Generate high-quality, well-documented code that follows the project's "
                            "existing patterns and passes strict linting (ruff) and type checking (mypy). "
                            "Follow Google-style docstrings and include comprehensive error handling."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
                max_tokens=4000,
                temperature=0.1,  # Low temperature for consistent, reliable code
            )

            generated_code = response.choices[0].message.content.strip()
            print(f"[SUCCESS] Generated {len(generated_code)} characters of code")
            return generated_code

        except Exception as e:
            print(f"[FAILURE] Failed to generate code: {e}")
            raise

    def save_generated_code(self, code: str, target_file: str) -> bool:
        """Save generated code to the target file.

        Args:
            code: Generated code content
            target_file: Path to target file (relative to project root)

        Returns:
            True if successful, False otherwise
        """
        target_path = self.project_root / target_file

        # Ensure target directory exists
        target_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            with open(target_path, "w", encoding="utf-8") as f:
                f.write(code)

            print(f"[SUCCESS] Saved generated code to: {target_file}")
            return True

        except Exception as e:
            print(f"[FAILURE] Failed to save code to {target_file}: {e}")
            return False

    def commit_and_push(self, commit_message: str, push: bool = True) -> bool:
        """Commit changes and optionally push to remote.

        Args:
            commit_message: Git commit message
            push: Whether to push to remote repository

        Returns:
            True if successful, False otherwise
        """
        try:
            # Add all changes
            subprocess.run(
                ["git", "add", "."],
                cwd=self.project_root,
                check=True,
                capture_output=True,
            )

            # Commit changes
            subprocess.run(
                ["git", "commit", "-m", commit_message],
                cwd=self.project_root,
                check=True,
                capture_output=True,
            )

            print(f"[SUCCESS] Committed changes: {commit_message}")

            if push:
                # Get current branch name
                result = subprocess.run(
                    ["git", "branch", "--show-current"],
                    cwd=self.project_root,
                    check=True,
                    capture_output=True,
                    text=True,
                )
                branch_name = result.stdout.strip()

                # Push to remote (using pre-configured HTTPS remote)
                subprocess.run(
                    ["git", "push", "-u", "origin", branch_name],
                    cwd=self.project_root,
                    check=True,
                    capture_output=True,
                )

                print(f"[SUCCESS] Pushed to remote: {branch_name}")

            return True

        except subprocess.CalledProcessError as e:
            print(f"[FAILURE] Failed to commit/push: {e}")
            return False

    def log_task_execution(
        self, task_name: str, success: bool, details: dict[str, Any]
    ) -> None:
        """Log task execution details.

        Args:
            task_name: Name of the executed task
            success: Whether the task succeeded
            details: Additional execution details
        """
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "task_name": task_name,
            "success": success,
            "details": details,
        }

        log_file = (
            self.logs_dir / f"task_execution_{datetime.now().strftime('%Y%m%d')}.jsonl"
        )

        with open(log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry) + "\n")

    def execute_task(self, task_name: str) -> bool:
        """Execute a complete Codex task.

        Args:
            task_name: Name of the task to execute

        Returns:
            True if successful, False otherwise
        """
        print(f"Executing Codex task: {task_name}")
        print("=" * 50)

        start_time = datetime.now()
        success = False
        details = {}

        try:
            # Load task configuration
            task_config = self.load_task(task_name)
            details["task_config"] = task_config

            # Load prompt
            prompt = self.load_prompt(task_config["prompt_file"])
            details["prompt_length"] = len(prompt)

            # Create branch if specified
            if "branch" in task_config and not self.create_branch(
                task_config["branch"]
            ):
                return False

            # Generate code
            generated_code = self.generate_code(prompt, task_config)
            details["generated_code_length"] = len(generated_code)

            # Save generated code
            if not self.save_generated_code(generated_code, task_config["target_file"]):
                return False

            # Run CI checks
            if "ci_checks" in task_config and not self.run_ci_checks(
                task_config["ci_checks"]
            ):
                details["ci_checks_failed"] = True
                return False

            # Commit and push
            commit_msg = task_config.get(
                "commit_message", f"feat: {task_name} via codex"
            )
            push_enabled = task_config.get("push", True)

            if not self.commit_and_push(commit_msg, push_enabled):
                return False

            success = True
            print("[SUCCESS] Task executed successfully!")

        except Exception as e:
            print(f"[FAILURE] Task execution failed: {e}")
            details["error"] = str(e)

        finally:
            end_time = datetime.now()
            details["execution_time_seconds"] = (end_time - start_time).total_seconds()
            self.log_task_execution(task_name, success, details)

        return success


def main():
    """Main entry point for the Codex task runner."""
    print("DEBUG: main() function started.")  # New print in main
    if len(sys.argv) != 2:
        print("Usage: python codex_runner.py <task_name>")
        print("Example: python codex_runner.py test_brain_utils")
        sys.exit(1)

    task_name = sys.argv[1]
    print(f"DEBUG: task_name = {task_name}")  # New print in main

    try:
        print("DEBUG: Attempting to instantiate CodexTaskRunner.")  # New print
        runner = CodexTaskRunner()
        print("DEBUG: CodexTaskRunner instantiated successfully.")  # New print
        print("DEBUG: Attempting to execute task.")  # New print
        success = runner.execute_task(task_name)
        print(f"DEBUG: Task execution finished. Success: {success}")  # New print
        sys.exit(0 if success else 1)

    except Exception as e:
        print(f"[FATAL ERROR] in main: {e}")
        sys.exit(1)


if __name__ == "__main__":
    print("DEBUG: __name__ == '__main__' block reached.")  # New print
    main()
