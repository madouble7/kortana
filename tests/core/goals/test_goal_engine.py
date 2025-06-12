"""
Unit tests for Kor'tana's Goal Engine components.
"""

from unittest.mock import AsyncMock, MagicMock

import pytest

from kortana.core.goals.engine import GoalEngine
from kortana.core.goals.generator import GoalGenerator
from kortana.core.goals.goal import Goal, GoalType
from kortana.core.goals.manager import GoalManager
from kortana.core.goals.prioritizer import GoalPrioritizer
from kortana.core.goals.scanner import EnvironmentalScanner


# Mock dependencies
class MockMemoryManager(AsyncMock):
    async def store_entry(self, entry):
        pass

    async def search_entries(self, query, limit=None):
        return []

    async def delete_entries(self, query):
        pass


class MockCovenantEnforcer(AsyncMock):
    async def validate_action(self, action_type, context):
        return True, "Approved"

    async def evaluate_sacred_alignment(self, description):
        return {"wisdom": 0.8, "compassion": 0.9, "truth": 0.7}


class MockLLMClient(AsyncMock):
    async def generate_content(self, prompt, **kwargs):
        # Simulate LLM response for goal generation
        # In a real test, this would parse the prompt and return structured data
        return MagicMock(text="Mock generated goal details")


@pytest.fixture
def mock_memory_manager():
    return MockMemoryManager()


@pytest.fixture
def mock_covenant_enforcer():
    return MockCovenantEnforcer()


@pytest.fixture
def mock_llm_client():
    return MockLLMClient()


@pytest.fixture
def goal_manager(mock_memory_manager, mock_covenant_enforcer):
    # GoalManager needs a real DB session in its __init__, but the methods we mock don't use it.
    # We can pass a dummy object or refactor GoalManager init if needed for more comprehensive tests.
    # For now, let's mock the methods that interact with memory/covenant.
    manager = GoalManager(mock_memory_manager, mock_covenant_enforcer)
    # Mock internal methods that interact with dependencies
    manager._validate_with_covenant = AsyncMock(return_value=(True, "Approved"))
    manager._persist_to_memory = AsyncMock()
    manager._load_from_memory = AsyncMock(
        return_value=None
    )  # Assume no goals in memory initially
    manager._remove_from_memory = AsyncMock()
    return manager


@pytest.fixture
def environmental_scanner():
    return EnvironmentalScanner()


@pytest.fixture
def goal_generator(goal_manager, mock_llm_client):
    return GoalGenerator(goal_manager, mock_llm_client)


@pytest.fixture
def goal_prioritizer():
    return GoalPrioritizer()


@pytest.fixture
def goal_engine(goal_manager, environmental_scanner, goal_generator, goal_prioritizer):
    # Mock ADE dependency if GoalEngine requires it for execution phase
    mock_ade = AsyncMock()
    engine = GoalEngine(
        goal_manager, environmental_scanner, goal_generator, goal_prioritizer
    )
    # engine.ade = mock_ade # Uncomment if ADE is added to GoalEngine init
    return engine


# Test cases


@pytest.mark.asyncio
async def test_environmental_scanner_scan_environment(environmental_scanner):
    """Test that the scanner returns a list of strings."""
    potential_goals = await environmental_scanner.scan_environment()
    assert isinstance(potential_goals, list)
    assert all(isinstance(goal, str) for goal in potential_goals)
    assert len(potential_goals) > 0  # Assuming placeholder returns at least one


@pytest.mark.asyncio
async def test_goal_generator_generate_goals(goal_generator, goal_manager):
    """Test that the generator creates Goal objects."""
    descriptions = ["Test goal 1", "Test goal 2"]
    # Mock the create_goal method to return dummy Goal objects
    goal_manager.create_goal.side_effect = (
        lambda type,
        description,
        priority,
        parent_id=None,
        created_by="kor_tana",
        success_criteria=None: Goal(
            type=type,
            description=description,
            priority=priority,
            success_criteria=success_criteria or [],
        )
    )

    generated_goals = await goal_generator.generate_goals(descriptions)

    assert isinstance(generated_goals, list)
    assert len(generated_goals) == len(descriptions)
    assert all(isinstance(goal, Goal) for goal in generated_goals)
    # Verify create_goal was called for each description
    assert goal_manager.create_goal.call_count == len(descriptions)


