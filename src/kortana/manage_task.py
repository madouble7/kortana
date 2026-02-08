#!/usr/bin/env python3
"""
Kor'tana Task Management Script
Handles execution of autonomous tasks.
"""

import argparse
import importlib
import json
import logging
import os
import re
import subprocess
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

# Whitelist of allowed modules for task execution (security measure)
ALLOWED_MODULES = {
    "kortana.agents",
    "kortana.core",
    "kortana.tools",
    "kortana.utils",
}


def validate_module_name(module_name: str) -> bool:
    """
    Validate that a module name is in the whitelist.
    
    Args:
        module_name: The module name to validate
        
    Returns:
        True if the module is allowed, False otherwise
    """
    # Check if module starts with any allowed prefix
    for allowed in ALLOWED_MODULES:
        if module_name.startswith(allowed):
            return True
    return False


def validate_command_args(command: str) -> bool:
    """
    Validate command string for shell injection risks.
    
    Args:
        command: The command string to validate
        
    Returns:
        True if command appears safe, False otherwise
    """
    # Disallow common shell injection patterns
    dangerous_patterns = [
        r'[;&|`$()]',  # Shell metacharacters
        r'\$\{',  # Variable expansion
        r'>\s*\&',  # Redirection
        r'<\s*\&',  # Redirection
    ]
    
    for pattern in dangerous_patterns:
        if re.search(pattern, command):
            logger.warning(f"Potentially dangerous command pattern detected: {pattern}")
            return False
    
    return True


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
        # Set up task environment (with validation)
        if "env_vars" in task_config:
            for key, value in task_config["env_vars"].items():
                # Validate environment variable names to prevent injection
                if not re.match(r'^[A-Z_][A-Z0-9_]*$', key):
                    logger.error(f"Invalid environment variable name: {key}")
                    return {
                        "success": False,
                        "error": f"Invalid environment variable name: {key}",
                        "task_id": task_id,
                        "timestamp": datetime.now().isoformat(),
                    }
                os.environ[key] = str(value)

        # Execute task module if specified
        if "module" in task_config:
            module_name = task_config["module"]
            function_name = task_config.get("function", "execute")

            # Security: Validate module name against whitelist
            if not validate_module_name(module_name):
                logger.error(
                    f"Module '{module_name}' is not in the allowed modules list"
                )
                return {
                    "success": False,
                    "error": f"Module '{module_name}' is not allowed",
                    "task_id": task_id,
                    "timestamp": datetime.now().isoformat(),
                }

            # Security: Validate function name format
            if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', function_name):
                logger.error(f"Invalid function name: {function_name}")
                return {
                    "success": False,
                    "error": f"Invalid function name: {function_name}",
                    "task_id": task_id,
                    "timestamp": datetime.now().isoformat(),
                }

            # Use importlib instead of __import__ for security
            try:
                module = importlib.import_module(module_name)
                task_func = getattr(module, function_name)
            except (ImportError, AttributeError) as e:
                logger.error(f"Failed to import module or function: {e}")
                return {
                    "success": False,
                    "error": f"Failed to import: {e}",
                    "task_id": task_id,
                    "timestamp": datetime.now().isoformat(),
                }

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
            command = task_config["command"]
            cwd = task_config.get("working_dir")

            # Security: Validate command for injection risks
            if not validate_command_args(command):
                logger.error(f"Command contains potentially dangerous patterns: {command}")
                return {
                    "success": False,
                    "error": "Command validation failed - potentially unsafe command",
                    "task_id": task_id,
                    "timestamp": datetime.now().isoformat(),
                }

            logger.info(f"Executing command: {command}")
            # Security: Use shell=False with list of arguments
            # Split command into list (basic splitting - for production, use shlex.split)
            try:
                import shlex
                command_list = shlex.split(command)
            except ValueError as e:
                logger.error(f"Failed to parse command: {e}")
                return {
                    "success": False,
                    "error": f"Invalid command syntax: {e}",
                    "task_id": task_id,
                    "timestamp": datetime.now().isoformat(),
                }
            
            process = subprocess.run(
                command_list, shell=False, cwd=cwd, capture_output=True, text=True
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
