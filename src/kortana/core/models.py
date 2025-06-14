import enum

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy import Enum as SQLAlchemyEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from src.kortana.services.database import Base


class GoalStatus(enum.Enum):
    PENDING = "pending"
    ACTIVE = "active"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Goal(Base):
    __tablename__ = "goals"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True)
    description = Column(Text, nullable=False)
    status = Column(
        SQLAlchemyEnum(GoalStatus), nullable=False, default=GoalStatus.PENDING
    )
    priority = Column(Integer, default=100)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)

    plan_steps = relationship(
        "PlanStep",
        back_populates="goal",
        cascade="all, delete-orphan",
        order_by="PlanStep.step_number",
    )


class PlanStep(Base):
    __tablename__ = "plan_steps"
    id = Column(Integer, primary_key=True, index=True)
    goal_id = Column(Integer, ForeignKey("goals.id"), nullable=False)
    step_number = Column(Integer, nullable=False)
    action_type = Column(String(50), nullable=False)
    parameters = Column(Text, nullable=False)
    status = Column(
        SQLAlchemyEnum(GoalStatus), nullable=False, default=GoalStatus.PENDING
    )
    result = Column(Text, nullable=True)

    goal = relationship("Goal", back_populates="plan_steps")
