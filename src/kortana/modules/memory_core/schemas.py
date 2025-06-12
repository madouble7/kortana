from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from .models import MemoryType


# --- MemorySentiment Schemas ---
class MemorySentimentBase(BaseModel):
    emotion: str = Field(
        ..., min_length=1, max_length=50, examples=["joy", "curiosity"]
    )
    intensity: int | None = Field(None, ge=1, le=10)
    source_text_span: dict[str, int] | None = Field(
        None, examples=[{"start": 10, "end": 25}]
    )


class MemorySentimentCreate(MemorySentimentBase):
    pass


class MemorySentimentDisplay(MemorySentimentBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


# --- CoreMemory Schemas ---
class CoreMemoryBase(BaseModel):
    memory_type: MemoryType = MemoryType.INTERACTION
    title: str | None = Field(None, max_length=255)
    content: str = Field(..., min_length=1)
    memory_metadata: dict[str, Any] | None = None  # Renamed from metadata
    related_to_id: int | None = None


class CoreMemoryCreate(CoreMemoryBase):
    sentiments: list[MemorySentimentCreate] | None = []


class CoreMemoryUpdate(BaseModel):
    memory_type: MemoryType | None = None
    title: str | None = Field(None, max_length=255)
    content: str | None = Field(None, min_length=1)
    memory_metadata: dict[str, Any] | None = None  # Renamed from metadata
    related_to_id: int | None = None


class CoreMemoryDisplay(CoreMemoryBase):
    id: int
    embedding: list[float] | None = None
    sentiments: list[MemorySentimentDisplay] = []
    created_at: datetime
    updated_at: datetime
    accessed_at: datetime

    class Config:
        from_attributes = True
