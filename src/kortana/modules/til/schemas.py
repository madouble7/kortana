"""Pydantic schemas for TIL (Today I Learned) module."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class TILNoteBase(BaseModel):
    """Base schema for TIL notes."""

    title: str = Field(..., min_length=1, max_length=255, description="Title of the TIL note")
    content: str = Field(..., min_length=1, description="Content of the TIL note")
    category: str = Field(..., min_length=1, max_length=100, description="Category of the note")
    tags: Optional[list[str]] = Field(default=None, description="Tags for categorization")
    source: str = Field(default="manual", description="Source of the note (manual, conversation, insight)")


class TILNoteCreate(TILNoteBase):
    """Schema for creating a new TIL note."""

    pass


class TILNoteUpdate(BaseModel):
    """Schema for updating a TIL note."""

    title: Optional[str] = Field(None, min_length=1, max_length=255)
    content: Optional[str] = Field(None, min_length=1)
    category: Optional[str] = Field(None, min_length=1, max_length=100)
    tags: Optional[list[str]] = None
    source: Optional[str] = None


class TILNoteDisplay(TILNoteBase):
    """Schema for displaying a TIL note."""

    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TILCategoryInfo(BaseModel):
    """Schema for category information."""

    category: str
    count: int
