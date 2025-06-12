from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from src.kortana.core.goal_framework import GoalType
from src.kortana.core.goal_manager import GoalManager
from src.kortana.modules.memory_core.services import MemoryCoreService
from src.kortana.services.database import get_db

router = APIRouter(prefix="/goals", tags=["Goal Management"])


class GoalCreate(BaseModel):
    description: str = Field(..., description="Goal description")
    priority: int = Field(default=100, description="Goal priority")


class GoalOut(BaseModel):
    id: int
    description: str
    status: str
    priority: int
    created_at: str | None = None
    completed_at: str | None = None

    class Config:
        orm_mode = True


@router.post("/", response_model=GoalOut)
def create_new_goal(goal_in: GoalCreate, db: Session = Depends(get_db)):
    memory_manager = MemoryCoreService(db)
    goal_manager = GoalManager(memory_manager=memory_manager)
    goal = goal_manager.create_goal(
        goal_type=GoalType.IMPROVEMENT,
        title=goal_in.description[:50],
        description=goal_in.description,
        priority=goal_in.priority,
    )
    return goal


@router.get("/", response_model=list[GoalOut])
def list_all_goals(db: Session = Depends(get_db)):
    memory_manager = MemoryCoreService(db)
    goal_manager = GoalManager(memory_manager=memory_manager)
    return goal_manager.prioritize_goals()
