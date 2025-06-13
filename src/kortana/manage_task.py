#!/usr/bin/env python3
"""
Kor'tana Task Management Script
Handles execution of autonomous tasks.
"""

import argparse
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

# Initialize logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(), logging.FileHandler("task_execution.log")],
)
logger = logging.getLogger(__name__)


def load_task_config(task_id: str) -> dict[str, Any] | None:
    """Load task configuration from the tasks directory."""
    try:
        task_file = Path("tasks") / f"{task_id}.json"
        if not task_file.exists():
            logger.error(f"Task configuration not found: {task_file}")
            return None

        with open(task_file) as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading task configuration: {e}")
        return None


def save_task_result(task_id: str, result: dict[str, Any]) -> None:
    """Save task execution result."""
    try:
        result_dir = Path("task_results")
        result_dir.mkdir(exist_ok=True)

        result_file = (
            result_dir / f"{task_id}-{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )
        with open(result_file, "w") as f:
            json.dump(result, f, indent=2)

    except Exception as e:
        logger.error(f"Error saving task result: {e}")


def execute_task(task_id: str) -> dict[str, Any]:
    """Execute a specific task and return the result."""
    start_time = datetime.now()

    task_config = load_task_config(task_id)
    if not task_config:
        return {
            "success": False,
            "error": "Failed to load task configuration",
            "task_id": task_id,
            "timestamp": datetime.now().isoformat(),
        }

    try:
        # Set up task environment
        if "env_vars" in task_config:
            for key, value in task_config["env_vars"].items():
                os.environ[key] = str(value)

        # Execute task module if specified
        if "module" in task_config:
            module_name = task_config["module"]
            function_name = task_config.get("function", "execute")

            sys.path.insert(0, str(Path("modules").resolve()))
            module = __import__(module_name)
            task_func = getattr(module, function_name)

            task_args = task_config.get("args", {})
            result = task_func(**task_args)

            return {
                "success": True,
                "task_id": task_id,
                "result": result,
                "start_time": start_time.isoformat(),
                "end_time": datetime.now().isoformat(),
            }

        # Execute shell command if specified
        elif "command" in task_config:
            import subprocess

            command = task_config["command"]
            cwd = task_config.get("working_dir")

            logger.info(f"Executing command: {command}")
            process = subprocess.run(
                command, shell=True, cwd=cwd, capture_output=True, text=True
            )

            return {
                "success": process.returncode == 0,
                "task_id": task_id,
                "return_code": process.returncode,
                "stdout": process.stdout,
                "stderr": process.stderr,
                "start_time": start_time.isoformat(),
                "end_time": datetime.now().isoformat(),
            }

        else:
            return {
                "success": False,
                "error": "No execution method specified in task configuration",
                "task_id": task_id,
                "timestamp": datetime.now().isoformat(),
            }

    except Exception as e:
        logger.error(f"Error executing task {task_id}: {e}")
        return {
            "success": False,
            "error": str(e),
            "task_id": task_id,
            "start_time": start_time.isoformat(),
            "end_time": datetime.now().isoformat(),
        }


def main():
    parser = argparse.ArgumentParser(description="Kor'tana Task Management")
    parser.add_argument("command", choices=["execute"], help="Command to execute")
    parser.add_argument("task_id", help="ID of the task to execute")

    args = parser.parse_args()

    if args.command == "execute":
        result = execute_task(args.task_id)
        save_task_result(args.task_id, result)
        sys.exit(0 if result["success"] else 1)


if __name__ == "__main__":
    main()
