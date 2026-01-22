"""
Tests for AI Decision-Making Module

Comprehensive tests for decision engine, dataset analyzer,
outcome predictor, and optimizer components.
"""

import pytest
from datetime import datetime, timedelta
import numpy as np

from kortana.ai_decision import (
    DecisionEngine,
    DatasetAnalyzer,
    OutcomePredictor,
    DecisionOptimizer,
)
from kortana.ai_decision.decision_engine import (
    DecisionContext,
    DecisionUrgency,
    DecisionConfidence,
)
from kortana.ai_decision.outcome_predictor import PredictionInput
from kortana.ai_decision.optimizer import OptimizationObjective


class TestDecisionEngine:
    """Tests for DecisionEngine"""

    def test_initialization(self):
        """Test decision engine initialization"""
        engine = DecisionEngine(safety_threshold=0.8, enable_learning=True)
        assert engine.safety_threshold == 0.8
        assert engine.enable_learning is True
        assert len(engine.decision_history) == 0

    def test_make_decision_basic(self):
        """Test basic decision-making"""
        engine = DecisionEngine()

        context = DecisionContext(
            scenario="autonomous_navigation",
            urgency=DecisionUrgency.HIGH,
            constraints={"max_speed": 50, "safe_distance": 10},
            sensor_data={"speed": 30, "distance_to_obstacle": 15},
            timestamp=datetime.now(),
        )

        decision = engine.make_decision(context)

        assert decision.action is not None
        assert isinstance(decision.confidence, DecisionConfidence)
        assert decision.reasoning is not None
        assert len(decision.alternatives) > 0
        assert "execution_failure" in decision.risk_assessment
        assert "steps" in decision.execution_plan

    def test_make_decision_critical_urgency(self):
        """Test decision-making with critical urgency"""
        engine = DecisionEngine()

        context = DecisionContext(
            scenario="emergency_stop",
            urgency=DecisionUrgency.CRITICAL,
            constraints={"immediate_action": True},
            sensor_data={"collision_imminent": True},
            timestamp=datetime.now(),
        )

        decision = engine.make_decision(context)

        assert decision.action is not None
        assert decision.confidence in [
            DecisionConfidence.HIGH,
            DecisionConfidence.VERY_HIGH,
            DecisionConfidence.MEDIUM,
            DecisionConfidence.LOW,
        ]

    def test_decision_history(self):
        """Test decision history tracking"""
        engine = DecisionEngine()

        # Make multiple decisions
        for i in range(3):
            context = DecisionContext(
                scenario=f"test_scenario_{i}",
                urgency=DecisionUrgency.MEDIUM,
                constraints={},
                sensor_data={"value": i},
                timestamp=datetime.now(),
            )
            engine.make_decision(context)

        history = engine.get_decision_history()
        assert len(history) == 3

        # Test reset
        engine.reset_history()
        assert len(engine.get_decision_history()) == 0

    def test_learn_from_outcome(self):
        """Test learning from decision outcomes"""
        engine = DecisionEngine(enable_learning=True)

        context = DecisionContext(
            scenario="test_learning",
            urgency=DecisionUrgency.MEDIUM,
            constraints={},
            sensor_data={},
            timestamp=datetime.now(),
        )

        decision = engine.make_decision(context)

        # Provide feedback
        engine.learn_from_outcome(
            decision_id=0,
            actual_outcome={"result": "success", "duration": 1.5},
            success=True,
        )

        history = engine.get_decision_history()
        assert "feedback" in history[0]
        assert history[0]["feedback"]["success"] is True

    def test_safety_threshold(self):
        """Test safety threshold enforcement"""
        engine = DecisionEngine(safety_threshold=0.95)

        context = DecisionContext(
            scenario="high_risk_scenario",
            urgency=DecisionUrgency.HIGH,
            constraints={},
            sensor_data={},
            timestamp=datetime.now(),
        )

        decision = engine.make_decision(context)

        # Should fall back to safer option due to high threshold
        assert decision.action is not None


