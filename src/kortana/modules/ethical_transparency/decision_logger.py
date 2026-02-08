"""
Ethical Decision Logger for Kor'tana
Logs ethical decisions and reasoning
"""

import uuid
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any


class EthicalDecisionType(StrEnum):
    CONTENT_MODERATION = "content_moderation"
    PRIVACY_PROTECTION = "privacy_protection"
    BIAS_MITIGATION = "bias_mitigation"
    TRANSPARENCY = "transparency"
    FAIRNESS = "fairness"


class EthicalDecision:
    """Represents an ethical decision"""

    def __init__(
        self,
        decision_type: EthicalDecisionType,
        context: str,
        decision: str,
        reasoning: str,
        confidence: float = 0.8,
    ):
        self.id = str(uuid.uuid4())
        self.timestamp = datetime.now(UTC).isoformat()
        self.decision_type = decision_type
        self.context = context
        self.decision = decision
        self.reasoning = reasoning
        self.confidence = confidence
        self.feedback: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "timestamp": self.timestamp,
            "decision_type": self.decision_type,
            "context": self.context,
            "decision": self.decision,
            "reasoning": self.reasoning,
            "confidence": self.confidence,
            "feedback": self.feedback,
        }

    def add_feedback(self, feedback: str):
        """Add user feedback to the decision"""
        self.feedback = feedback


class EthicalDecisionLogger:
    """Service for logging ethical decisions"""

    def __init__(self):
        self.decisions: list[EthicalDecision] = []

    def log_decision(
        self,
        decision_type: EthicalDecisionType,
        context: str,
        decision: str,
        reasoning: str,
        confidence: float = 0.8,
    ) -> str:
        """
        Log an ethical decision

        Args:
            decision_type: Type of ethical decision
            context: Context in which decision was made
            decision: The decision made
            reasoning: Reasoning behind the decision
            confidence: Confidence level (0-1)

        Returns:
            Decision ID
        """
        ethical_decision = EthicalDecision(
            decision_type, context, decision, reasoning, confidence
        )
        self.decisions.append(ethical_decision)
        return ethical_decision.id

    def get_decision(self, decision_id: str) -> EthicalDecision | None:
        """Get a decision by ID"""
        for decision in self.decisions:
            if decision.id == decision_id:
                return decision
        return None

    def get_all_decisions(self) -> list[dict[str, Any]]:
        """Get all logged decisions"""
        return [d.to_dict() for d in self.decisions]

    def get_recent_decisions(self, limit: int = 10) -> list[dict[str, Any]]:
        """Get most recent decisions"""
        return [d.to_dict() for d in self.decisions[-limit:]]

    def add_feedback(self, decision_id: str, feedback: str) -> bool:
        """
        Add feedback to a decision

        Args:
            decision_id: ID of the decision
            feedback: User feedback

        Returns:
            True if successful, False otherwise
        """
        decision = self.get_decision(decision_id)
        if decision:
            decision.add_feedback(feedback)
            return True
        return False
