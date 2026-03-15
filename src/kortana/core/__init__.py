"""
Kor'tana Core Package

Contains the core functionality of the Kor'tana system, including:
- ChatEngine for model management and conversation
- Goal Framework for autonomous operation
- Sacred Covenant enforcement
- Memory and persistence systems
- Debugging and Maintenance Tools
"""

# Import modules explicitly to avoid circular dependency issues
try:
    from . import schemas
except ImportError:
    schemas = None

try:
    from .goals import Goal, GoalManager, GoalStatus, GoalType
except ImportError:
    Goal = GoalManager = GoalStatus = GoalType = None

__all__ = [
    # Goal Framework
    "Goal",
    "GoalManager",
    "GoalStatus",
    "GoalType",
    "schemas",
]
