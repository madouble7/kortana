# AI-Powered Decision-Making Module

## Overview

The AI Decision-Making Module provides machine learning-driven strategies for real-time decision-making in autonomous systems. It enhances Kor'tana's ability to analyze time-sensitive datasets, predict outcomes, and provide optimized solutions.

## Features

### 1. **Decision Engine** (`decision_engine.py`)
ML-powered decision-making system that:
- Analyzes current context and historical patterns
- Evaluates multiple decision options using neural networks
- Predicts outcomes for each option
- Selects optimal actions with confidence scores
- Provides risk assessments and execution plans
- Supports online learning from feedback

### 2. **Dataset Analyzer** (`dataset_analyzer.py`)
Real-time analysis of time-sensitive datasets:
- Data quality assessment
- Temporal pattern detection
- Anomaly detection using statistical methods
- Trend analysis and forecasting
- Feature extraction for ML models

### 3. **Outcome Predictor** (`outcome_predictor.py`)
ML-based outcome prediction:
- Success probability prediction
- Duration and cost estimation
- Risk factor assessment
- Multi-scenario analysis
- Model updates from actual outcomes

### 4. **Decision Optimizer** (`optimizer.py`)
Multi-objective optimization:
- Weighted objective optimization
- Constraint handling
- Pareto-optimal solution discovery
- Trade-off analysis
- Support for multiple optimization scenarios

## Installation

The module requires PyTorch and NumPy, which are already included in Kor'tana's dependencies:

```bash
pip install torch numpy
```

## Quick Start

### Basic Decision Making

```python
from datetime import datetime
from kortana.ai_decision import DecisionEngine
from kortana.ai_decision.decision_engine import DecisionContext, DecisionUrgency

# Initialize the decision engine
engine = DecisionEngine(safety_threshold=0.7, enable_learning=True)

# Create a decision context
context = DecisionContext(
    scenario="autonomous_navigation",
    urgency=DecisionUrgency.HIGH,
    constraints={"max_speed": 50, "safe_distance": 10},
    sensor_data={"speed": 30, "distance_to_obstacle": 15},
    timestamp=datetime.now(),
)

# Make a decision
decision = engine.make_decision(context)

print(f"Action: {decision.action}")
print(f"Confidence: {decision.confidence.value}")
print(f"Risk Assessment: {decision.risk_assessment}")
print(f"Execution Plan: {decision.execution_plan}")
```

### Dataset Analysis

```python
from datetime import datetime, timedelta
from kortana.ai_decision import DatasetAnalyzer

# Initialize analyzer
analyzer = DatasetAnalyzer(window_size=100, anomaly_threshold=2.5)

# Prepare time-series data
data = []
base_time = datetime.now()
for i in range(100):
    data.append({
        "timestamp": base_time + timedelta(seconds=i),
        "temperature": 20 + i * 0.1,
        "pressure": 100 + random.uniform(-2, 2),
    })

# Analyze dataset
metrics = analyzer.analyze_dataset(data, "timestamp")
print(f"Data Quality: {metrics.data_quality:.2f}")
print(f"Temporal Consistency: {metrics.temporal_consistency:.2f}")

# Analyze trends
trends = analyzer.analyze_trends(data, "temperature", "timestamp")
print(f"Trend Direction: {trends.trend_direction}")
print(f"Trend Strength: {trends.trend_strength:.2f}")

# Detect anomalies
anomalies = analyzer.detect_anomalies(data, "pressure")
print(f"Anomalies Detected: {len(anomalies)}")
```

### Outcome Prediction

```python
from kortana.ai_decision import OutcomePredictor
from kortana.ai_decision.outcome_predictor import PredictionInput

# Initialize predictor
predictor = OutcomePredictor(use_ensemble=True, confidence_threshold=0.6)

# Create prediction input
pred_input = PredictionInput(
    action="proceed_cautiously",
    context={"speed": 30, "visibility": 0.8},
    constraints={"max_speed": 50},
)

# Predict outcome
prediction = predictor.predict(pred_input)

print(f"Success Probability: {prediction.success_probability:.3f}")
print(f"Expected Duration: {prediction.expected_duration:.2f}s")
print(f"Expected Cost: {prediction.expected_cost:.2f}")
print(f"Confidence: {prediction.confidence:.3f}")
print(f"Risk Factors: {prediction.risk_factors}")
```

### Decision Optimization

```python
from kortana.ai_decision import DecisionOptimizer
from kortana.ai_decision.optimizer import OptimizationObjective

# Initialize optimizer
optimizer = DecisionOptimizer(max_iterations=100)

# Define objectives
objectives = [
    OptimizationObjective(
        name="success_probability",
        weight=1.0,
        minimize=False,
        constraint_min=0.7,  # Must be at least 70% success rate
    ),
    OptimizationObjective(
        name="execution_time",
        weight=0.8,
        minimize=True,
        constraint_max=10.0,  # Must complete within 10 seconds
    ),
]

# Define evaluator function
def evaluate_action(action, context):
    # Your evaluation logic here
    return {
        "success_probability": 0.85,
        "execution_time": 5.2,
    }

# Optimize
actions = ["action_a", "action_b", "action_c"]
result = optimizer.optimize(actions, {}, objectives, evaluate_action)

print(f"Best Action: {result.best_action}")
print(f"Best Score: {result.best_score:.3f}")
print(f"Pareto Front: {len(result.pareto_front)} solutions")
```

