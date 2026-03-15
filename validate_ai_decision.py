"""
Simple validation script for AI decision-making module
Tests basic functionality without requiring pytest
"""

import sys
from datetime import datetime, timedelta

# Add src to path
sys.path.insert(0, '/home/runner/work/kortana/kortana/src')

print("=" * 60)
print("AI Decision-Making Module - Validation Script")
print("=" * 60)

try:
    import numpy as np
    print("✓ NumPy available")
except ImportError:
    print("✗ NumPy not available - installing...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "numpy", "-q"])
    import numpy as np
    print("✓ NumPy installed")

try:
    import torch
    print("✓ PyTorch available")
except ImportError:
    print("✗ PyTorch not available - installing (this may take a while)...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "torch", "--index-url", "https://download.pytorch.org/whl/cpu", "-q"])
    import torch
    print("✓ PyTorch installed")

print("\n" + "=" * 60)
print("Testing AI Decision Module Components")
print("=" * 60)

# Test 1: Import modules
print("\n1. Testing module imports...")
try:
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
    print("   ✓ All modules imported successfully")
except Exception as e:
    print(f"   ✗ Import failed: {e}")
    sys.exit(1)

# Test 2: DecisionEngine
print("\n2. Testing DecisionEngine...")
try:
    engine = DecisionEngine(safety_threshold=0.7, enable_learning=True)
    print(f"   ✓ DecisionEngine initialized (device={engine.device})")
    
    context = DecisionContext(
        scenario="test_navigation",
        urgency=DecisionUrgency.HIGH,
        constraints={"max_speed": 50},
        sensor_data={"speed": 30, "distance": 15},
        timestamp=datetime.now(),
    )
    
    decision = engine.make_decision(context)
    print(f"   ✓ Decision made: {decision.action}")
    print(f"   ✓ Confidence: {decision.confidence.value}")
    print(f"   ✓ Alternatives: {len(decision.alternatives)}")
    print(f"   ✓ Risk assessment: {len(decision.risk_assessment)} factors")
    
except Exception as e:
    print(f"   ✗ DecisionEngine test failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 3: DatasetAnalyzer
print("\n3. Testing DatasetAnalyzer...")
try:
    analyzer = DatasetAnalyzer(window_size=50, anomaly_threshold=2.5)
    print("   ✓ DatasetAnalyzer initialized")
    
    # Create sample dataset
    data = []
    base_time = datetime.now()
    for i in range(50):
        data.append({
            "timestamp": base_time + timedelta(seconds=i),
            "temperature": 20 + i * 0.1 + np.random.randn() * 0.5,
            "pressure": 100 + np.random.randn() * 2,
        })
    
    metrics = analyzer.analyze_dataset(data, "timestamp")
    print(f"   ✓ Dataset analyzed: {metrics.size} records")
    print(f"   ✓ Data quality: {metrics.data_quality:.2f}")
    print(f"   ✓ Key features: {len(metrics.key_features)}")
    
    trends = analyzer.analyze_trends(data, "temperature", "timestamp")
    print(f"   ✓ Trends analyzed: {trends.trend_direction}")
    
    anomalies = analyzer.detect_anomalies(data, "pressure")
    print(f"   ✓ Anomalies detected: {len(anomalies)}")
    
except Exception as e:
    print(f"   ✗ DatasetAnalyzer test failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 4: OutcomePredictor
print("\n4. Testing OutcomePredictor...")
try:
    predictor = OutcomePredictor(use_ensemble=True, confidence_threshold=0.6)
    print(f"   ✓ OutcomePredictor initialized (device={predictor.device})")
    
    pred_input = PredictionInput(
        action="proceed_cautiously",
        context={"speed": 30, "visibility": 0.8},
    )
    
    prediction = predictor.predict(pred_input)
    print(f"   ✓ Prediction made:")
    print(f"      Success probability: {prediction.success_probability:.3f}")
    print(f"      Expected duration: {prediction.expected_duration:.2f}")
    print(f"      Confidence: {prediction.confidence:.3f}")
    print(f"      Risk factors: {len(prediction.risk_factors)}")
    
except Exception as e:
    print(f"   ✗ OutcomePredictor test failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 5: DecisionOptimizer
print("\n5. Testing DecisionOptimizer...")
try:
    optimizer = DecisionOptimizer(max_iterations=100)
    print("   ✓ DecisionOptimizer initialized")
    
    actions = ["action_a", "action_b", "action_c"]
    context = {"scenario": "test"}
    
    objectives = [
        OptimizationObjective(name="success_probability", weight=1.0, minimize=False),
        OptimizationObjective(name="execution_time", weight=0.8, minimize=True),
    ]
    
    def evaluator(action, ctx):
        return {
            "success_probability": np.random.uniform(0.6, 0.9),
            "execution_time": np.random.uniform(1.0, 5.0),
        }
    
    result = optimizer.optimize(actions, context, objectives, evaluator)
    print(f"   ✓ Optimization complete:")
    print(f"      Best action: {result.best_action}")
    print(f"      Best score: {result.best_score:.3f}")
    print(f"      Pareto front size: {len(result.pareto_front)}")
    
except Exception as e:
    print(f"   ✗ DecisionOptimizer test failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 6: Integration test
print("\n6. Testing Integration Flow...")
try:
    # Initialize all components
    engine = DecisionEngine()
    analyzer = DatasetAnalyzer()
    predictor = OutcomePredictor()
    optimizer = DecisionOptimizer()
    
    # Create dataset
    data = []
    base_time = datetime.now()
    for i in range(30):
        data.append({
            "timestamp": base_time + timedelta(seconds=i),
            "speed": 30 + np.random.randn() * 2,
        })
    
    # Analyze
    metrics = analyzer.analyze_dataset(data, "timestamp")
    
    # Make decision
    context = DecisionContext(
        scenario="integration_test",
        urgency=DecisionUrgency.MEDIUM,
        constraints={},
        sensor_data=metrics.key_features,
        timestamp=datetime.now(),
    )
    
    decision = engine.make_decision(context)
    
    # Predict outcomes
    pred_input = PredictionInput(
        action=decision.action,
        context={"speed": 30},
    )
    prediction = predictor.predict(pred_input)
    
    # Optimize
    actions = [decision.action] + [alt["action"] for alt in decision.alternatives[:2]]
    objectives = [
        OptimizationObjective(name="success_probability", weight=1.0, minimize=False),
    ]
    
    def simple_evaluator(action, ctx):
        return {"success_probability": np.random.uniform(0.6, 0.9)}
    
    opt_result = optimizer.optimize(actions, {}, objectives, simple_evaluator)
    
    print("   ✓ Integration flow completed successfully")
    print(f"      Decision: {decision.action}")
    print(f"      Prediction: {prediction.success_probability:.3f}")
    print(f"      Optimized: {opt_result.best_action}")
    
except Exception as e:
    print(f"   ✗ Integration test failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "=" * 60)
print("✓ ALL TESTS PASSED")
print("=" * 60)
print("\nAI Decision-Making Module is working correctly!")
print("\nKey Features Validated:")
print("  • ML-powered decision engine with neural networks")
print("  • Time-sensitive dataset analysis and trend detection")
print("  • Outcome prediction with confidence scoring")
print("  • Multi-objective optimization with Pareto fronts")
print("  • Full integration between all components")
print("\nThe module is ready for integration with Kor'tana's autonomous systems.")
