"""
Transparency Service for Kor'tana
Provides transparency reports and analytics
"""

from typing import Any

from .decision_logger import EthicalDecisionLogger, EthicalDecisionType


class TransparencyService:
    """Service for generating transparency reports"""

    def __init__(self, logger: EthicalDecisionLogger):
        self.logger = logger

    def generate_report(self) -> dict[str, Any]:
        """
        Generate comprehensive transparency report

        Returns:
            Dictionary containing transparency metrics
        """
        decisions = self.logger.get_all_decisions()

        # Count by type
        type_counts = {}
        for decision_type in EthicalDecisionType:
            type_counts[decision_type.value] = sum(
                1 for d in decisions if d["decision_type"] == decision_type
            )

        # Calculate average confidence
        avg_confidence = (
            sum(d["confidence"] for d in decisions) / len(decisions)
            if decisions
            else 0
        )

        # Count feedback
        feedback_count = sum(1 for d in decisions if d["feedback"] is not None)

        return {
            "total_decisions": len(decisions),
            "decisions_by_type": type_counts,
            "average_confidence": avg_confidence,
            "feedback_received": feedback_count,
            "feedback_rate": feedback_count / len(decisions) if decisions else 0,
        }

    def get_decision_breakdown(self) -> dict[str, Any]:
        """
        Get detailed breakdown of decisions

        Returns:
            Breakdown of decisions by type
        """
        decisions = self.logger.get_all_decisions()
        breakdown = {}

        for decision_type in EthicalDecisionType:
            type_decisions = [
                d for d in decisions if d["decision_type"] == decision_type
            ]
            breakdown[decision_type.value] = {
                "count": len(type_decisions),
                "recent": type_decisions[-5:] if type_decisions else [],
            }

        return breakdown
