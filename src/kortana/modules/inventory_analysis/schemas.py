"""Pydantic schemas for inventory analysis."""
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from .models import StockStatus


class InventoryBase(BaseModel):
    """Base inventory schema."""
    product_name: str = Field(..., min_length=1, max_length=255)
    sku: str | None = Field(None, max_length=100)
    quantity: int = Field(default=0, ge=0)


class InventoryCreate(InventoryBase):
    """Schema for creating inventory."""
    status: StockStatus = StockStatus.IN_STOCK
    inventory_metadata: dict[str, Any] | None = None


class InventoryAnalysisRequest(BaseModel):
    """Schema for inventory analysis request with financial metrics."""
    product_name: str = Field(..., min_length=1, max_length=255)
    pe_ratio: float = Field(..., description="Price to Earnings ratio")
    pb_ratio: float = Field(..., description="Price to Book ratio")
    de_ratio: float = Field(..., description="Debt to Equity ratio")
    roe: float = Field(..., description="Return on Equity")
    roa: float = Field(..., description="Return on Assets")


class InventoryAnalysisResponse(BaseModel):
    """Schema for inventory analysis response."""
    recommendation: str = Field(..., description="Buy or Do not buy")
    confidence_score: float = Field(..., ge=0.0, le=1.0)
    analysis: str | None = None


class InventoryDisplay(InventoryBase):
    """Schema for displaying inventory."""
    id: int
    status: StockStatus
    pe_ratio: float | None
    pb_ratio: float | None
    de_ratio: float | None
    roe: float | None
    roa: float | None
    recommendation: str | None
    confidence_score: float | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class InventoryUpdate(BaseModel):
    """Schema for updating inventory."""
    product_name: str | None = Field(None, min_length=1, max_length=255)
    sku: str | None = Field(None, max_length=100)
    quantity: int | None = Field(None, ge=0)
    status: StockStatus | None = None
    inventory_metadata: dict[str, Any] | None = None
