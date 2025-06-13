"""
Goal Prioritizer for Kor'tana's Goal Framework.

This component is responsible for evaluating generated goals and assigning
them a priority based on various factors, including Sacred Trinity alignment.
"""

import logging
from datetime import UTC, datetime

from .goal import Goal, GoalStatus, GoalType

logger = logging.getLogger(__name__)


class GoalPrioritizer:
    """
    Prioritizes a list of goals based on multiple factors and weighting systems.
    """

    def __init__(self) -> None:
        """Initialize the GoalPrioritizer."""
        logger.info("GoalPrioritizer initialized.")

        # Define priority weights for different factors
        # These could be made configurable in the future
        self.weights = {
            "explicit_priority": 0.35,  # User/creator-assigned priority
            "sacred_alignment": 0.25,  # Sacred Trinity alignment scores
            "goal_type_weight": 0.15,  # Weight based on goal type
            "dependencies": 0.10,  # Dependency relationships
            "blockers": -0.10,  # Negative weight for blocked goals
            "staleness": 0.05,  # Time since creation/last update
            "progress": 0.10,  # Current progress (prioritize nearly complete)
        }

        # Configure goal type weights (some types may be inherently higher priority)
        self.type_weights = {
            GoalType.DEVELOPMENT: 0.5,
            GoalType.LEARNING: 0.3,
            GoalType.OPTIMIZATION: 0.6,
            GoalType.MAINTENANCE: 0.7,
            GoalType.ASSISTANCE: 0.8,
            GoalType.INTEGRATION: 0.6,
            GoalType.AUTONOMOUS: 0.4,
            GoalType.COVENANT: 0.9,  # Sacred Covenant goals are high priority
        }

    async def prioritize_goals(self, goals: list[Goal]) -> list[Goal]:
        """
        Prioritizes a list of goals based on multiple factors.

        The prioritization algorithm considers:
        - Explicit priority (1-5) set during goal creation
        - Sacred Trinity alignment scores (wisdom, compassion, truth)
        - Goal dependencies and blockers
        - Goal type importance
        - Time-based factors (staleness, deadlines)
        - Current progress toward completion

        Args:
            goals: A list of Goal objects to prioritize.

        Returns:
            A list of Goal objects sorted by computed priority (highest first).
        """
        logger.info(f"Prioritizing {len(goals)} goals...")
        if not goals:
            logger.info("No goals to prioritize.")
            return []

        # Calculate a composite score for each goal
        scored_goals: list[tuple[Goal, float]] = []

        for goal in goals:
            # Skip goals that are completed, failed, or abandoned
            if goal.status in [
                GoalStatus.COMPLETED,
                GoalStatus.FAILED,
                GoalStatus.ABANDONED,
            ]:
                continue

            # Calculate composite score based on weighted factors
            score = self._calculate_goal_score(goal, goals)
            scored_goals.append((goal, score))

            logger.debug(f"Goal '{goal.description[:30]}...' score: {score:.2f}")

        # Sort by computed score (descending)
        prioritized_goals = [
            g[0] for g in sorted(scored_goals, key=lambda x: x[1], reverse=True)
        ]
        logger.info(f"Finished prioritizing {len(prioritized_goals)} goals.")
        return prioritized_goals

    def _calculate_goal_score(self, goal: Goal, all_goals: list[Goal]) -> float:
        """Calculate a composite priority score for a single goal."""
        scores: dict[str, float] = {}

        # 1. Explicit priority (1-5, normalized to 0-1)
        scores["explicit_priority"] = (goal.priority - 1) / 4.0

        # 2. Sacred Trinity alignment (average of the three scores)
        trinity_avg = (
            goal.wisdom_score + goal.compassion_score + goal.truth_score
        ) / 3.0
        scores["sacred_alignment"] = trinity_avg

        # 3. Goal type priority
        scores["goal_type_weight"] = self.type_weights.get(goal.type, 0.5)

        # 4. Dependencies (goals with dependents are higher priority)
        dependent_count = len(goal.dependent_goal_ids)
        scores["dependencies"] = min(1.0, dependent_count / 5.0)  # Cap at 1.0

        # 5. Blockers (blocked goals get penalty)
        blocker_penalty = (
            1.0 if not goal.blockers else max(0.0, 1.0 - (len(goal.blockers) * 0.2))
        )
        scores["blockers"] = blocker_penalty

        # 6. Staleness (older goals get boost if not worked on)
        days_since_update = (datetime.now(UTC) - goal.updated_at).days
        staleness_score = min(1.0, days_since_update / 14.0)  # 2 weeks = max staleness
        scores["staleness"] = staleness_score

        # 7. Progress (nearly complete goals get boost)
        progress_score = 0.0
        if goal.progress > 0.7:  # Boost goals that are >70% complete
            progress_score = goal.progress
        elif goal.progress < 0.1:  # Also boost goals just getting started
            progress_score = 0.7  # Give these a decent score too
        else:
            progress_score = 0.5  # Middle progress gets middle score
        scores["progress"] = progress_score

        # Apply weights to each factor and sum
        weighted_score = sum(scores[key] * self.weights[key] for key in scores)

        # Apply status-based adjustments
        if goal.status == GoalStatus.BLOCKED:
            weighted_score *= 0.5  # Reduce priority of blocked goals
        elif goal.status == GoalStatus.IN_PROGRESS:
            weighted_score *= 1.2  # Boost in-progress goals
        elif goal.status == GoalStatus.NEEDS_REVIEW:
            weighted_score *= 1.1  # Slight boost for review-ready goals

        return weighted_score


# Example usage (for testing/demonstration)
# async def main():
#     # Assuming you have a list of Goal objects
#     # from .goal import Goal, GoalType, GoalStatus
#     # goal1 = Goal(type=GoalType.DEVELOPMENT, description="Implement feature X", priority=5)
#     # goal2 = Goal(type=GoalType.MAINTENANCE, description="Fix bug Y", priority=3)
#     # goals_list = [goal1, goal2]
#     # prioritizer = GoalPrioritizer()
#     # prioritized = await prioritizer.prioritize_goals(goals_list)
#     # print("Prioritized Goals:")
#     # for goal in prioritized:
#     #     print(f"- {goal.description} (Priority: {goal.priority})")

# if __name__ == "__main__":
#     import asyncio
#     # asyncio.run(main())
