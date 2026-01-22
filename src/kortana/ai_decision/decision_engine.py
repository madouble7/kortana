"""
Decision Engine - Core ML-based decision-making system for autonomous operations

This module implements real-time decision-making strategies using machine learning,
inspired by autonomous driving systems. It evaluates multiple decision factors,
applies learned patterns, and selects optimal actions in time-sensitive scenarios.
"""

import logging
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any

import numpy as np
import torch

logger = logging.getLogger(__name__)


class DecisionUrgency(Enum):
    """Priority levels for decision-making"""

    CRITICAL = "critical"  # Immediate action required
    HIGH = "high"  # Action needed within seconds
    MEDIUM = "medium"  # Action needed within minutes
    LOW = "low"  # Can be deferred


class DecisionConfidence(Enum):
    """Confidence levels for decision outputs"""

    VERY_HIGH = "very_high"  # >95% confidence
    HIGH = "high"  # 80-95% confidence
    MEDIUM = "medium"  # 60-80% confidence
    LOW = "low"  # <60% confidence


@dataclass
class DecisionContext:
    """Context information for a decision request"""

    scenario: str
    urgency: DecisionUrgency
    constraints: dict[str, Any]
    sensor_data: dict[str, Any]
    timestamp: datetime
    historical_context: list[dict[str, Any]] | None = None


@dataclass
class DecisionOutput:
    """Output from the decision engine"""

    action: str
    confidence: DecisionConfidence
    reasoning: str
    alternatives: list[dict[str, Any]]
    risk_assessment: dict[str, float]
    execution_plan: dict[str, Any]
    timestamp: datetime


