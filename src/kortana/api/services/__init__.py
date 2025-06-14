"""
Kor'tana API Services Layer

This package contains service layer implementations for business logic,
separating concerns from the API routing layer.

Created as part of autonomous refactoring assignment.
"""

from .goal_service import GoalService

__all__ = ["GoalService"]