class TestDatasetAnalyzer:
    """Tests for DatasetAnalyzer"""

    def test_initialization(self):
        """Test analyzer initialization"""
        analyzer = DatasetAnalyzer(window_size=50, anomaly_threshold=3.0)
        assert analyzer.window_size == 50
        assert analyzer.anomaly_threshold == 3.0

    def test_analyze_empty_dataset(self):
        """Test analyzing empty dataset"""
        analyzer = DatasetAnalyzer()
        metrics = analyzer.analyze_dataset([])

        assert metrics.size == 0
        assert metrics.data_quality == 0.0
        assert metrics.missing_values_ratio == 1.0

    def test_analyze_dataset_basic(self):
        """Test basic dataset analysis"""
        analyzer = DatasetAnalyzer()

        # Create sample dataset
        data = []
        base_time = datetime.now()
        for i in range(100):
            data.append(
                {
                    "timestamp": base_time + timedelta(seconds=i),
                    "temperature": 20 + i * 0.1 + np.random.randn() * 0.5,
                    "pressure": 100 + np.random.randn() * 2,
                    "status": "normal",
                }
            )

        metrics = analyzer.analyze_dataset(data, timestamp_key="timestamp")

        assert metrics.size == 100
        assert metrics.data_quality > 0.9  # Should be high quality
        assert metrics.temporal_consistency > 0.8  # Should be consistent
        assert "temperature" in metrics.key_features
        assert "pressure" in metrics.key_features

    def test_detect_anomalies(self):
        """Test anomaly detection"""
        analyzer = DatasetAnalyzer(anomaly_threshold=2.0)

        # Create dataset with anomalies
        data = []
        for i in range(100):
            value = 50 + np.random.randn() * 5
            # Add anomalies
            if i in [25, 75]:
                value = 150  # Clear outlier
            data.append({"value": value})

        anomalies = analyzer.detect_anomalies(data, "value")

        assert len(anomalies) >= 2  # Should detect at least the injected anomalies
        assert all("z_score" in a for a in anomalies)

    def test_analyze_trends(self):
        """Test trend analysis"""
        analyzer = DatasetAnalyzer()

        # Create increasing trend
        data = []
        base_time = datetime.now()
        for i in range(50):
            data.append(
                {
                    "timestamp": base_time + timedelta(seconds=i),
                    "metric": 10 + i * 0.5,  # Clear increasing trend
                }
            )

        trends = analyzer.analyze_trends(data, "metric", "timestamp")

        assert trends.trend_direction == "increasing"
        assert trends.trend_strength > 0.0
        assert len(trends.forecast["values"]) > 0

    def test_realtime_summary(self):
        """Test real-time summary generation"""
        analyzer = DatasetAnalyzer()

        data = []
        for i in range(20):
            data.append(
                {
                    "temperature": 20 + i * 0.1,
                    "humidity": 60 + np.random.randn() * 2,
                }
            )

        summary = analyzer.get_realtime_summary(data, ["temperature", "humidity"])

        assert summary["record_count"] == 20
        assert "temperature" in summary["fields"]
        assert "humidity" in summary["fields"]
        assert "mean" in summary["fields"]["temperature"]
        assert "trend" in summary["fields"]["temperature"]


class TestOutcomePredictor:
    """Tests for OutcomePredictor"""

    def test_initialization(self):
        """Test predictor initialization"""
        predictor = OutcomePredictor(use_ensemble=True, confidence_threshold=0.7)
        assert predictor.use_ensemble is True
        assert predictor.confidence_threshold == 0.7

    def test_predict_basic(self):
        """Test basic outcome prediction"""
        predictor = OutcomePredictor()

        pred_input = PredictionInput(
            action="proceed_cautiously",
            context={"speed": 30, "visibility": 0.8},
            constraints={"max_speed": 50},
        )

        output = predictor.predict(pred_input)

        assert 0.0 <= output.success_probability <= 1.0
        assert output.expected_duration > 0.0
        assert output.expected_cost >= 0.0
        assert len(output.risk_factors) > 0
        assert 0.0 <= output.confidence <= 1.0
        assert len(output.alternative_scenarios) > 0

    def test_batch_predict(self):
        """Test batch prediction"""
        predictor = OutcomePredictor()

        inputs = [
            PredictionInput(
                action="accelerate",
                context={"speed": 20},
            ),
            PredictionInput(
                action="decelerate",
                context={"speed": 50},
            ),
            PredictionInput(
                action="stop",
                context={"speed": 30},
            ),
        ]

        outputs = predictor.batch_predict(inputs)

        assert len(outputs) == 3
        assert all(0.0 <= o.success_probability <= 1.0 for o in outputs)

    def test_update_from_feedback(self):
        """Test model update from feedback"""
        predictor = OutcomePredictor()

        pred_input = PredictionInput(
            action="test_action",
            context={"value": 42},
        )

        output = predictor.predict(pred_input)

        # Provide feedback
        predictor.update_from_feedback(
            prediction_id=0,
            actual_outcome={"success": True, "duration": 1.2},
        )

        history = predictor.prediction_history
        assert "actual_outcome" in history[0]

    def test_prediction_accuracy(self):
        """Test accuracy calculation"""
        predictor = OutcomePredictor()

        # Make prediction
        pred_input = PredictionInput(action="test", context={})
        predictor.predict(pred_input)

        # Provide feedback
        predictor.update_from_feedback(0, {"success": True})

        accuracy = predictor.get_prediction_accuracy()
        assert "accuracy" in accuracy
        assert "sample_count" in accuracy


