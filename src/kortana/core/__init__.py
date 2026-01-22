"""
Kor'tana Core Package

Contains the core functionality of the Kor'tana system, including:
- ChatEngine for model management and conversation
- Goal Framework for autonomous operation
- Sacred Covenant enforcement
- Memory and persistence systems
- Debugging and Maintenance Tools
"""

# Lazy imports to avoid circular dependencies
def __getattr__(name):
    """Lazy loading of modules to prevent circular import issues."""
    if name == "schemas":
        from . import schemas
        return schemas
    elif name in ["Goal", "GoalManager", "GoalStatus", "GoalType"]:
        from .goals import Goal, GoalManager, GoalStatus, GoalType
        return locals()[name]
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")


__all__ = [
    # Goal Framework
    "Goal",
    "GoalManager",
    "GoalStatus",
    "GoalType",
    "schemas",
]
