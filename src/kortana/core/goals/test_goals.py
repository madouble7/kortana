import asyncio
import unittest
from unittest.mock import Mock

from kortana.core.goals.engine import GoalEngine
from kortana.core.goals.generator import GoalGenerator
from kortana.core.goals.goal import Goal, GoalType
from kortana.core.goals.prioritizer import GoalPrioritizer
from kortana.core.goals.scanner import EnvironmentalScanner


class TestEnvironmentalScanner(unittest.TestCase):
    def test_scan_environment(self):
        scanner = EnvironmentalScanner()
        goals = asyncio.run(scanner.scan_environment())
        self.assertIsInstance(goals, list)
        self.assertGreater(len(goals), 0)


class TestGoalGenerator(unittest.TestCase):
    def test_generate_goals(self):
        mock_goal_manager = Mock()
        generator = GoalGenerator(goal_manager=mock_goal_manager)
        raw_goals = ["Fix bug in module X", "Implement feature Y"]
        goals = asyncio.run(generator.generate_goals(raw_goals))
        self.assertEqual(len(goals), len(raw_goals))
        self.assertIsInstance(goals[0], Goal)


class TestGoalPrioritizer(unittest.TestCase):
    def test_prioritize_goals(self):
        prioritizer = GoalPrioritizer()
        goals = [
            Goal(type=GoalType.DEVELOPMENT, description="Test goal", priority=2),
            Goal(type=GoalType.DEVELOPMENT, description="Another goal", priority=1),
        ]
        prioritized_goals = asyncio.run(prioritizer.prioritize_goals(goals))
        self.assertEqual(prioritized_goals[0].priority, 2)


class TestGoalEngine(unittest.TestCase):
    def test_run_cycle(self):
        mock_goal_manager = Mock()
        mock_scanner = Mock()
        mock_generator = Mock()
        mock_prioritizer = Mock()
        engine = GoalEngine(
            goal_manager=mock_goal_manager,
            environmental_scanner=mock_scanner,
            goal_generator=mock_generator,
            goal_prioritizer=mock_prioritizer,
        )
        goals = asyncio.run(engine.run_cycle())
        self.assertIsInstance(goals, list)


if __name__ == "__main__":
    unittest.main()
