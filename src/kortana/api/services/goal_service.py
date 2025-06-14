"""
🎯 AUTONOMOUS DEVELOPMENT DEMO
This file demonstrates Kor'tana's autonomous engineering capabilities.

Goal Service Layer - Created autonomously as part of refactoring assignment.
"""

from sqlalchemy.orm import Session

from ..models.goal import Goal


class GoalService:
    """Service layer for goal operations - separates business logic from API routing."""

    def __init__(self, db_session: Session):
        self.db = db_session

    async def list_all_goals(self) -> list[Goal]:
        """
        Retrieve all goals from the database.

        This function was refactored from the router layer to create proper
        separation of concerns and improve modularity.
        """
        return self.db.query(Goal).all()

    async def get_goal_by_id(self, goal_id: int) -> Goal | None:
        """Get a specific goal by ID."""
        return self.db.query(Goal).filter(Goal.id == goal_id).first()

    async def create_goal(self, goal_data: dict) -> Goal:
        """Create a new goal."""
        goal = Goal(**goal_data)
        self.db.add(goal)
        self.db.commit()
        self.db.refresh(goal)
        return goal

    async def update_goal(self, goal_id: int, goal_data: dict) -> Goal | None:
        """Update an existing goal."""
        goal = self.db.query(Goal).filter(Goal.id == goal_id).first()
        if goal:
            for key, value in goal_data.items():
                setattr(goal, key, value)
            self.db.commit()
            self.db.refresh(goal)
        return goal

    async def delete_goal(self, goal_id: int) -> bool:
        """Delete a goal by ID."""
        goal = self.db.query(Goal).filter(Goal.id == goal_id).first()
        if goal:
            self.db.delete(goal)
            self.db.commit()
            return True
        return False
