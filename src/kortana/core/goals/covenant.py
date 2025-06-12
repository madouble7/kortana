"""
Sacred Covenant integration for goal validation and alignment scoring.
"""

import logging

from ..covenant import CovenantEnforcer
from .goal import Goal


class GoalCovenantValidator:
    """
    Handles Sacred Covenant validation and alignment scoring for goals.
    Acts as a bridge between the Goal Framework and core Covenant system.
    """

    def __init__(self, covenant: CovenantEnforcer):
        self.logger = logging.getLogger(__name__)
        self.covenant = covenant

    async def validate_goal(self, goal: Goal) -> tuple[bool, str | None]:
        """
        Validate a goal against Sacred Covenant principles.
        Returns (is_valid, feedback) tuple.
        """
        # Build validation context
        context = {
            "goal_type": goal.type.value,
            "description": goal.description,
            "created_by": goal.created_by,
            "priority": goal.priority,
            "success_criteria": goal.success_criteria,
        }

        try:
            # Check basic covenant compliance
            is_valid, feedback = await self.covenant.validate_action(
                action_type="create_goal",
                context=context,
            )

            if not is_valid:
                self.logger.warning(f"Goal validation failed: {feedback}")
                return False, feedback

            # Evaluate alignment with Sacred Trinity principles
            alignment = await self.evaluate_alignment(goal)

            # Get individual scores
            wisdom = alignment.get("wisdom", 0.0)
            compassion = alignment.get("compassion", 0.0)
            truth = alignment.get("truth", 0.0)

            # Update goal's alignment scores
            goal.update_sacred_scores(wisdom, compassion, truth)

            # Calculate weighted average for overall score
            # Weights could be adjusted based on goal type/context
            total_score = (wisdom + compassion + truth) / 3.0

            # Goal must meet minimum alignment threshold
            MIN_ALIGNMENT = 0.6  # 60% minimum alignment required
            if total_score < MIN_ALIGNMENT:
                msg = (
                    f"Goal alignment scores too low (total: {total_score:.1%}). "
                    f"Requires stronger alignment with Sacred Trinity principles."
                )
                return False, msg

            success_msg = (
                f"Goal validated with alignment scores - "
                f"Wisdom: {wisdom:.1%}, "
                f"Compassion: {compassion:.1%}, "
                f"Truth: {truth:.1%}"
            )
            return True, success_msg

        except Exception as e:
            error_msg = f"Error during goal validation: {str(e)}"
            self.logger.error(error_msg)
            return False, error_msg

    async def evaluate_alignment(self, goal: Goal) -> dict[str, float]:
        """
        Evaluate how well a goal aligns with Sacred Trinity principles.
        Returns scores for wisdom, compassion, and truth (0-1 scale).
        """
        try:
            alignment = await self.covenant.evaluate_sacred_alignment(
                content=goal.description,
                context={
                    "goal_type": goal.type.value,
                    "success_criteria": goal.success_criteria,
                },
            )

            # Ensure we have all three scores
            alignment.setdefault("wisdom", 0.0)
            alignment.setdefault("compassion", 0.0)
            alignment.setdefault("truth", 0.0)

            return alignment

        except Exception as e:
            self.logger.error(f"Error evaluating goal alignment: {str(e)}")
            # Return zero scores on error
            return {"wisdom": 0.0, "compassion": 0.0, "truth": 0.0}

    def get_alignment_recommendations(self, goal: Goal) -> dict[str, list]:
        """
        Get recommendations for improving goal alignment with Sacred Trinity.
        Returns dict with improvement suggestions for each principle.
        """
        recommendations = {"wisdom": [], "compassion": [], "truth": []}

        # Wisdom recommendations
        if goal.wisdom_score < 0.7:
            recommendations["wisdom"].extend(
                [
                    "Consider long-term implications and learning opportunities",
                    "Add explicit knowledge-sharing or documentation components",
                    "Include mechanisms for gathering and applying insights",
                ]
            )

        # Compassion recommendations
        if goal.compassion_score < 0.7:
            recommendations["compassion"].extend(
                [
                    "Consider impact on users and stakeholders",
                    "Add empathy-driven success criteria",
                    "Include user experience and accessibility aspects",
                ]
            )

        # Truth recommendations
        if goal.truth_score < 0.7:
            recommendations["truth"].extend(
                [
                    "Add clear validation and verification criteria",
                    "Include explicit transparency measures",
                    "Define concrete metrics for measuring success",
                ]
            )

        return recommendations
