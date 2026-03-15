"""
AI-Powered Decision-Making Module for Kor'tana

This module provides machine learning-driven strategies for real-time decision-making,
enhancing Kor'tana's ability to analyze time-sensitive datasets, predict outcomes,
and provide optimized solutions for autonomous systems.

Key Components:
- Decision Engine: Core ML-based decision-making system
- Dataset Analyzer: Time-sensitive data analysis
- Outcome Predictor: ML-based prediction system
- Decision Optimizer: Solution optimization framework
"""

from kortana.ai_decision.decision_engine import DecisionEngine
from kortana.ai_decision.dataset_analyzer import DatasetAnalyzer
from kortana.ai_decision.outcome_predictor import OutcomePredictor
from kortana.ai_decision.optimizer import DecisionOptimizer

__all__ = [
    "DecisionEngine",
    "DatasetAnalyzer",
    "OutcomePredictor",
    "DecisionOptimizer",
]

__version__ = "1.0.0"
