"""
GoalManager for Kor'tana's Goal Framework.
Handles goal lifecycle, storage, and Sacred Covenant validation.
"""

import logging
from datetime import UTC, datetime
from uuid import UUID

from ..covenant import CovenantEnforcer
from ..memory import MemoryManager
from .goal import Goal, GoalStatus, GoalType


class GoalManager:
    """
    Manages the lifecycle of Kor'tana's goals.
    Integrates with memory system for persistence and covenant system for validation.
    """

    def __init__(
        self, memory_manager: MemoryManager, covenant_enforcer: CovenantEnforcer
    ) -> None:
        self.logger = logging.getLogger(__name__)
        self.memory = memory_manager
        self.covenant = covenant_enforcer
        self.active_goals: dict[UUID, Goal] = {}

    async def create_goal(
        self,
        type: GoalType,
        description: str,
        priority: int = 1,
        parent_id: UUID | None = None,
        created_by: str = "kor_tana",
        success_criteria: list[str] | None = None,
    ) -> Goal:
        """Create a new goal and validate it through Sacred Covenant"""
        goal = Goal(
            type=type,
            description=description,
            priority=priority,
            parent_goal_id=parent_id,
            created_by=created_by,
            success_criteria=success_criteria or [],
        )

        # Validate through Sacred Covenant
        approved, feedback = await self._validate_with_covenant(goal)
        goal.set_covenant_approval(approved, feedback)

        if not approved:
            self.logger.warning(f"Goal rejected by Sacred Covenant: {feedback}")
            goal.update_status(GoalStatus.FAILED)
            return goal

        # Add to active goals and memory
        self.active_goals[goal.id] = goal
        await self._persist_to_memory(goal)

        # Update parent-child relationships
        if parent_id:
            parent = self.active_goals.get(parent_id)
            if parent:
                parent.add_child_goal(goal.id)
                await self.update_goal(parent)

        self.logger.info(f"Created goal: {goal.description} [{goal.id}]")
        return goal

    async def update_goal(self, goal: Goal) -> Goal:
        """Update an existing goal's state"""
        if goal.id not in self.active_goals:
            raise ValueError(f"Goal {goal.id} not found in active goals")

        self.active_goals[goal.id] = goal
        await self._persist_to_memory(goal)

        self.logger.info(
            f"Updated goal {goal.id}: {goal.status.value}, "
            f"progress: {goal.progress:.1%}"
        )
        return goal

    async def get_goal(self, goal_id: UUID) -> Goal | None:
        """Retrieve a goal by ID"""
        # Check active goals first
        if goal_id in self.active_goals:
            return self.active_goals[goal_id]

        # If not active, try to load from memory
        goal_data = await self._load_from_memory(goal_id)
        if goal_data:
            goal = Goal(**goal_data)
            self.active_goals[goal_id] = goal
            return goal

        return None

    async def delete_goal(self, goal_id: UUID) -> bool:
        """Delete a goal and its memory entries"""
        if goal_id not in self.active_goals:
            return False

        goal = self.active_goals[goal_id]

        # Update parent if needed
        if goal.parent_goal_id:
            parent = await self.get_goal(goal.parent_goal_id)
            if parent and goal_id in parent.child_goal_ids:
                parent.child_goal_ids.remove(goal_id)
                await self.update_goal(parent)

        # Update any dependent goals
        for dep_id in goal.dependent_goal_ids:
            dep_goal = await self.get_goal(dep_id)
            if dep_goal:
                dep_goal.add_blocker(f"Dependent goal {goal_id} was deleted")
                dep_goal.update_status(GoalStatus.BLOCKED)
                await self.update_goal(dep_goal)

        # Remove from active goals and memory
        del self.active_goals[goal_id]
        await self._remove_from_memory(goal_id)

        self.logger.info(f"Deleted goal {goal_id}")
        return True

    async def list_goals(
        self,
        status: GoalStatus | None = None,
        type: GoalType | None = None,
        parent_id: UUID | None = None,
    ) -> list[Goal]:
        """List goals with optional filtering"""
        goals = list(self.active_goals.values())

        if status:
            goals = [g for g in goals if g.status == status]
        if type:
            goals = [g for g in goals if g.type == type]
        if parent_id:
            goals = [g for g in goals if g.parent_goal_id == parent_id]

        return sorted(goals, key=lambda g: (-g.priority, g.created_at))

    async def get_blocked_goals(self) -> list[Goal]:
        """Get all goals currently in BLOCKED status"""
        return await self.list_goals(status=GoalStatus.BLOCKED)

    async def get_child_goals(self, parent_id: UUID) -> list[Goal]:
        """Get all child goals for a given parent goal"""
        return await self.list_goals(parent_id=parent_id)

    async def _validate_with_covenant(self, goal: Goal) -> tuple[bool, str]:
        """Submit goal for Sacred Covenant validation"""
        # Prepare validation context
        validation_context = {
            "goal_type": goal.type.value,
            "description": goal.description,
            "created_by": goal.created_by,
        }

        # Get validation results
        is_valid, feedback = await self.covenant.validate_action(
            action_type="create_goal", context=validation_context
        )

        if is_valid:
            # Get Sacred Trinity alignment scores
            scores = await self.covenant.evaluate_sacred_alignment(goal.description)
            goal.update_sacred_scores(
                wisdom=scores.get("wisdom", 0.0),
                compassion=scores.get("compassion", 0.0),
                truth=scores.get("truth", 0.0),
            )

        return is_valid, feedback

    async def _persist_to_memory(self, goal: Goal) -> None:
        """Store goal state in memory system"""
        memory_entry = {
            "role": "goal_state",
            "goal_id": str(goal.id),
            "content": goal.__dict__,  # Store full state
            "timestamp": datetime.now(UTC).isoformat(),
            "metadata": {
                "type": goal.type.value,
                "status": goal.status.value,
                "progress": goal.progress,
            },
        }

        await self.memory.store_entry(memory_entry)

    async def _load_from_memory(self, goal_id: UUID) -> dict | None:
        """Load goal state from memory system"""
        query = f"goal_state AND goal_id:{str(goal_id)}"
        entries = await self.memory.search_entries(query, limit=1)

        if entries:
            return entries[0].get("content")
        return None

    async def _remove_from_memory(self, goal_id: UUID) -> None:
        """Remove goal entries from memory system"""
        # Note: This is a basic implementation. A more sophisticated version
        # might archive instead of delete, or handle clean-up of related entries.
        query = f"goal_state AND goal_id:{str(goal_id)}"
        await self.memory.delete_entries(query)
