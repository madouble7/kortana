"""
A planning agent for task organization and prioritization.
This module provides functionality to plan daily tasks based on memory records.
"""

from datetime import datetime
from typing import Any, Dict, Optional

from kortana.config.schema import KortanaConfig
from kortana.memory.memory_manager import MemoryManager


class PlanningAgent:
    """
    An agent responsible for planning and prioritizing daily tasks.
    Retrieves incomplete tasks from memory and organizes them based on significance.
    """

    def __init__(self, config: Optional[KortanaConfig] = None) -> None:
        """
        Initialize a PlanningAgent with configuration.

        Args:
            config: Configuration for the planning agent and memory manager
        """
        self.config = config if config is not None else KortanaConfig()
        self.mem = MemoryManager(self.config)

    def plan_day(self) -> Dict[str, Any]:
        """
        Create a prioritized plan for today's tasks.

        Returns:
            Dict[str, Any]: A dictionary containing today's date and prioritized tasks
                           {"date": str, "today": List[str]}
        """
        # Load all memory entries
        all_entries = self.mem.load_project_memory()

        # Filter for incomplete tasks
        tasks = [
            entry for entry in all_entries if "incomplete_task" in entry.get("tags", [])
        ]

        # Score & sort by significance/emotional_gravity in metadata
        prioritized = sorted(
            tasks,
            key=lambda x: x.get("metadata", {}).get("significance_score", 0),
            reverse=True,
        )

        # Generate a to-do list (top 5)
        today = [t.get("text", "") for t in prioritized[:5]]
        return {"date": datetime.utcnow().date().isoformat(), "today": today}
        return {"date": datetime.utcnow().date().isoformat(), "today": today}