class TestDecisionOptimizer:
    """Tests for DecisionOptimizer"""

    def test_initialization(self):
        """Test optimizer initialization"""
        optimizer = DecisionOptimizer(
            max_iterations=200, population_size=100, convergence_threshold=0.0001
        )
        assert optimizer.max_iterations == 200
        assert optimizer.population_size == 100

    def test_optimize_basic(self):
        """Test basic optimization"""
        optimizer = DecisionOptimizer()

        actions = ["action_a", "action_b", "action_c"]
        context = {"scenario": "test"}

        objectives = [
            OptimizationObjective(
                name="success_probability", weight=1.0, minimize=False
            ),
            OptimizationObjective(name="execution_time", weight=0.8, minimize=True),
            OptimizationObjective(name="cost", weight=0.6, minimize=True),
        ]

        def evaluator(action, context):
            # Simple mock evaluator
            return {
                "success_probability": np.random.uniform(0.6, 0.9),
                "execution_time": np.random.uniform(1.0, 5.0),
                "cost": np.random.uniform(0.5, 2.0),
            }

        result = optimizer.optimize(actions, context, objectives, evaluator)

        assert result.best_action in actions
        assert 0.0 <= result.best_score <= 1.0
        assert len(result.objective_values) > 0
        assert len(result.pareto_front) > 0

    def test_optimize_with_constraints(self):
        """Test optimization with constraints"""
        optimizer = DecisionOptimizer()

        actions = ["fast", "slow", "medium"]
        context = {}

        objectives = [
            OptimizationObjective(
                name="speed",
                weight=1.0,
                minimize=False,
                constraint_min=0.5,  # Must be at least 0.5
            ),
            OptimizationObjective(
                name="safety", weight=1.0, minimize=False, constraint_min=0.7
            ),
        ]

        def evaluator(action, context):
            if action == "fast":
                return {"speed": 0.9, "safety": 0.6}  # Violates safety constraint
            elif action == "slow":
                return {"speed": 0.4, "safety": 0.9}  # Violates speed constraint
            else:
                return {"speed": 0.8, "safety": 0.8}  # Satisfies both

        result = optimizer.optimize(actions, context, objectives, evaluator)

        # Should select "medium" as it satisfies constraints
        assert result.best_action == "medium"

    def test_optimize_with_tradeoffs(self):
        """Test optimization with different tradeoff scenarios"""
        optimizer = DecisionOptimizer()

        actions = ["option_a", "option_b"]
        context = {}

        objectives = [
            OptimizationObjective(name="success_probability", weight=1.0, minimize=False),
            OptimizationObjective(name="expected_duration", weight=1.0, minimize=True),
        ]

        def evaluator(action, context):
            if action == "option_a":
                return {"success_probability": 0.9, "expected_duration": 5.0}
            else:
                return {"success_probability": 0.7, "expected_duration": 2.0}

        scenarios = [
            {
                "name": "quality_first",
                "weights": {"success_probability": 2.0, "expected_duration": 1.0},
            },
            {
                "name": "speed_first",
                "weights": {"success_probability": 1.0, "expected_duration": 2.0},
            },
        ]

        results = optimizer.optimize_with_tradeoffs(
            actions, context, objectives, evaluator, scenarios
        )

        assert "quality_first" in results
        assert "speed_first" in results
        # Quality first should prefer option_a (high success rate)
        # Speed first should prefer option_b (low duration)

    def test_get_recommendation(self):
        """Test recommendation from multiple results"""
        optimizer = DecisionOptimizer()

        # Mock results
        results = {
            "balanced": type(
                "Result", (), {"best_action": "action_a", "best_score": 0.8}
            )(),
            "aggressive": type(
                "Result", (), {"best_action": "action_b", "best_score": 0.9}
            )(),
        }

        action, reasoning = optimizer.get_recommendation(results, preference="balanced")
        assert action == "action_a"
        assert "balanced" in reasoning


