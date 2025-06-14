#!/usr/bin/env python3
"""
Basic test for the Goal Engine functionality.
"""

import asyncio
import logging
from unittest.mock import MagicMock

from src.kortana.core.goals.engine import GoalEngine
from src.kortana.core.goals.generator import GoalGenerator
from src.kortana.core.goals.goal import Goal, GoalStatus, GoalType
from src.kortana.core.goals.manager import GoalManager
from src.kortana.core.goals.prioritizer import GoalPrioritizer
from src.kortana.core.goals.scanner import EnvironmentalScanner

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_goal_engine_basic():
    """Test basic Goal Engine functionality."""
    print("🧠 Testing Goal Engine Basic Functionality")
    print("=" * 50)

    try:
        # Create mock dependencies
        goal_manager = MagicMock(spec=GoalManager)
        environmental_scanner = MagicMock(spec=EnvironmentalScanner)
        goal_generator = MagicMock(spec=GoalGenerator)
        goal_prioritizer = MagicMock(spec=GoalPrioritizer)
        planning_engine = MagicMock()
        execution_engine = MagicMock()

        # Setup mock returns
        environmental_scanner.scan_environment.return_value = [
            "Optimize code performance",
            "Update documentation",
            "Fix type annotations"
        ]

        # Create mock goals
        mock_goals = [
            Goal(
                type=GoalType.OPTIMIZATION,
                description="Optimize code performance",
                priority=5
            ),
            Goal(
                type=GoalType.MAINTENANCE,
                description="Update documentation",
                priority=3
            ),
            Goal(
                type=GoalType.DEVELOPMENT,
                description="Fix type annotations",
                priority=4
            )
        ]

        goal_generator.generate_goals.return_value = mock_goals
        goal_prioritizer.prioritize_goals.return_value = mock_goals
        planning_engine.create_plan_for_goal.return_value = [
            {"action_type": "READ_FILE", "parameters": {"file_path": "test.py"}},
            {"action_type": "REASONING_COMPLETE", "parameters": {"final_summary": "Task completed"}}
        ]

        execution_engine.read_file.return_value = {"success": True, "content": "test content"}
        goal_manager.update_goal.return_value = None

        # Initialize Goal Engine
        goal_engine = GoalEngine(
            goal_manager=goal_manager,
            environmental_scanner=environmental_scanner,
            goal_generator=goal_generator,
            goal_prioritizer=goal_prioritizer,
            planning_engine=planning_engine,
            execution_engine=execution_engine
        )

        print("✅ Goal Engine initialized successfully")

        # Test run_cycle
        print("\n🔄 Testing Goal Engine cycle...")
        result = await goal_engine.run_cycle()

        print(f"✅ Goal Engine cycle completed, processed {len(result)} goals")

        # Verify calls were made
        environmental_scanner.scan_environment.assert_called_once()
        goal_generator.generate_goals.assert_called_once()
        goal_prioritizer.prioritize_goals.assert_called_once()

        print("\n🎉 Goal Engine basic functionality test PASSED!")
        return True

    except Exception as e:
        print(f"\n❌ Goal Engine test FAILED: {e}")
        logger.exception("Goal Engine test failed")
        return False

async def test_goal_creation():
    """Test basic goal creation."""
    print("\n🎯 Testing Goal Creation")
    print("-" * 30)

    try:
        # Create a goal
        goal = Goal(
            type=GoalType.AUTONOMOUS,
            description="Test autonomous goal creation",
            priority=5
        )

        print(f"✅ Created goal: {goal.id}")
        print(f"   Type: {goal.type.value}")
        print(f"   Description: {goal.description}")
        print(f"   Status: {goal.status.value}")
        print(f"   Priority: {goal.priority}")

        # Test goal status update
        goal.update_status(GoalStatus.IN_PROGRESS)
        print(f"✅ Updated status to: {goal.status.value}")

        return True

    except Exception as e:
        print(f"❌ Goal creation test FAILED: {e}")
        return False

async def main():
    """Main test function."""
    print("🚀 Starting Goal Engine Test Suite")
    print("=" * 60)

    results = []

    # Test 1: Goal Creation
    results.append(await test_goal_creation())

    # Test 2: Goal Engine Basic Functionality
    results.append(await test_goal_engine_basic())

    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)

    passed = sum(results)
    total = len(results)

    print(f"Tests Passed: {passed}/{total}")

    if passed == total:
        print("🎉 ALL TESTS PASSED - Goal Engine is functional!")
        return 0
    else:
        print("❌ Some tests failed - Goal Engine needs attention")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
