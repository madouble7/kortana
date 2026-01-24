"""
API router for conversation history management with filtering and search.
"""

from datetime import datetime
from typing import Any

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from src.kortana.services.conversation_history import ConversationHistoryService

router = APIRouter(
    prefix="/conversations",
    tags=["Conversation History"],
)

# Initialize the service
conversation_service = ConversationHistoryService()


class CreateConversationRequest(BaseModel):
    """Request model for creating a conversation."""

    user_id: str | None = None
    tags: list[str] = Field(default_factory=list)


class AddMessageRequest(BaseModel):
    """Request model for adding a message to a conversation."""

    role: str = Field(..., pattern="^(user|assistant)$")
    content: str = Field(..., min_length=1)
    metadata: dict[str, Any] = Field(default_factory=dict)


class UpdateTagsRequest(BaseModel):
    """Request model for updating conversation tags."""

    tags: list[str]


@router.post("/", status_code=201)
def create_conversation(request: CreateConversationRequest):
    """Create a new conversation."""
    conversation = conversation_service.create_conversation(
        user_id=request.user_id,
        tags=request.tags,
    )
    return conversation.model_dump(mode="json")


@router.get("/{conversation_id}")
def get_conversation(conversation_id: str):
    """Get a specific conversation by ID."""
    conversation = conversation_service.get_conversation(conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conversation.model_dump(mode="json")


@router.delete("/{conversation_id}", status_code=204)
def delete_conversation(conversation_id: str):
    """Delete a conversation.

    This operation is idempotent: a 204 status is returned even if the
    conversation does not exist.
    """
    conversation_service.delete_conversation(conversation_id)
@router.post("/{conversation_id}/messages")
def add_message(conversation_id: str, request: AddMessageRequest):
    """Add a message to a conversation."""
    conversation = conversation_service.get_conversation(conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    conversation.add_message(
        role=request.role,
        content=request.content,
        metadata=request.metadata,
    )
    conversation_service.save_conversation(conversation)

    return conversation.model_dump(mode="json")


@router.get("/")
def list_conversations(
    user_id: str | None = Query(None, description="Filter by user ID"),
    tags: list[str] | None = Query(None, description="Filter by tags (OR condition)"),
    keywords: list[str] | None = Query(
        None, description="Filter by keywords in messages"
    ),
    min_engagement_rank: float | None = Query(
        None, ge=0.0, le=1.0, description="Minimum engagement rank"
    ),
    max_engagement_rank: float | None = Query(
        None, ge=0.0, le=1.0, description="Maximum engagement rank"
    ),
    start_date: datetime | None = Query(
        None, description="Filter conversations created after this date (ISO format)"
    ),
    end_date: datetime | None = Query(
        None, description="Filter conversations created before this date (ISO format)"
    ),
    limit: int | None = Query(None, ge=1, le=100, description="Maximum results"),
):
    """
    List conversations with advanced filtering.

    Supports filtering by:
    - user_id: Specific user
    - tags: Conversations with at least one matching tag
    - keywords: Messages containing any of the keywords
    - min_engagement_rank/max_engagement_rank: Engagement quality range
    - start_date/end_date: Creation date range
    - limit: Maximum number of results
    """
    conversations = conversation_service.list_conversations(
        user_id=user_id,
        tags=tags,
        keywords=keywords,
        min_engagement_rank=min_engagement_rank,
        max_engagement_rank=max_engagement_rank,
        start_date=start_date,
        end_date=end_date,
        limit=limit,
    )

    return {
        "total": len(conversations),
        "conversations": [c.model_dump(mode="json") for c in conversations],
    }


@router.post("/{conversation_id}/tags")
def add_tags(conversation_id: str, request: UpdateTagsRequest):
    """Add tags to a conversation."""
    success = conversation_service.add_tags(conversation_id, request.tags)
    if not success:
        raise HTTPException(status_code=404, detail="Conversation not found")

    conversation = conversation_service.get_conversation(conversation_id)
    return conversation.model_dump(mode="json")


@router.delete("/{conversation_id}/tags")
def remove_tags(conversation_id: str, request: UpdateTagsRequest):
    """Remove tags from a conversation."""
    success = conversation_service.remove_tags(conversation_id, request.tags)
    if not success:
        raise HTTPException(status_code=404, detail="Conversation not found")

    conversation = conversation_service.get_conversation(conversation_id)
    return conversation.model_dump(mode="json")


@router.get("/{conversation_id}/preview")
def get_preview(conversation_id: str, max_chars: int = Query(100, ge=10, le=500)):
    """Get a preview of a conversation."""
    preview = conversation_service.get_conversation_preview(conversation_id, max_chars)
    if preview is None:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return {"conversation_id": conversation_id, "preview": preview}


@router.get("/users/{user_id}/search")
def search_user_conversations(
    user_id: str,
    start_timestamp: datetime | None = Query(None, description="Start timestamp (ISO format)"),
    end_timestamp: datetime | None = Query(None, description="End timestamp (ISO format)"),
):
    """
    Search conversations for a specific user within a timestamp range.
    """
    conversations = conversation_service.search_by_user_timestamp(
        user_id=user_id,
        start_timestamp=start_timestamp,
        end_timestamp=end_timestamp,
    )

    return {
        "user_id": user_id,
        "total": len(conversations),
        "conversations": [c.model_dump(mode="json") for c in conversations],
    }


@router.get("/statistics")
def get_statistics():
    """Get statistics about stored conversations."""
    return conversation_service.get_statistics()