@pytest.mark.asyncio
async def test_goal_prioritizer_prioritize_goals(goal_prioritizer):
    """Test that the prioritizer sorts goals correctly."""
    goal1 = Goal(type=GoalType.DEVELOPMENT, description="Low priority", priority=1)
    goal2 = Goal(type=GoalType.MAINTENANCE, description="High priority", priority=5)
    goal3 = Goal(type=GoalType.OPTIMIZATION, description="Medium priority", priority=3)
    goals_list = [goal1, goal2, goal3]

    prioritized_goals = await goal_prioritizer.prioritize_goals(goals_list)

    assert isinstance(prioritized_goals, list)
    assert len(prioritized_goals) == len(goals_list)
    # Check if sorted by priority (descending)
    assert prioritized_goals[0].priority >= prioritized_goals[1].priority
    assert prioritized_goals[1].priority >= prioritized_goals[2].priority
    assert prioritized_goals[0] == goal2  # Highest priority
    assert prioritized_goals[2] == goal1  # Lowest priority


@pytest.mark.asyncio
async def test_goal_engine_run_cycle(goal_engine):
    """Test the main goal engine cycle orchestration."""
    # Mock the methods of the components the engine calls
    goal_engine.scanner.scan_environment = AsyncMock(return_value=["Desc1", "Desc2"])
    # Mock generator to return dummy Goal objects
    dummy_goals = [
        Goal(type=GoalType.DEVELOPMENT, description="Dummy", priority=1),
        Goal(type=GoalType.DEVELOPMENT, description="Dummy", priority=2),
    ]
    goal_engine.generator.generate_goals = AsyncMock(return_value=dummy_goals)
    goal_engine.prioritizer.prioritize_goals = AsyncMock(
        return_value=sorted(dummy_goals, key=lambda g: g.priority, reverse=True)
    )

    processed_goals = await goal_engine.run_cycle()

    # Verify that each component's method was called
    goal_engine.scanner.scan_environment.assert_called_once()
    goal_engine.generator.generate_goals.assert_called_once_with(["Desc1", "Desc2"])
    goal_engine.prioritizer.prioritize_goals.assert_called_once_with(dummy_goals)

    assert isinstance(processed_goals, list)
    assert len(processed_goals) == len(dummy_goals)
    assert all(isinstance(goal, Goal) for goal in processed_goals)


@pytest.mark.asyncio
async def test_goal_engine_run_cycle_no_potential_goals(goal_engine):
    """Test run_cycle when scanner finds no potential goals."""
    goal_engine.scanner.scan_environment = AsyncMock(return_value=[])
    goal_engine.generator.generate_goals = AsyncMock()
    goal_engine.prioritizer.prioritize_goals = AsyncMock()

    processed_goals = await goal_engine.run_cycle()

    goal_engine.scanner.scan_environment.assert_called_once()
    goal_engine.generator.generate_goals.assert_not_called()
    goal_engine.prioritizer.prioritize_goals.assert_not_called()

    assert isinstance(processed_goals, list)
    assert len(processed_goals) == 0


@pytest.mark.asyncio
async def test_goal_engine_run_cycle_no_generated_goals(goal_engine):
    """Test run_cycle when generator creates no goals."""
    goal_engine.scanner.scan_environment = AsyncMock(return_value=["Desc1"])
    goal_engine.generator.generate_goals = AsyncMock(return_value=[])
    goal_engine.prioritizer.prioritize_goals = AsyncMock()

    processed_goals = await goal_engine.run_cycle()

    goal_engine.scanner.scan_environment.assert_called_once()
    goal_engine.generator.generate_goals.assert_called_once_with(["Desc1"])
    goal_engine.prioritizer.prioritize_goals.assert_not_called()

    assert isinstance(processed_goals, list)
    assert len(processed_goals) == 0