class DecisionEngine:
    """
    ML-powered decision engine for autonomous systems

    Implements a multi-factor decision-making system that:
    1. Analyzes current context and historical patterns
    2. Evaluates multiple decision options
    3. Predicts outcomes for each option
    4. Selects the optimal action based on learned strategies
    5. Provides confidence scores and risk assessments
    """

    def __init__(
        self,
        model_weights: str | None = None,
        safety_threshold: float = 0.7,
        enable_learning: bool = True,
    ):
        """
        Initialize the decision engine

        Args:
            model_weights: Path to pre-trained model weights (optional)
            safety_threshold: Minimum confidence threshold for decisions
            enable_learning: Whether to enable online learning
        """
        self.safety_threshold = safety_threshold
        self.enable_learning = enable_learning
        self.decision_history: list[dict[str, Any]] = []

        # Initialize simple neural network for decision scoring
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self._initialize_model()

        if model_weights:
            self._load_weights(model_weights)

        logger.info(
            f"Decision engine initialized (device={self.device}, "
            f"safety_threshold={safety_threshold})"
        )

    def _initialize_model(self):
        """Initialize the decision scoring neural network"""
        # Simple feedforward network for decision scoring
        # Input: context features, Output: decision scores
        self.input_size = 64  # Feature vector size
        self.hidden_size = 128
        self.output_size = 10  # Number of possible actions

        self.model = torch.nn.Sequential(
            torch.nn.Linear(self.input_size, self.hidden_size),
            torch.nn.ReLU(),
            torch.nn.Dropout(0.2),
            torch.nn.Linear(self.hidden_size, self.hidden_size),
            torch.nn.ReLU(),
            torch.nn.Dropout(0.2),
            torch.nn.Linear(self.hidden_size, self.output_size),
            torch.nn.Softmax(dim=-1),
        ).to(self.device)

        logger.debug(f"Model initialized with architecture: {self.model}")

    def _load_weights(self, weights_path: str):
        """Load pre-trained model weights"""
        try:
            self.model.load_state_dict(torch.load(weights_path, map_location=self.device))
            logger.info(f"Loaded model weights from {weights_path}")
        except Exception as e:
            logger.warning(f"Failed to load weights: {e}. Using random initialization.")

    def _extract_features(self, context: DecisionContext) -> torch.Tensor:
        """
        Extract feature vector from decision context

        Args:
            context: The decision context

        Returns:
            Feature tensor for the model
        """
        # Create a feature vector from the context
        # This is a simplified implementation - in production, this would be more sophisticated
        features = np.zeros(self.input_size)

        # Encode urgency
        urgency_map = {
            DecisionUrgency.CRITICAL: 1.0,
            DecisionUrgency.HIGH: 0.75,
            DecisionUrgency.MEDIUM: 0.5,
            DecisionUrgency.LOW: 0.25,
        }
        features[0] = urgency_map[context.urgency]

        # Encode sensor data (simplified)
        sensor_values = list(context.sensor_data.values())[:10]
        for i, value in enumerate(sensor_values):
            if isinstance(value, (int, float)):
                features[i + 1] = float(value)

        # Encode constraints
        features[15] = len(context.constraints)

        # Add timestamp features
        features[20] = context.timestamp.hour / 24.0
        features[21] = context.timestamp.minute / 60.0

        # Random features for remaining dimensions (in production, use real features)
        features[30:] = np.random.randn(self.input_size - 30) * 0.1

        return torch.FloatTensor(features).to(self.device)

    def _evaluate_decision_options(
        self, context: DecisionContext
    ) -> list[tuple[str, float, dict[str, Any]]]:
        """
        Evaluate possible decision options

        Args:
            context: Decision context

        Returns:
            List of (action, score, metadata) tuples
        """
        # Extract features
        features = self._extract_features(context).unsqueeze(0)

        # Get model predictions
        with torch.no_grad():
            scores = self.model(features).cpu().numpy()[0]

        # Define action space (simplified for demo)
        actions = [
            "proceed_cautiously",
            "accelerate",
            "decelerate",
            "stop",
            "wait_for_clearance",
            "request_assistance",
            "adjust_parameters",
            "continue_monitoring",
            "escalate_priority",
            "execute_fallback_plan",
        ]

        # Combine actions with scores
        options = []
        for i, action in enumerate(actions):
            score = float(scores[i])
            metadata = {
                "predicted_success_rate": score,
                "estimated_time": np.random.uniform(0.1, 5.0),  # Simplified
                "resource_cost": np.random.uniform(0.0, 1.0),
            }
            options.append((action, score, metadata))

        # Sort by score
        options.sort(key=lambda x: x[1], reverse=True)

        return options

    def _assess_risks(
        self, action: str, context: DecisionContext
    ) -> dict[str, float]:
        """
        Assess risks associated with a decision

        Args:
            action: The proposed action
            context: Decision context

        Returns:
            Risk assessment dictionary
        """
        # Simplified risk assessment
        base_risk = 0.1

        # Increase risk for urgent decisions
        if context.urgency == DecisionUrgency.CRITICAL:
            base_risk += 0.2

        # Risk factors
        risks = {
            "execution_failure": base_risk + np.random.uniform(0.0, 0.1),
            "resource_exhaustion": base_risk + np.random.uniform(0.0, 0.15),
            "timing_violation": base_risk + np.random.uniform(0.0, 0.1),
            "constraint_violation": base_risk + np.random.uniform(0.0, 0.12),
            "safety_concern": base_risk + np.random.uniform(0.0, 0.08),
        }

        return risks

    def _create_execution_plan(
        self, action: str, context: DecisionContext, metadata: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Create an execution plan for the selected action

        Args:
            action: Selected action
            context: Decision context
            metadata: Action metadata

        Returns:
            Execution plan
        """
        return {
            "action": action,
            "steps": [
                {"step": 1, "description": f"Prepare for {action}", "duration": 0.1},
                {"step": 2, "description": f"Execute {action}", "duration": 0.5},
                {
                    "step": 3,
                    "description": "Monitor execution",
                    "duration": metadata.get("estimated_time", 1.0),
                },
                {"step": 4, "description": "Verify completion", "duration": 0.2},
            ],
            "estimated_duration": metadata.get("estimated_time", 1.0),
            "success_criteria": ["Action completed", "No errors", "Within time limit"],
            "fallback_plan": {
                "trigger_condition": "Execution failure or timeout",
                "fallback_action": "request_assistance",
            },
        }

    def make_decision(self, context: DecisionContext) -> DecisionOutput:
        """
        Make a decision based on the given context

        Args:
            context: Decision context with scenario, urgency, constraints, etc.

        Returns:
            Decision output with action, confidence, reasoning, and execution plan
        """
        logger.info(
            f"Making decision for scenario: {context.scenario} "
            f"(urgency={context.urgency.value})"
        )

        # Evaluate options
        options = self._evaluate_decision_options(context)

        # Select best action
        best_action, best_score, best_metadata = options[0]

        # Determine confidence level
        if best_score >= 0.95:
            confidence = DecisionConfidence.VERY_HIGH
        elif best_score >= 0.80:
            confidence = DecisionConfidence.HIGH
        elif best_score >= 0.60:
            confidence = DecisionConfidence.MEDIUM
        else:
            confidence = DecisionConfidence.LOW

        # Check safety threshold
        if best_score < self.safety_threshold:
            logger.warning(
                f"Decision confidence ({best_score:.2f}) below safety threshold "
                f"({self.safety_threshold}). Selecting safer fallback."
            )
            # Fall back to safer option
            best_action = "wait_for_clearance"
            confidence = DecisionConfidence.LOW

        # Assess risks
        risks = self._assess_risks(best_action, context)

        # Create execution plan
        execution_plan = self._create_execution_plan(best_action, context, best_metadata)

        # Generate reasoning
        reasoning = (
            f"Selected '{best_action}' with confidence {confidence.value} "
            f"(score={best_score:.3f}). "
            f"Based on urgency level {context.urgency.value}, "
            f"sensor data analysis, and constraint evaluation. "
            f"Alternative options considered: {len(options) - 1}."
        )

        # Prepare alternatives
        alternatives = [
            {
                "action": action,
                "score": score,
                "estimated_time": metadata.get("estimated_time", "unknown"),
            }
            for action, score, metadata in options[1:4]  # Top 3 alternatives
        ]

        # Create output
        output = DecisionOutput(
            action=best_action,
            confidence=confidence,
            reasoning=reasoning,
            alternatives=alternatives,
            risk_assessment=risks,
            execution_plan=execution_plan,
            timestamp=datetime.now(),
        )

        # Store in history
        self.decision_history.append(
            {
                "context": context,
                "output": output,
                "timestamp": datetime.now(),
            }
        )

        logger.info(
            f"Decision made: {best_action} (confidence={confidence.value}, "
            f"score={best_score:.3f})"
        )

        return output

    def learn_from_outcome(
        self, decision_id: int, actual_outcome: dict[str, Any], success: bool
    ):
        """
        Learn from the outcome of a previous decision (online learning)

        Args:
            decision_id: Index of the decision in history
            actual_outcome: The actual outcome that occurred
            success: Whether the decision was successful
        """
        if not self.enable_learning:
            logger.debug("Learning disabled, skipping outcome feedback")
            return

        if decision_id >= len(self.decision_history):
            logger.error(f"Invalid decision_id: {decision_id}")
            return

        decision_record = self.decision_history[decision_id]

        logger.info(
            f"Learning from outcome: decision={decision_record['output'].action}, "
            f"success={success}"
        )

        # In a full implementation, this would update model weights
        # For now, we just log the feedback
        decision_record["feedback"] = {
            "actual_outcome": actual_outcome,
            "success": success,
            "timestamp": datetime.now(),
        }

    def get_decision_history(self) -> list[dict[str, Any]]:
        """
        Get the history of decisions made

        Returns:
            List of decision records
        """
        return self.decision_history

    def reset_history(self):
        """Clear decision history"""
        self.decision_history.clear()
        logger.info("Decision history cleared")
