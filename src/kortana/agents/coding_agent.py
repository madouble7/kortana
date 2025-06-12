"""
A specialized agent for executing code development tasks.
This module provides functionality for executing tasks according to a plan.
"""

from typing import Any

from dev_agent import execute_dev_task


class CodingAgent:
    """
    An agent responsible for executing coding tasks according to a plan.
    Uses the dev_agent module to execute individual development tasks.
    """

    def __init__(self, planner: Any) -> None:
        """
        Initialize a CodingAgent.

        Args:
            planner: The planning agent that generates daily task plans
        """
        self.planner = planner

    def execute_today(self) -> dict[str, Any]:
        """
        Execute all tasks planned for today.

        Returns:
            Dict[str, Any]: A dictionary mapping task descriptions to their execution results
        """
        plan = self.planner.plan_day()
        results = {}
        for task in plan["today"]:
            results[task] = execute_dev_task(task)
        return results
        return results
