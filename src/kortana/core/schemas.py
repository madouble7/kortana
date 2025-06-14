from datetime import datetime

from pydantic import BaseModel, Field

# Assuming GoalStatus is an Enum defined elsewhere, e.g., in models.py
# from .models import GoalStatus

class GoalCreate(BaseModel):
    """Schema for creating a new Goal."""
    description: str = Field(..., description="Goal description")
    priority: int = Field(default=100, description="Goal priority")

class GoalDisplay(BaseModel):
    """Schema for displaying a Goal."""
    id: int
    description: str
    # Assuming GoalStatus is a string value in the API response
    status: str
    priority: int
    created_at: datetime # Use datetime type hint for automatic serialization
    completed_at: datetime | None = None

    class Config:
        from_attributes = True # Enable mapping from SQLAlchemy models
