"""
Kor'tana's Environmental Scanner
This module is responsible for observing Kor'tana's environment and autonomously
generating new goals when specific conditions or triggers are met.
"""

import json
import logging
import os

from kortana.core.execution_engine import ExecutionEngine
from kortana.core.goal_framework import GoalStatus, GoalType
from kortana.core.goal_manager import GoalManager

logger = logging.getLogger(__name__)

# Sensible defaults for ExecutionEngine, can be moved to config later
DEFAULT_ALLOWED_DIRS_RELATIVE = [
    "src",
    "docs",
    "tests",
    "data",
    ".",
]  # Added "." for project root
DEFAULT_BLOCKED_COMMANDS = ["rm", "del", "sudo", "git", "reboot", "shutdown"]


class EnvironmentalScanner:
    def __init__(self, goal_manager: GoalManager, project_root: str):
        self.goal_manager = goal_manager
        self.project_root = project_root

        allowed_dirs_absolute = [
            os.path.join(self.project_root, d) for d in DEFAULT_ALLOWED_DIRS_RELATIVE
        ]
        self.execution_engine = ExecutionEngine(
            allowed_dirs=allowed_dirs_absolute,
            blocked_commands=DEFAULT_BLOCKED_COMMANDS,
        )

    async def scan_for_opportunities(self):
        """
        Main method to run all configured scans.
        This will be called periodically by the scheduler.
        """
        logger.info(
            "🤖 [EnvironmentalScanner] Starting scan for new goal opportunities..."
        )

        await self._scan_code_health()
        # Add calls to other scan methods here
        # await self._scan_for_new_todos()
        # await self._scan_system_resources()

        logger.info("🤖 [EnvironmentalScanner] Scan complete.")

    def _does_similar_goal_exist(self, title_substring: str) -> bool:
        """Checks if a similar pending or active goal already exists."""
        pending_goals = self.goal_manager.get_goals_by_status(GoalStatus.NEW)
        active_goals = self.goal_manager.get_goals_by_status(GoalStatus.ACTIVE)

        all_relevant_goals = []
        if pending_goals:
            all_relevant_goals.extend(pending_goals)
        if active_goals:
            all_relevant_goals.extend(active_goals)

        for goal in all_relevant_goals:
            if (
                goal
                and hasattr(goal, "title")
                and title_substring.lower() in goal.title.lower()
            ):
                logger.info(
                    f"[EnvironmentalScanner] Similar goal already exists: '{goal.title}' (ID: {goal.goal_id}, Status: {goal.status.value if hasattr(goal.status, 'value') else goal.status})"
                )
                return True
        return False

    async def _scan_code_health(self):
        """
        Scans the codebase for health issues (e.g., linting errors)
        and generates a goal if new issues are found and no similar goal exists.
        """
        logger.info("[EnvironmentalScanner] Scanning code health using Ruff...")
        try:
            ruff_command = "poetry run ruff check src/ --output-format=json --exit-zero"

            try:
                result = await self.execution_engine.execute_shell_command(
                    command=ruff_command,
                    working_dir=self.project_root,
                )
            except AttributeError:
                logger.warning(
                    "[EnvironmentalScanner] Could not perform code health scan. The method 'execute_shell_command' (or similar) was not found on the ExecutionEngine instance. "
                    "Please update environmental_scanner.py with the correct method name for shell execution."
                )
                return

            if result.success and result.data:
                stdout_trimmed = result.data.strip()
                issues_found = []
                if stdout_trimmed:
                    try:
                        issues_found = json.loads(stdout_trimmed)
                    except json.JSONDecodeError:
                        logger.warning(
                            f"[EnvironmentalScanner] Ruff output was not empty but failed to parse as JSON. Output: {stdout_trimmed[:200]}..."
                        )
                        return

                if (
                    issues_found
                    and isinstance(issues_found, list)
                    and len(issues_found) > 0
                ):
                    issue_count = len(issues_found)
                    logger.info(
                        f"[EnvironmentalScanner] Code health check (Ruff) found {issue_count} issues."
                    )

                    goal_title = "Autonomously address code health issues (Ruff)"
                    goal_description = f"Ruff detected {issue_count} code quality issues that need to be reviewed and addressed."

                    if self._does_similar_goal_exist(
                        "Ruff code health issues"
                    ) or self._does_similar_goal_exist(goal_title):
                        logger.info(
                            "[EnvironmentalScanner] Skipping Ruff goal creation as a similar one already exists."
                        )
                        return

                    new_goal = self.goal_manager.create_goal_from_template(
                        goal_type=GoalType.MAINTENANCE,
                        template_name="code_health",
                        title=goal_title,
                        description=goal_description,
                        context={
                            "ruff_issues_count": issue_count,
                            "raw_ruff_output_preview": stdout_trimmed[:500],
                        },
                    )

                    if new_goal:
                        logger.info(
                            f"[EnvironmentalScanner] Created new goal: '{new_goal.title}' (ID: {new_goal.goal_id})"
                        )
                    else:
                        logger.warning(
                            "[EnvironmentalScanner] Failed to create new goal for Ruff code health issues."
                        )
                else:
                    logger.info(
                        "[EnvironmentalScanner] Code health check (Ruff) found no new issues (empty or invalid JSON)."
                        if stdout_trimmed
                        else "[EnvironmentalScanner] Code health check (Ruff) found no issues (empty stdout)."
                    )
            elif not result.success:
                logger.error(
                    f"[EnvironmentalScanner] Code health check (Ruff) command failed: {result.error}"
                )
            else:
                logger.info(
                    "[EnvironmentalScanner] Code health check (Ruff) ran successfully with no output, indicating no issues."
                )

        except Exception as e:
            logger.error(
                f"[EnvironmentalScanner] Error during code health scan: {e}",
                exc_info=True,
            )

    # Placeholder for other scanning methods
    # async def _scan_for_new_todos(self):
    #     logger.info("[EnvironmentalScanner] Scanning for new TODOs...")
    #     # Logic to scan files for "TODO" comments
    #     pass


async def run_environmental_scan_cycle(goal_manager: GoalManager, project_root: str):
    """
    Wrapper function for the scheduler to call.
    """
    scanner = EnvironmentalScanner(goal_manager=goal_manager, project_root=project_root)
    await scanner.scan_for_opportunities()
