"""
Kor'tana Core Package

Contains the core functionality of the Kor'tana system, including:
- ChatEngine for model management and conversation
- Goal Framework for autonomous operation
- Sacred Covenant enforcement
- Memory and persistence systems
"""

from . import schemas  # Corrected import path for schemas
from .goals import Goal, GoalManager, GoalStatus, GoalType

__all__ = [
    # Goal Framework
    "Goal",
    "GoalManager",
    "GoalStatus",
    "GoalType",
    "schemas", # Re-export schemas
]
