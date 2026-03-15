"""Pydantic schemas for conversation history."""
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from .models import ConversationStatus


class ConversationMessageCreate(BaseModel):
    role: str = Field(..., description="Message role: user, assistant, or system")
    content: str = Field(..., min_length=1, description="Message content")
    metadata: dict[str, Any] | None = Field(None, description="Additional metadata")


class ConversationMessageResponse(BaseModel):
    id: int
    conversation_id: int
    role: str
    content: str
    metadata: dict[str, Any] | None
    created_at: datetime

    class Config:
        from_attributes = True


class ConversationCreate(BaseModel):
    user_id: str = Field(..., description="User identifier")
    title: str | None = Field(None, max_length=255, description="Conversation title")
    metadata: dict[str, Any] | None = Field(None, description="Additional metadata")


class ConversationUpdate(BaseModel):
    title: str | None = Field(None, max_length=255)
    status: ConversationStatus | None = None
    metadata: dict[str, Any] | None = None


class ConversationResponse(BaseModel):
    id: int
    user_id: str
    title: str | None
    status: ConversationStatus
    metadata: dict[str, Any] | None
    created_at: datetime
    updated_at: datetime
    archived_at: datetime | None
    message_count: int | None = None

    class Config:
        from_attributes = True


class ConversationWithMessages(ConversationResponse):
    messages: list[ConversationMessageResponse]


class ConversationSearchFilters(BaseModel):
    user_id: str | None = None
    start_date: datetime | None = None
    end_date: datetime | None = None
    keyword: str | None = None
    min_length: int | None = Field(None, ge=0, description="Minimum number of messages")
    max_length: int | None = Field(None, ge=0, description="Maximum number of messages")
    status: ConversationStatus | None = None
