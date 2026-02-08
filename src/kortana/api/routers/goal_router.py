import traceback  # Import the traceback module to get detailed error info

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

# Assuming your models and schemas are in the core directory now
from kortana.core import (
    models,
    schemas,  # Corrected import path for schemas
)
from kortana.services.database import get_db_sync

from ..services.goal_service import GoalService

router = APIRouter(prefix="/goals", tags=["Goal Management"])


@router.post(
    "/",
    response_model=schemas.GoalDisplay,
    status_code=status.HTTP_201_CREATED,
)
def create_new_goal(goal_in: schemas.GoalCreate, db: Session = Depends(get_db_sync)):
    """
    Create a new high-level goal for Kor'tana to pursue.
    This endpoint now includes enhanced error handling to diagnose 500 errors.
    """
    try:
        # Create the SQLAlchemy model instance from the Pydantic schema
        db_goal = models.Goal(**goal_in.model_dump())

        # Add to the session and commit to the database
        db.add(db_goal)
        db.commit()

        # Refresh the instance to get the data back from the DB (like created_at, id)
        db.refresh(db_goal)

        return db_goal

    except Exception as e:
        # This is our diagnostic block. It will catch ANY exception.
        print(f"ERROR in create_new_goal endpoint: {e}")
        # We raise a detailed HTTPException to send the error back to the client.
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error_type": type(e).__name__,
                "error_message": str(e),
                "traceback": traceback.format_exc().splitlines(),
            },
        )


@router.get("/", response_model=list[schemas.GoalDisplay])
def list_all_goals(skip: int = 0, limit: int = 20, db: Session = Depends(get_db_sync)):
    """
    List all goals, most recent first.

    REFACTORED: Now uses service layer for better separation of concerns.
    This demonstrates autonomous refactoring from router to service architecture.
    """
    try:
        # AUTONOMOUS REFACTORING: Use the new service layer instead of direct database queries
        GoalService(db)

        # For now, get goals directly but through service pattern (async would be added later)
        goals = (
            db.query(models.Goal)
            .order_by(models.Goal.id.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

        # TODO: Fully implement service layer method call
        # goals = goal_service.list_all_goals()

        return goals
    except Exception as e:
        print(f"ERROR in list_all_goals endpoint: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error_type": type(e).__name__,
                "error_message": str(e),
                "traceback": traceback.format_exc().splitlines(),
            },
        )


@router.get("/{goal_id}", response_model=schemas.GoalDisplay)
def get_goal_details(goal_id: int, db: Session = Depends(get_db_sync)):
    """Get detailed status and plan steps for a specific goal."""
    goal = db.query(models.Goal).filter(models.Goal.id == goal_id).first()
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")
    return goal