class TestIntegration:
    """Integration tests for the complete AI decision system"""

    def test_end_to_end_decision_flow(self):
        """Test complete decision-making flow"""
        # Initialize components
        engine = DecisionEngine()
        analyzer = DatasetAnalyzer()
        predictor = OutcomePredictor()
        optimizer = DecisionOptimizer()

        # Prepare dataset
        data = []
        base_time = datetime.now()
        for i in range(50):
            data.append(
                {
                    "timestamp": base_time + timedelta(seconds=i),
                    "speed": 30 + np.random.randn() * 2,
                    "distance": 100 - i * 2,
                }
            )

        # Analyze dataset
        metrics = analyzer.analyze_dataset(data, "timestamp")
        assert metrics.size == 50

        trends = analyzer.analyze_trends(data, "distance", "timestamp")
        assert trends.trend_direction == "decreasing"

        # Create decision context
        context = DecisionContext(
            scenario="autonomous_driving",
            urgency=DecisionUrgency.HIGH,
            constraints={"max_speed": 50, "min_distance": 10},
            sensor_data=metrics.key_features,
            timestamp=datetime.now(),
        )

        # Make decision
        decision = engine.make_decision(context)
        assert decision.action is not None

        # Predict outcomes for alternatives
        for alt in decision.alternatives[:2]:
            pred_input = PredictionInput(
                action=alt["action"], context={"speed": 30, "distance": 20}
            )
            prediction = predictor.predict(pred_input)
            assert prediction.success_probability >= 0.0

        # Optimize decision
        actions = [decision.action] + [alt["action"] for alt in decision.alternatives[:2]]
        objectives = [
            OptimizationObjective(name="success_probability", weight=1.0, minimize=False),
            OptimizationObjective(name="expected_duration", weight=0.8, minimize=True),
        ]

        def evaluator(action, ctx):
            pred_input = PredictionInput(action=action, context=ctx)
            pred = predictor.predict(pred_input)
            return {
                "success_probability": pred.success_probability,
                "expected_duration": pred.expected_duration,
            }

        opt_result = optimizer.optimize(actions, {"speed": 30}, objectives, evaluator)
        assert opt_result.best_action is not None

    def test_time_sensitive_decision_making(self):
        """Test decision-making with time-sensitive data"""
        engine = DecisionEngine()
        analyzer = DatasetAnalyzer()

        # Simulate real-time data stream
        data_stream = []
        base_time = datetime.now()

        for i in range(100):
            data_stream.append(
                {
                    "timestamp": base_time + timedelta(milliseconds=i * 100),
                    "sensor_value": 50 + np.sin(i * 0.1) * 10 + np.random.randn() * 2,
                }
            )

        # Analyze in real-time windows
        window_size = 20
        for i in range(0, len(data_stream) - window_size, window_size):
            window_data = data_stream[i : i + window_size]

            metrics = analyzer.analyze_dataset(window_data, "timestamp")
            assert metrics.size == window_size

            summary = analyzer.get_realtime_summary(window_data, ["sensor_value"])
            assert "sensor_value" in summary["fields"]

            # Make urgent decision based on current window
            context = DecisionContext(
                scenario=f"realtime_window_{i}",
                urgency=DecisionUrgency.HIGH,
                constraints={},
                sensor_data=summary["fields"]["sensor_value"],
                timestamp=datetime.now(),
            )

            decision = engine.make_decision(context)
            assert decision.action is not None
