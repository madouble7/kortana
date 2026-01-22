"""
Outcome Predictor - ML-based outcome prediction for decision-making

This module uses machine learning to predict outcomes of potential actions,
helping the decision engine select optimal strategies.
"""

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any

import numpy as np
import torch

logger = logging.getLogger(__name__)


@dataclass
class PredictionInput:
    """Input for outcome prediction"""

    action: str
    context: dict[str, Any]
    historical_data: list[dict[str, Any]] | None = None
    constraints: dict[str, Any] | None = None


@dataclass
class PredictionOutput:
    """Predicted outcome"""

    success_probability: float
    expected_duration: float
    expected_cost: float
    risk_factors: dict[str, float]
    confidence: float
    alternative_scenarios: list[dict[str, Any]]


class OutcomePredictor:
    """
    ML-based outcome prediction system

    Uses neural networks to predict the likely outcomes of actions
    based on historical data and current context.

    Features:
    - Success probability prediction
    - Duration estimation
    - Cost/resource prediction
    - Risk factor assessment
    - Multi-scenario analysis
    """

    def __init__(
        self,
        model_path: str | None = None,
        use_ensemble: bool = True,
        confidence_threshold: float = 0.6,
    ):
        """
        Initialize the outcome predictor

        Args:
            model_path: Path to pre-trained model (optional)
            use_ensemble: Whether to use ensemble predictions
            confidence_threshold: Minimum confidence for predictions
        """
        self.use_ensemble = use_ensemble
        self.confidence_threshold = confidence_threshold
        self.prediction_history: list[dict[str, Any]] = []

        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self._initialize_models()

        if model_path:
            self._load_model(model_path)

        logger.info(
            f"Outcome predictor initialized (device={self.device}, "
            f"ensemble={use_ensemble})"
        )

    def _initialize_models(self):
        """Initialize prediction models"""
        # Feature input size
        self.input_size = 64

        # Success probability predictor
        self.success_model = torch.nn.Sequential(
            torch.nn.Linear(self.input_size, 128),
            torch.nn.ReLU(),
            torch.nn.Dropout(0.3),
            torch.nn.Linear(128, 64),
            torch.nn.ReLU(),
            torch.nn.Linear(64, 1),
            torch.nn.Sigmoid(),
        ).to(self.device)

        # Duration predictor
        self.duration_model = torch.nn.Sequential(
            torch.nn.Linear(self.input_size, 128),
            torch.nn.ReLU(),
            torch.nn.Dropout(0.3),
            torch.nn.Linear(128, 64),
            torch.nn.ReLU(),
            torch.nn.Linear(64, 1),
            torch.nn.ReLU(),  # Ensure positive output
        ).to(self.device)

        # Cost predictor
        self.cost_model = torch.nn.Sequential(
            torch.nn.Linear(self.input_size, 128),
            torch.nn.ReLU(),
            torch.nn.Dropout(0.3),
            torch.nn.Linear(128, 64),
            torch.nn.ReLU(),
            torch.nn.Linear(64, 1),
            torch.nn.ReLU(),  # Ensure positive output
        ).to(self.device)

        logger.debug("Prediction models initialized")

    def _load_model(self, model_path: str):
        """Load pre-trained models"""
        try:
            checkpoint = torch.load(model_path, map_location=self.device)
            self.success_model.load_state_dict(checkpoint["success_model"])
            self.duration_model.load_state_dict(checkpoint["duration_model"])
            self.cost_model.load_state_dict(checkpoint["cost_model"])
            logger.info(f"Loaded models from {model_path}")
        except Exception as e:
            logger.warning(
                f"Failed to load models from {model_path}: {e}. "
                f"Using random initialization."
            )

    def _encode_action(self, action: str) -> np.ndarray:
        """
        Encode action as a feature vector

        Args:
            action: Action name

        Returns:
            Encoded feature vector
        """
        # Simple one-hot-like encoding (in production, use embeddings)
        action_map = {
            "proceed_cautiously": 0,
            "accelerate": 1,
            "decelerate": 2,
            "stop": 3,
            "wait_for_clearance": 4,
            "request_assistance": 5,
            "adjust_parameters": 6,
            "continue_monitoring": 7,
            "escalate_priority": 8,
            "execute_fallback_plan": 9,
        }

        action_id = action_map.get(action, 0)
        encoding = np.zeros(10)
        encoding[action_id] = 1.0

        return encoding

    def _encode_context(self, context: dict[str, Any]) -> np.ndarray:
        """
        Encode context as feature vector

        Args:
            context: Context dictionary

        Returns:
            Encoded feature vector
        """
        features = np.zeros(40)

        # Encode numeric values
        numeric_values = []
        for key, value in context.items():
            if isinstance(value, (int, float)):
                numeric_values.append(float(value))

        # Fill feature vector
        for i, value in enumerate(numeric_values[:40]):
            features[i] = value

        return features

    def _extract_features(self, pred_input: PredictionInput) -> torch.Tensor:
        """
        Extract feature vector from prediction input

        Args:
            pred_input: Prediction input

        Returns:
            Feature tensor
        """
        # Encode action
        action_features = self._encode_action(pred_input.action)

        # Encode context
        context_features = self._encode_context(pred_input.context)

        # Combine features
        features = np.concatenate([action_features, context_features])

        # Pad or truncate to input_size
        if len(features) < self.input_size:
            features = np.pad(features, (0, self.input_size - len(features)))
        else:
            features = features[: self.input_size]

        return torch.FloatTensor(features).to(self.device)

    def _predict_risk_factors(
        self, action: str, context: dict[str, Any]
    ) -> dict[str, float]:
        """
        Predict risk factors for an action

        Args:
            action: Action to analyze
            context: Context information

        Returns:
            Dictionary of risk factors
        """
        # Base risk levels
        base_risks = {
            "execution_failure": 0.10,
            "resource_shortage": 0.08,
            "timing_issue": 0.12,
            "safety_concern": 0.05,
        }

        # Action-specific risk modifiers
        action_risk_modifiers = {
            "stop": {"timing_issue": 0.15, "execution_failure": 0.03},
            "wait": {"timing_issue": 0.18, "resource_shortage": 0.05},
            "accelerate": {"safety_concern": 0.10, "execution_failure": 0.05},
            "decelerate": {"timing_issue": 0.08, "execution_failure": 0.02},
        }

        # Apply action-specific modifiers
        for action_keyword, modifiers in action_risk_modifiers.items():
            if action_keyword in action.lower():
                for risk_type, modifier in modifiers.items():
                    base_risks[risk_type] += modifier

        # Context-based adjustments
        if "complexity" in context:
            complexity_factor = float(context["complexity"]) / 10.0
            base_risks["execution_failure"] += complexity_factor * 0.05

        if "speed" in context:
            speed_factor = float(context.get("speed", 0)) / 100.0
            base_risks["safety_concern"] += speed_factor * 0.08

        # Ensure values are in valid range
        for key in base_risks:
            base_risks[key] = max(0.0, min(1.0, base_risks[key]))

        return base_risks

    def _generate_alternative_scenarios(
        self, pred_input: PredictionInput
    ) -> list[dict[str, Any]]:
        """
        Generate alternative outcome scenarios

        Args:
            pred_input: Prediction input

        Returns:
            List of alternative scenarios
        """
        scenarios = []

        # Best case scenario
        scenarios.append(
            {
                "name": "best_case",
                "probability": 0.25,
                "success_rate": 0.95,
                "duration_factor": 0.8,
                "cost_factor": 0.9,
            }
        )

        # Expected case
        scenarios.append(
            {
                "name": "expected",
                "probability": 0.50,
                "success_rate": 0.80,
                "duration_factor": 1.0,
                "cost_factor": 1.0,
            }
        )

        # Worst case
        scenarios.append(
            {
                "name": "worst_case",
                "probability": 0.25,
                "success_rate": 0.60,
                "duration_factor": 1.5,
                "cost_factor": 1.3,
            }
        )

        return scenarios

    def predict(self, pred_input: PredictionInput) -> PredictionOutput:
        """
        Predict the outcome of an action

        Args:
            pred_input: Prediction input with action and context

        Returns:
            Predicted outcome with probabilities and estimates
        """
        logger.info(f"Predicting outcome for action: {pred_input.action}")

        # Extract features
        features = self._extract_features(pred_input).unsqueeze(0)

        # Make predictions
        with torch.no_grad():
            success_prob = float(self.success_model(features).cpu().item())
            expected_duration = float(self.duration_model(features).cpu().item())
            expected_cost = float(self.cost_model(features).cpu().item())

        # Ensure reasonable ranges
        success_prob = max(0.0, min(1.0, success_prob))
        expected_duration = max(0.1, min(100.0, expected_duration))
        expected_cost = max(0.0, min(10.0, expected_cost))

        # Predict risk factors
        risk_factors = self._predict_risk_factors(pred_input.action, pred_input.context)

        # Calculate confidence based on various factors
        confidence = success_prob * 0.5 + (1.0 - np.std(list(risk_factors.values()))) * 0.5
        confidence = max(0.0, min(1.0, confidence))

        # Generate alternative scenarios
        alternative_scenarios = self._generate_alternative_scenarios(pred_input)

        # Create output
        output = PredictionOutput(
            success_probability=success_prob,
            expected_duration=expected_duration,
            expected_cost=expected_cost,
            risk_factors=risk_factors,
            confidence=confidence,
            alternative_scenarios=alternative_scenarios,
        )

        # Store in history
        self.prediction_history.append(
            {
                "input": pred_input,
                "output": output,
                "timestamp": datetime.now(),
            }
        )

        logger.info(
            f"Prediction complete: success_prob={success_prob:.2f}, "
            f"duration={expected_duration:.2f}, confidence={confidence:.2f}"
        )

        return output

    def batch_predict(
        self, inputs: list[PredictionInput]
    ) -> list[PredictionOutput]:
        """
        Make predictions for multiple inputs

        Args:
            inputs: List of prediction inputs

        Returns:
            List of prediction outputs
        """
        logger.info(f"Batch predicting {len(inputs)} outcomes")

        outputs = []
        for pred_input in inputs:
            output = self.predict(pred_input)
            outputs.append(output)

        return outputs

    def update_from_feedback(
        self, prediction_id: int, actual_outcome: dict[str, Any]
    ):
        """
        Update models based on actual outcomes (online learning)

        Args:
            prediction_id: Index of prediction in history
            actual_outcome: Actual outcome that occurred
        """
        if prediction_id >= len(self.prediction_history):
            logger.error(f"Invalid prediction_id: {prediction_id}")
            return

        record = self.prediction_history[prediction_id]

        logger.info(
            f"Updating from feedback: predicted={record['output'].success_probability:.2f}, "
            f"actual={actual_outcome.get('success', 'unknown')}"
        )

        # In a full implementation, this would:
        # 1. Calculate loss between prediction and actual
        # 2. Perform gradient descent to update weights
        # 3. Store updated models

        record["actual_outcome"] = actual_outcome
        record["feedback_timestamp"] = datetime.now()

    def get_prediction_accuracy(self) -> dict[str, float]:
        """
        Calculate prediction accuracy from history

        Returns:
            Accuracy metrics
        """
        if not self.prediction_history:
            return {"accuracy": 0.0, "sample_count": 0}

        # Count predictions with feedback
        with_feedback = [
            p for p in self.prediction_history if "actual_outcome" in p
        ]

        if not with_feedback:
            return {"accuracy": 0.0, "sample_count": 0}

        # Calculate accuracy
        correct = 0
        for record in with_feedback:
            predicted = record["output"].success_probability > 0.5
            actual = record.get("actual_outcome", {}).get("success", False)
            if predicted == actual:
                correct += 1

        accuracy = correct / len(with_feedback)

        return {
            "accuracy": accuracy,
            "sample_count": len(with_feedback),
            "total_predictions": len(self.prediction_history),
        }