## Integration with Kor'tana Agents

### Example: Autonomous Agent with AI Decision-Making

```python
from kortana.ai_decision import (
    DecisionEngine,
    DatasetAnalyzer,
    OutcomePredictor,
    DecisionOptimizer,
)
from kortana.ai_decision.decision_engine import DecisionContext, DecisionUrgency

class AutonomousAgent:
    """Enhanced autonomous agent with AI decision-making"""
    
    def __init__(self):
        self.decision_engine = DecisionEngine(safety_threshold=0.75)
        self.dataset_analyzer = DatasetAnalyzer()
        self.outcome_predictor = OutcomePredictor()
        self.optimizer = DecisionOptimizer()
    
    async def process_task(self, task_data):
        """Process a task with AI-powered decision-making"""
        
        # 1. Analyze incoming data
        metrics = self.dataset_analyzer.analyze_dataset(
            task_data["sensor_readings"],
            "timestamp"
        )
        
        # 2. Create decision context
        context = DecisionContext(
            scenario=task_data["scenario"],
            urgency=task_data["urgency"],
            constraints=task_data["constraints"],
            sensor_data=metrics.key_features,
            timestamp=datetime.now(),
        )
        
        # 3. Make initial decision
        decision = self.decision_engine.make_decision(context)
        
        # 4. Predict outcomes for alternatives
        predictions = []
        for alt in decision.alternatives[:3]:
            pred_input = PredictionInput(
                action=alt["action"],
                context=metrics.key_features,
            )
            pred = self.outcome_predictor.predict(pred_input)
            predictions.append((alt["action"], pred))
        
        # 5. Optimize across objectives
        actions = [decision.action] + [p[0] for p in predictions]
        objectives = [
            OptimizationObjective(name="success_probability", weight=1.0, minimize=False),
            OptimizationObjective(name="expected_duration", weight=0.8, minimize=True),
        ]
        
        def evaluator(action, ctx):
            for a, pred in predictions:
                if a == action:
                    return {
                        "success_probability": pred.success_probability,
                        "expected_duration": pred.expected_duration,
                    }
            return {"success_probability": 0.5, "expected_duration": 5.0}
        
        opt_result = self.optimizer.optimize(actions, {}, objectives, evaluator)
        
        # 6. Execute optimal action
        final_action = opt_result.best_action
        
        return {
            "action": final_action,
            "decision": decision,
            "optimization": opt_result,
        }
```

## Architecture

```
kortana.ai_decision/
├── __init__.py              # Module exports
├── decision_engine.py       # Core ML-based decision engine
├── dataset_analyzer.py      # Time-sensitive data analysis
├── outcome_predictor.py     # ML-based outcome prediction
└── optimizer.py             # Multi-objective optimization
```

## Key Concepts

### Decision Urgency Levels
- **CRITICAL**: Immediate action required (autonomous emergency response)
- **HIGH**: Action needed within seconds (real-time navigation)
- **MEDIUM**: Action needed within minutes (task scheduling)
- **LOW**: Can be deferred (background optimization)

### Decision Confidence Levels
- **VERY_HIGH**: >95% confidence
- **HIGH**: 80-95% confidence
- **MEDIUM**: 60-80% confidence
- **LOW**: <60% confidence

### Safety Threshold
The safety threshold determines the minimum confidence level required for autonomous execution. Decisions below this threshold trigger fallback to safer alternatives or request human oversight.

## Performance Considerations

### Model Optimization
- Models run on GPU when available, CPU otherwise
- Batch prediction supported for efficiency
- Ensemble predictions can be enabled for higher accuracy

### Real-Time Processing
- Dataset analyzer optimized for sliding window analysis
- Decision engine uses fast neural network inference
- Caching available for repeated analyses

### Memory Management
- Decision history can be cleared periodically
- Prediction history supports pruning
- Models support quantization for deployment

## Testing

Run the validation script:

```bash
python validate_ai_decision.py
```

Run comprehensive tests (requires pytest):

```bash
pytest tests/test_ai_decision.py -v
```

## Future Enhancements

Potential areas for expansion:
- Deep reinforcement learning for long-term strategy
- Transformer models for sequence-to-sequence decision-making
- Federated learning for multi-agent collaboration
- Explainable AI for decision transparency
- Advanced anomaly detection with autoencoders
- Real-time model updates with online learning

## References

This module draws inspiration from autonomous driving systems and implements concepts from:
- Deep Q-Networks (DQN) for decision-making
- Proximal Policy Optimization (PPO) strategies
- Multi-objective optimization algorithms
- Time-series analysis and forecasting methods

## License

Part of the Kor'tana project. See main LICENSE file for details.

## Support

For issues or questions about the AI decision-making module, please refer to the main Kor'tana documentation or open an issue in the repository.
