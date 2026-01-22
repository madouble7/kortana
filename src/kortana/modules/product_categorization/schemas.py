"""Pydantic schemas for product categorization."""
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from .models import CategoryType


class ProductBase(BaseModel):
    """Base product schema."""
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None


class ProductCreate(ProductBase):
    """Schema for creating a product."""
    category: CategoryType | None = None
    product_metadata: dict[str, Any] | None = None


class ProductCategorizeRequest(BaseModel):
    """Schema for categorization request."""
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None


class ProductCategorizeResponse(BaseModel):
    """Schema for categorization response."""
    category: CategoryType
    confidence_score: float = Field(..., ge=0.0, le=1.0)
    reasoning: str | None = None


class ProductDisplay(ProductBase):
    """Schema for displaying product."""
    id: int
    category: CategoryType | None
    confidence_score: float | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ProductUpdate(BaseModel):
    """Schema for updating a product."""
    name: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None
    category: CategoryType | None = None
    product_metadata: dict[str, Any] | None = None
