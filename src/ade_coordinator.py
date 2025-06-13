"""
ADE Coordinator - Integrates autonomous development with existing agents.
Uses Goal Framework for structured goal management.
"""

import logging
from typing import Any
from uuid import UUID

from kortana.core.autonomous_development_engine import create_ade
from kortana.core.goals import Goal, GoalManager, GoalStatus, GoalType


class ADECoordinator:
    """
    Coordinates between the new Autonomous Development Engine and existing agents.
    Uses Goal Framework for structured goal management.
    """

    def __init__(self, chat_engine) -> None:
        """Initialize coordinator with chat engine and components."""
        self.chat_engine = chat_engine

        # Create ADE instance
        self.ade = create_ade(
            chat_engine.llm_clients.get(chat_engine.default_model_id),
            chat_engine.covenant_enforcer,
            chat_engine.memory_manager,
        )

        # Initialize goal management
        self.goal_manager = GoalManager(
            chat_engine.memory_manager, chat_engine.covenant_enforcer
        )

        # Existing agents
        self.planning_agent = chat_engine.ade_planner
        self.coding_agent = getattr(chat_engine, "ade_coder", None)
        self.testing_agent = chat_engine.ade_tester
        self.monitoring_agent = chat_engine.ade_monitor

    async def start_autonomous_session(
        self, goals: list[str], parent_goal_id: UUID | None = None
    ) -> dict[str, Any]:
        """
        Start a coordinated autonomous development session.

        Args:
            goals: List of goal descriptions
            parent_goal_id: Optional parent goal ID to link these goals under

        Returns:
            Session results including ADE outputs and goal IDs
        """
        logging.info(f"🚀 Starting coordinated ADE session with {len(goals)} goals")

        # Create Goal objects for each goal description
        goal_objects = []
        for description in goals:
            goal = await self.goal_manager.create_goal(
                type=GoalType.DEVELOPMENT,
                description=description,
                parent_id=parent_goal_id,
                created_by="ade_coordinator",
                success_criteria=[
                    "Code changes implemented successfully",
                    "All tests passing",
                    "No regressions in system health",
                ],
            )
            goal_objects.append(goal)
            logging.info(f"Created goal {goal.id}: {description}")

        # Run development cycle on goal descriptions (for backward compatibility)
        ade_results = await self.ade.autonomous_development_cycle(
            [g.description for g in goal_objects], max_cycles=2
        )

        # Process results and update goals
        for i, result in enumerate(ade_results):
            goal = goal_objects[i]
            success = result.get("success", False)

            if success:
                # Update goal progress and trigger verification
                goal.update_progress(0.8)  # 80% done after successful execution

                # Run tests if code was generated
                if "generate_code" in str(result.get("results", [])):
                    test_result = self.testing_agent.run_tests()
                    logging.info(f"Tests for goal {goal.id}: {test_result}")

                    if test_result.get("success"):
                        goal.update_progress(0.9)  # 90% after successful tests
                    else:
                        goal.add_blocker(f"Tests failed: {test_result.get('error')}")
                        goal.update_status(GoalStatus.BLOCKED)

        return {
            "success": True,
            "goals": [str(g.id) for g in goal_objects],
            "results": ade_results,
        }

    async def get_active_goals(self) -> list[Goal]:
        """Get all goals currently being worked on."""
        return await self.goal_manager.list_goals(status=GoalStatus.IN_PROGRESS)

    async def get_blocked_goals(self) -> list[Goal]:
        """Get all goals that are blocked."""
        return await self.goal_manager.list_goals(status=GoalStatus.BLOCKED)

    async def get_pending_goals(self) -> list[Goal]:
        """Get all goals waiting to be worked on."""
        return await self.goal_manager.list_goals(status=GoalStatus.PENDING)
