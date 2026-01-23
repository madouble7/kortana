"""Pydantic schemas for recommendation engine."""
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class UserPreferenceBase(BaseModel):
    """Base user preference schema."""
    user_id: str = Field(..., min_length=1, max_length=255)
    preferences: dict[str, Any] | None = None


class UserPreferenceCreate(UserPreferenceBase):
    """Schema for creating user preference."""
    pass


class UserPreferenceDisplay(UserPreferenceBase):
    """Schema for displaying user preference."""
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class RecommendationRequest(BaseModel):
    """Schema for recommendation request."""
    user_id: str = Field(..., min_length=1, max_length=255)
    query: str | None = Field(None, description="User query or context")
    limit: int = Field(default=5, ge=1, le=50)


class RecommendationItem(BaseModel):
    """Schema for a single recommendation."""
    product_id: int | None
    product_name: str
    recommendation_score: float = Field(..., ge=0.0, le=1.0)
    reasoning: str | None


class RecommendationResponse(BaseModel):
    """Schema for recommendation response."""
    user_id: str
    recommendations: list[RecommendationItem]
    query: str | None


class RecommendationDisplay(BaseModel):
    """Schema for displaying a recommendation."""
    id: int
    user_id: str
    product_id: int | None
    product_name: str
    recommendation_score: float
    reasoning: str | None
    created_at: datetime

    class Config:
        from_attributes = True
