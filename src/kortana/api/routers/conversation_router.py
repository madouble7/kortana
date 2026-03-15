"""API router for conversation history endpoints."""
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from kortana.modules.conversation_history import models, schemas, services
from kortana.services.database import get_db_sync

router = APIRouter(
    prefix="/conversations",
    tags=["Conversation History"],
)


@router.post("/", response_model=schemas.ConversationResponse, status_code=201)
def create_conversation(
    conversation: schemas.ConversationCreate,
    db: Session = Depends(get_db_sync)
):
    """Create a new conversation."""
    service = services.ConversationHistoryService(db)
    db_conversation = service.create_conversation(conversation)
    
    # Add message count
    response_data = schemas.ConversationResponse.model_validate(db_conversation)
    response_data.message_count = 0
    return response_data


@router.post("/{conversation_id}/messages", response_model=schemas.ConversationMessageResponse, status_code=201)
def add_message(
    conversation_id: int,
    message: schemas.ConversationMessageCreate,
    db: Session = Depends(get_db_sync)
):
    """Add a message to a conversation."""
    service = services.ConversationHistoryService(db)
    try:
        db_message = service.add_message(conversation_id, message)
        return db_message
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/{conversation_id}", response_model=schemas.ConversationWithMessages)
def get_conversation(
    conversation_id: int,
    db: Session = Depends(get_db_sync)
):
    """Get a conversation by ID with all messages."""
    service = services.ConversationHistoryService(db)
    conversation = service.get_conversation_by_id(conversation_id, include_messages=True)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conversation


@router.get("/", response_model=list[schemas.ConversationResponse])
def list_conversations(
    user_id: str = Query(..., description="User identifier"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db_sync)
):
    """List conversations for a user."""
    service = services.ConversationHistoryService(db)
    conversations = service.get_user_conversations(user_id, skip=skip, limit=limit)
    
    # Add message counts
    results = []
    for conv in conversations:
        conv_data = schemas.ConversationResponse.model_validate(conv)
        conv_data.message_count = len(conv.messages) if conv.messages else 0
        results.append(conv_data)
    
    return results


@router.post("/search", response_model=list[schemas.ConversationResponse])
def search_conversations(
    filters: schemas.ConversationSearchFilters,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db_sync)
):
    """
    Advanced search for conversations with multiple filters.
    
    Supports filtering by:
    - User ID
    - Date range (start_date, end_date)
    - Keyword in messages
    - Conversation length (min_length, max_length in message count)
    - Status
    """
    service = services.ConversationHistoryService(db)
    conversations = service.search_conversations(filters, skip=skip, limit=limit)
    
    # Add message counts
    results = []
    for conv in conversations:
        conv_data = schemas.ConversationResponse.model_validate(conv)
        conv_data.message_count = len(conv.messages) if conv.messages else 0
        results.append(conv_data)
    
    return results


@router.post("/{conversation_id}/archive", response_model=schemas.ConversationResponse)
def archive_conversation(
    conversation_id: int,
    db: Session = Depends(get_db_sync)
):
    """Archive a conversation for long-term storage with compression."""
    service = services.ConversationHistoryService(db)
    conversation = service.archive_conversation(conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    conv_data = schemas.ConversationResponse.model_validate(conversation)
    conv_data.message_count = len(conversation.messages) if conversation.messages else 0
    return conv_data


@router.delete("/{conversation_id}", status_code=204)
def delete_conversation(
    conversation_id: int,
    db: Session = Depends(get_db_sync)
):
    """Delete a conversation (soft delete)."""
    service = services.ConversationHistoryService(db)
    success = service.delete_conversation(conversation_id)
    if not success:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return None


@router.get("/{conversation_id}/stats", response_model=dict[str, Any])
def get_conversation_stats(
    conversation_id: int,
    db: Session = Depends(get_db_sync)
):
    """Get statistics for a conversation including message counts and performance metrics."""
    service = services.ConversationHistoryService(db)
    stats = service.get_conversation_stats(conversation_id)
    if not stats:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return stats
