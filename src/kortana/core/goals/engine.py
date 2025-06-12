"""
Goal Engine for Kor'tana's Autonomous Development System.

This component orchestrates the process of goal processing and execution.
"""

import asyncio
import logging

from kortana.core.execution_engine import ExecutionEngine
from kortana.core.goals.goal import GoalStatus
from kortana.core.goals.manager import GoalManager
from kortana.core.planning_engine import PlanningEngine

logger = logging.getLogger(__name__)

DEFAULT_ALLOWED_DIRS_RELATIVE_ENGINE = ["src", "docs", "tests", "data", "."]
DEFAULT_BLOCKED_COMMANDS_ENGINE = ["rm", "del", "sudo", "git", "reboot", "shutdown"]


class GoalEngine:
    """
    The core engine that processes and executes goals.
    """

    def __init__(
        self,
        goal_manager: GoalManager,
        environmental_scanner,
        goal_generator,
        goal_prioritizer,
        planning_engine: PlanningEngine,
        execution_engine: ExecutionEngine,
    ) -> None:
        self.goal_manager = goal_manager
        self.scanner = environmental_scanner
        self.generator = goal_generator
        self.prioritizer = goal_prioritizer
        self.planning_engine = planning_engine
        self.execution_engine = execution_engine
        self._is_running = False
        self._processing_lock = asyncio.Lock()
        logger.info("GoalEngine initialized.")

    async def run_cycle(self) -> list:
        logger.info("Running Goal Engine cycle...")
        # 1. Scan Environment
        potential_descriptions = await self.scanner.scan_environment()
        if not potential_descriptions:
            logger.info("No potential goals identified during scan.")
            return []
        # 2. Generate Goals
        generated_goals = await self.generator.generate_goals(potential_descriptions)
        if not generated_goals:
            logger.warning("No structured goals generated.")
            return []
        # 3. Prioritize Goals
        prioritized_goals = await self.prioritizer.prioritize_goals(generated_goals)
        if not prioritized_goals:
            logger.info("No goals to execute after prioritization.")
            return []
        # 4. Select the top goal
        top_goal = prioritized_goals[0]
        logger.info(
            f"Selected top goal: {top_goal.description} (Priority: {top_goal.priority})"
        )
        try:
            # Mark as IN_PROGRESS
            top_goal.update_status(GoalStatus.IN_PROGRESS)
            await self.goal_manager.update_goal(top_goal)
            # 5. Plan the goal
            plan_steps = await self.planning_engine.create_plan_for_goal(
                top_goal.description
            )
            if not plan_steps:
                top_goal.update_status(GoalStatus.FAILED)
                await self.goal_manager.update_goal(top_goal)
                logger.error("Planning failed for goal.")
                return prioritized_goals
            # 6. Execute the plan step by step
            execution_context = {}
            for i, step in enumerate(plan_steps):
                action_type = step.get("action_type")
                params = step.get("parameters", {})
                # Simple context injection for step outputs (if needed)
                for k, v in params.items():
                    if isinstance(v, str) and v.startswith("{{step_"):
                        ref_num = int(v.split("{{step_")[1].split("_output}}")[0])
                        params[k] = execution_context.get(f"step_{ref_num}")
                result = {}
                try:
                    if action_type == "READ_FILE":
                        result = self.execution_engine.read_file(**params)
                        if result.get("success"):
                            execution_context[f"step_{i + 1}"] = result.get("content")
                    elif action_type == "WRITE_FILE":
                        result = self.execution_engine.write_to_file(**params)
                    elif action_type == "EXECUTE_SHELL":
                        result = self.execution_engine.execute_shell_command(**params)
                    elif action_type == "REASONING_COMPLETE":
                        result = {
                            "success": True,
                            "summary": params.get("final_summary"),
                        }
                    else:
                        result = {
                            "success": False,
                            "error": f"Unknown action_type: {action_type}",
                        }
                except Exception as e:
                    result = {"success": False, "error": str(e)}
                if not result.get("success"):
                    top_goal.update_status(GoalStatus.FAILED)
                    await self.goal_manager.update_goal(top_goal)
                    logger.error(f"Step {i + 1} failed: {result.get('error')}")
                    return prioritized_goals
            # If all steps succeeded
            top_goal.update_status(GoalStatus.COMPLETED)
            await self.goal_manager.update_goal(top_goal)
            logger.info(f"Goal completed: {top_goal.description}")
        except Exception as e:
            top_goal.update_status(GoalStatus.FAILED)
            await self.goal_manager.update_goal(top_goal)
            logger.error(f"Goal execution failed: {e}")
        logger.info("Goal Engine cycle finished.")
        return prioritized_goals
