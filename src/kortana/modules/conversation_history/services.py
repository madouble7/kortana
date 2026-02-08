"""Service layer for conversation history management."""
import gzip
import json
from datetime import datetime
from typing import Any

from sqlalchemy import func, or_
from sqlalchemy.orm import Session, joinedload

from . import models, schemas


class ConversationHistoryService:
    """Service for managing conversation history."""

    def __init__(self, db: Session):
        self.db = db

    def create_conversation(
        self, conversation_create: schemas.ConversationCreate
    ) -> models.Conversation:
        """Create a new conversation."""
        db_conversation = models.Conversation(**conversation_create.model_dump())
        self.db.add(db_conversation)
        self.db.commit()
        self.db.refresh(db_conversation)
        return db_conversation

    def add_message(
        self, conversation_id: int, message_create: schemas.ConversationMessageCreate
    ) -> models.ConversationMessage:
        """Add a message to a conversation."""
        # Verify conversation exists
        conversation = self.get_conversation_by_id(conversation_id)
        if not conversation:
            raise ValueError(f"Conversation {conversation_id} not found")

        db_message = models.ConversationMessage(
            conversation_id=conversation_id, **message_create.model_dump()
        )
        self.db.add(db_message)
        self.db.commit()
        self.db.refresh(db_message)
        return db_message

    def get_conversation_by_id(
        self, conversation_id: int, include_messages: bool = False
    ) -> models.Conversation | None:
        """Get a conversation by ID."""
        query = self.db.query(models.Conversation).filter(
            models.Conversation.id == conversation_id
        )

        if include_messages:
            query = query.options(joinedload(models.Conversation.messages))

        return query.first()

    def get_user_conversations(
        self, user_id: str, skip: int = 0, limit: int = 100
    ) -> list[models.Conversation]:
        """Get all conversations for a user."""
        return (
            self.db.query(models.Conversation)
            .filter(models.Conversation.user_id == user_id)
            .order_by(models.Conversation.updated_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def search_conversations(
        self, filters: schemas.ConversationSearchFilters, skip: int = 0, limit: int = 100
    ) -> list[models.Conversation]:
        """
        Advanced search for conversations with multiple filters.

        Supports filtering by:
        - User ID
        - Date range
        - Keyword in messages
        - Conversation length (message count)
        - Status
        """
        query = self.db.query(models.Conversation)

        # Apply user filter
        if filters.user_id:
            query = query.filter(models.Conversation.user_id == filters.user_id)

        # Apply date range filters
        if filters.start_date:
            query = query.filter(models.Conversation.created_at >= filters.start_date)
        if filters.end_date:
            query = query.filter(models.Conversation.created_at <= filters.end_date)

        # Apply status filter
        if filters.status:
            query = query.filter(models.Conversation.status == filters.status)

        # Apply keyword search in messages
        if filters.keyword:
            query = query.join(models.ConversationMessage).filter(
                models.ConversationMessage.content.ilike(f"%{filters.keyword}%")
            )

        # Apply length filters (message count)
        if filters.min_length is not None or filters.max_length is not None:
            # Add subquery to count messages
            message_count = (
                self.db.query(
                    models.ConversationMessage.conversation_id,
                    func.count(models.ConversationMessage.id).label("msg_count"),
                )
                .group_by(models.ConversationMessage.conversation_id)
                .subquery()
            )

            query = query.outerjoin(
                message_count, models.Conversation.id == message_count.c.conversation_id
            )

            if filters.min_length is not None:
                query = query.filter(
                    or_(
                        message_count.c.msg_count >= filters.min_length,
                        message_count.c.msg_count.is_(None),
                    )
                )
            if filters.max_length is not None:
                query = query.filter(
                    or_(
                        message_count.c.msg_count <= filters.max_length,
                        message_count.c.msg_count.is_(None),
                    )
                )

        # Order by most recent and apply pagination
        return (
            query.order_by(models.Conversation.updated_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def archive_conversation(self, conversation_id: int) -> models.Conversation | None:
        """Archive a conversation for long-term storage."""
        conversation = self.get_conversation_by_id(conversation_id, include_messages=True)
        if not conversation:
            return None

        # Update status and timestamp
        conversation.status = models.ConversationStatus.ARCHIVED
        conversation.archived_at = datetime.utcnow()

        # Optionally compress old messages in metadata for storage optimization
        if conversation.messages:
            # Store compressed message data
            message_data = [
                {
                    "role": msg.role,
                    "content": msg.content,
                    "created_at": msg.created_at.isoformat(),
                }
                for msg in conversation.messages
            ]
            compressed = gzip.compress(json.dumps(message_data).encode("utf-8"))
            if not conversation.metadata:
                conversation.metadata = {}
            conversation.metadata["compressed_messages"] = compressed.hex()
            conversation.metadata["compression_date"] = datetime.utcnow().isoformat()

        self.db.commit()
        self.db.refresh(conversation)
        return conversation

    def delete_conversation(self, conversation_id: int) -> bool:
        """Delete a conversation (soft delete)."""
        conversation = self.get_conversation_by_id(conversation_id)
        if not conversation:
            return False

        conversation.status = models.ConversationStatus.DELETED
        self.db.commit()
        return True

    def get_conversation_stats(self, conversation_id: int) -> dict[str, Any]:
        """Get statistics for a conversation."""
        conversation = self.get_conversation_by_id(conversation_id, include_messages=True)
        if not conversation:
            return {}

        messages = conversation.messages
        total_messages = len(messages)
        user_messages = sum(1 for msg in messages if msg.role == "user")
        assistant_messages = sum(1 for msg in messages if msg.role == "assistant")

        # Calculate average response time if metadata available
        avg_response_time = None
        response_times = [
            msg.metadata.get("response_time_ms")
            for msg in messages
            if msg.metadata and "response_time_ms" in msg.metadata
        ]
        if response_times:
            avg_response_time = sum(response_times) / len(response_times)

        return {
            "conversation_id": conversation_id,
            "total_messages": total_messages,
            "user_messages": user_messages,
            "assistant_messages": assistant_messages,
            "created_at": conversation.created_at,
            "updated_at": conversation.updated_at,
            "status": conversation.status.value,
            "average_response_time_ms": avg_response_time,
        }
