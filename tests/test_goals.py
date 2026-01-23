"""
Tests for Kor'tana's Goal Framework components.
"""

import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock

import pytest

from kortana.core.goals import Goal, GoalStatus, GoalType
from kortana.core.goals.covenant import GoalCovenantValidator
from kortana.core.goals.manager import GoalManager


@pytest.fixture
def memory_manager():
    """Mock memory manager for testing"""
    mock = AsyncMock()
    mock.store_entry = AsyncMock()
    mock.search_entries = AsyncMock(return_value=[])
    mock.delete_entries = AsyncMock()
    return mock


@pytest.fixture
def covenant_enforcer():
    """Mock covenant enforcer for testing"""
    mock = AsyncMock()
    mock.validate_action = AsyncMock(return_value=(True, "Test validation passed"))
    mock.evaluate_sacred_alignment = AsyncMock(
        return_value={"wisdom": 0.8, "compassion": 0.7, "truth": 0.9}
    )
    return mock


@pytest.fixture
def goal_manager(memory_manager, covenant_enforcer):
    """Create GoalManager instance for testing"""
    return GoalManager(memory_manager, covenant_enforcer)


@pytest.fixture
def goal_validator(covenant_enforcer):
    """Create GoalCovenantValidator instance for testing"""
    return GoalCovenantValidator(covenant_enforcer)


class TestGoal:
    """Tests for the Goal dataclass"""

    def test_goal_creation(self):
        """Test basic goal creation and defaults"""
        goal = Goal(type=GoalType.DEVELOPMENT, description="Test goal")

        assert goal.type == GoalType.DEVELOPMENT
        assert goal.description == "Test goal"
        assert goal.status == GoalStatus.PENDING
        assert goal.progress == 0.0
        assert isinstance(goal.id, uuid.UUID)
        assert isinstance(goal.created_at, datetime)
        assert goal.created_at.tzinfo == UTC

    def test_update_status(self):
        """Test goal status updates"""
        goal = Goal(type=GoalType.LEARNING, description="Test status updates")

        # Test status transition
        goal.update_status(GoalStatus.IN_PROGRESS)
        assert goal.status == GoalStatus.IN_PROGRESS
        assert goal.completed_at is None

        # Test completion
        goal.update_status(GoalStatus.COMPLETED)
        assert goal.status == GoalStatus.COMPLETED
        assert isinstance(goal.completed_at, datetime)
        assert goal.progress == 1.0

    def test_sacred_scores(self):
        """Test Sacred Trinity alignment score updates"""
        goal = Goal(type=GoalType.COVENANT, description="Test alignment")

        goal.update_sacred_scores(wisdom=0.8, compassion=0.7, truth=0.9)
        assert goal.wisdom_score == 0.8
        assert goal.compassion_score == 0.7
        assert goal.truth_score == 0.9

        # Test score clamping
        goal.update_sacred_scores(wisdom=1.5, compassion=-0.1, truth=0.5)
        assert goal.wisdom_score == 1.0
        assert goal.compassion_score == 0.0
        assert goal.truth_score == 0.5


class TestGoalManager:
    """Tests for the GoalManager class"""

    @pytest.mark.asyncio
    async def test_create_goal(self, goal_manager):
        """Test goal creation through manager"""
        goal = await goal_manager.create_goal(
            type=GoalType.DEVELOPMENT,
            description="Test managed goal",
            priority=3,
        )

        assert isinstance(goal, Goal)
        assert goal.id in goal_manager.active_goals
        assert goal.type == GoalType.DEVELOPMENT
        assert goal.priority == 3
        assert goal.covenant_approval is True

        # Verify memory persistence
        goal_manager.memory.store_entry.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_goal(self, goal_manager):
        """Test goal updates through manager"""
        goal = await goal_manager.create_goal(
            type=GoalType.MAINTENANCE,
            description="Test updates",
        )

        # Update goal status
        goal.update_status(GoalStatus.IN_PROGRESS)
        updated = await goal_manager.update_goal(goal)

        assert updated.status == GoalStatus.IN_PROGRESS
        assert goal_manager.memory.store_entry.call_count == 2

    @pytest.mark.asyncio
    async def test_parent_child_goals(self, goal_manager):
        """Test parent-child goal relationships"""
        parent = await goal_manager.create_goal(
            type=GoalType.INTEGRATION,
            description="Parent goal",
        )

        child = await goal_manager.create_goal(
            type=GoalType.DEVELOPMENT,
            description="Child goal",
            parent_id=parent.id,
        )

        assert child.parent_goal_id == parent.id
        assert child.id in parent.child_goal_ids

        # List child goals
        children = await goal_manager.get_child_goals(parent.id)
        assert len(children) == 1
        assert children[0].id == child.id


class TestGoalCovenantValidator:
    """Tests for the GoalCovenantValidator"""

    @pytest.mark.asyncio
    async def test_validate_goal(self, goal_validator):
        """Test goal validation against Sacred Covenant"""
        goal = Goal(
            type=GoalType.AUTONOMOUS,
            description="Test goal validation",
            success_criteria=["Must pass covenant check"],
        )

        is_valid, feedback = await goal_validator.validate_goal(goal)
        assert is_valid is True
        assert feedback is not None
        assert goal.wisdom_score == 0.8
        assert goal.compassion_score == 0.7
        assert goal.truth_score == 0.9

    def test_get_recommendations(self, goal_validator):
        """Test alignment improvement recommendations"""
        goal = Goal(type=GoalType.DEVELOPMENT, description="Test recommendations")
        goal.update_sacred_scores(wisdom=0.5, compassion=0.8, truth=0.6)

        recommendations = goal_validator.get_alignment_recommendations(goal)
        assert "wisdom" in recommendations
        assert len(recommendations["wisdom"]) > 0  # Should have wisdom recommendations
        assert (
            len(recommendations["compassion"]) == 0
        )  # No compassion recommendations needed
        assert len(recommendations["truth"]) > 0  # Should have truth recommendations
