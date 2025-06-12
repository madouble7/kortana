"""
Tests for the Goal Engine
"""

from datetime import datetime
from unittest.mock import patch

import pytest

from kortana.core.goal_engine import Goal, GoalEngine, GoalType


@pytest.fixture
def goal_engine():
    return GoalEngine()


def test_goal_creation():
    goal = Goal(
        id="test_1",
        type=GoalType.MAINTENANCE,
        title="Test Goal",
        description="Test Description",
        priority=1,
        created_at=datetime.now(),
    )
    assert goal.id == "test_1"
    assert goal.type == GoalType.MAINTENANCE
    assert goal.status == "pending"


@patch("kortana.core.goal_engine.execution_engine")
def test_scan_project_files(mock_execution_engine, goal_engine):
    mock_execution_engine.list_directory.return_value = {
        "success": True,
        "items": [{"type": "file", "name": "test.py"}],
    }
    mock_execution_engine.read_file.return_value = {
        "success": True,
        "content": "def test1():\npass\n" * 11,  # 11 function definitions
    }

    result = goal_engine._scan_project_files()
    assert result["needs_optimization"]
    assert "test.py" in result["high_complexity_files"]


@patch("kortana.core.goal_engine.execution_engine")
def test_scan_system_performance(mock_execution_engine, goal_engine):
    mock_execution_engine.execute_shell_command.side_effect = [
        {"success": True, "stdout": "LoadPercentage\n75\n"},
        {
            "success": True,
            "stdout": "FreePhysicalMemory TotalVisibleMemorySize\n4000000 8000000",
        },
    ]

    metrics = goal_engine._scan_system_performance()
    assert isinstance(metrics["cpu_usage"], (int, float))
    assert isinstance(metrics["memory_usage"], (int, float))


@patch("kortana.core.goal_engine.memory_manager")
def test_identify_research_opportunities(mock_memory_manager, goal_engine):
    mock_memory_manager.get_recent_interactions.return_value = [
        "I don't know about quantum computing",
        "I'm not sure about neural architecture search",
    ]

    topics = goal_engine._identify_research_opportunities()
    assert len(topics) <= 5
    assert any("quantum computing" in topic for topic in topics)


@patch("kortana.core.goal_engine.execution_engine")
@patch("kortana.core.goal_engine.memory_manager")
def test_scan_environment(mock_memory_manager, mock_execution_engine, goal_engine):
    # Setup mocks
    mock_execution_engine.list_directory.return_value = {
        "success": True,
        "items": [{"type": "file", "name": "complex.py"}],
    }
    mock_execution_engine.read_file.return_value = {
        "success": True,
        "content": "def test():\npass\n" * 15,
    }
    mock_execution_engine.execute_shell_command.side_effect = [
        {"success": True, "stdout": "LoadPercentage\n90\n"},
        {
            "success": True,
            "stdout": "FreePhysicalMemory TotalVisibleMemorySize\n1000000 10000000",
        },
    ]
    mock_memory_manager.get_recent_interactions.return_value = [
        "I don't know about reinforcement learning"
    ]

    goals = goal_engine.scan_environment()
    assert len(goals) > 0
    assert any(goal.type == GoalType.OPTIMIZATION for goal in goals)
    assert any(goal.type == GoalType.MAINTENANCE for goal in goals)
    assert any(goal.type == GoalType.RESEARCH for goal in goals)


if __name__ == "__main__":
    pytest.main([__file__])
