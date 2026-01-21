"""
Conversation History Service with enhanced filtering, tags, and search capabilities.
Implements persistent conversation storage with metadata tracking.
"""

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field


class ConversationMessage(BaseModel):
    """Individual message in a conversation."""

    role: str  # "user" or "assistant"
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: dict[str, Any] = Field(default_factory=dict)


class Conversation(BaseModel):
    """Represents a complete conversation with metadata."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str | None = None
    messages: list[ConversationMessage] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    engagement_rank: float = 0.0  # 0.0 to 1.0 based on interaction quality
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: dict[str, Any] = Field(default_factory=dict)

    def add_message(self, role: str, content: str, metadata: dict[str, Any] | None = None):
        """Add a message to the conversation."""
        message = ConversationMessage(
            role=role,
            content=content,
            metadata=metadata or {},
        )
        self.messages.append(message)
        self.updated_at = datetime.utcnow()
        self._update_engagement_rank()

    def _update_engagement_rank(self):
        """Update engagement rank based on conversation metrics."""
        if not self.messages:
            self.engagement_rank = 0.0
            return

        # Simple heuristic: longer conversations with varied content get higher rank
        message_count = len(self.messages)
        avg_length = sum(len(m.content) for m in self.messages) / message_count
        unique_words = len(set(" ".join(m.content for m in self.messages).split()))

        # Normalize to 0-1 range
        count_score = min(message_count / 20, 1.0)  # Max at 20 messages
        length_score = min(avg_length / 200, 1.0)  # Max at 200 chars avg
        diversity_score = min(unique_words / 100, 1.0)  # Max at 100 unique words

        self.engagement_rank = (count_score + length_score + diversity_score) / 3


class ConversationHistoryService:
    """Service for managing conversation history with advanced filtering."""

    def __init__(self, storage_path: str | Path = "data/conversations"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)

    def create_conversation(
        self, user_id: str | None = None, tags: list[str] | None = None
    ) -> Conversation:
        """Create a new conversation."""
        conversation = Conversation(user_id=user_id, tags=tags or [])
        self.save_conversation(conversation)
        return conversation

    def get_conversation(self, conversation_id: str) -> Conversation | None:
        """Retrieve a conversation by ID."""
        file_path = self.storage_path / f"{conversation_id}.json"
        if not file_path.exists():
            return None

        with open(file_path, "r") as f:
            data = json.load(f)
            return Conversation.model_validate(data)

    def save_conversation(self, conversation: Conversation) -> None:
        """Save a conversation to storage."""
        file_path = self.storage_path / f"{conversation.id}.json"
        with open(file_path, "w") as f:
            json.dump(conversation.model_dump(mode="json"), f, indent=2, default=str)

    def delete_conversation(self, conversation_id: str) -> bool:
        """Delete a conversation."""
        file_path = self.storage_path / f"{conversation_id}.json"
        if file_path.exists():
            file_path.unlink()
            return True
        return False

    def list_conversations(
        self,
        user_id: str | None = None,
        tags: list[str] | None = None,
        keywords: list[str] | None = None,
        min_engagement_rank: float | None = None,
        max_engagement_rank: float | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        limit: int | None = None,
    ) -> list[Conversation]:
        """
        List conversations with advanced filtering.

        Args:
            user_id: Filter by user ID
            tags: Filter by tags (conversations must have at least one of these tags)
            keywords: Filter by keywords in message content
            min_engagement_rank: Minimum engagement rank
            max_engagement_rank: Maximum engagement rank
            start_date: Filter conversations created after this date
            end_date: Filter conversations created before this date
            limit: Maximum number of results to return

        Returns:
            List of matching conversations
        """
        conversations = []

        # Load all conversations
        for file_path in self.storage_path.glob("*.json"):
            try:
                with open(file_path, "r") as f:
                    data = json.load(f)
                    conv = Conversation.model_validate(data)
                    conversations.append(conv)
            except Exception as e:
                print(f"Error loading conversation {file_path}: {e}")
                continue

        # Apply filters
        filtered = conversations

        if user_id is not None:
            filtered = [c for c in filtered if c.user_id == user_id]

        if tags:
            filtered = [c for c in filtered if any(tag in c.tags for tag in tags)]

        if keywords:
            keywords_lower = [k.lower() for k in keywords]
            filtered = [
                c
                for c in filtered
                if any(
                    any(kw in msg.content.lower() for kw in keywords_lower)
                    for msg in c.messages
                )
            ]

        if min_engagement_rank is not None:
            filtered = [c for c in filtered if c.engagement_rank >= min_engagement_rank]

        if max_engagement_rank is not None:
            filtered = [c for c in filtered if c.engagement_rank <= max_engagement_rank]

        if start_date is not None:
            filtered = [c for c in filtered if c.created_at >= start_date]

        if end_date is not None:
            filtered = [c for c in filtered if c.created_at <= end_date]

        # Sort by updated_at (most recent first)
        filtered.sort(key=lambda c: c.updated_at, reverse=True)

        # Apply limit
        if limit:
            filtered = filtered[:limit]

        return filtered

    def add_tags(self, conversation_id: str, tags: list[str]) -> bool:
        """Add tags to a conversation."""
        conversation = self.get_conversation(conversation_id)
        if not conversation:
            return False

        # Add unique tags
        for tag in tags:
            if tag not in conversation.tags:
                conversation.tags.append(tag)

        conversation.updated_at = datetime.utcnow()
        self.save_conversation(conversation)
        return True

    def remove_tags(self, conversation_id: str, tags: list[str]) -> bool:
        """Remove tags from a conversation."""
        conversation = self.get_conversation(conversation_id)
        if not conversation:
            return False

        conversation.tags = [t for t in conversation.tags if t not in tags]
        conversation.updated_at = datetime.utcnow()
        self.save_conversation(conversation)
        return True

    def search_by_user_timestamp(
        self,
        user_id: str,
        start_timestamp: datetime | None = None,
        end_timestamp: datetime | None = None,
    ) -> list[Conversation]:
        """
        Search conversations for a specific user within a timestamp range.

        Args:
            user_id: User ID to filter by
            start_timestamp: Start of timestamp range
            end_timestamp: End of timestamp range

        Returns:
            List of matching conversations
        """
        return self.list_conversations(
            user_id=user_id,
            start_date=start_timestamp,
            end_date=end_timestamp,
        )

    def get_conversation_preview(self, conversation_id: str, max_chars: int = 100) -> str | None:
        """Get a preview of a conversation (first message or summary)."""
        conversation = self.get_conversation(conversation_id)
        if not conversation or not conversation.messages:
            return None

        first_message = conversation.messages[0].content
        if len(first_message) <= max_chars:
            return first_message

        return first_message[:max_chars] + "..."

    def get_statistics(self) -> dict[str, Any]:
        """Get statistics about stored conversations."""
        conversations = self.list_conversations()

        if not conversations:
            return {
                "total_conversations": 0,
                "total_messages": 0,
                "avg_engagement_rank": 0.0,
                "unique_users": 0,
                "unique_tags": [],
            }

        total_messages = sum(len(c.messages) for c in conversations)
        avg_engagement = sum(c.engagement_rank for c in conversations) / len(conversations)
        unique_users = len(set(c.user_id for c in conversations if c.user_id))
        all_tags = set()
        for c in conversations:
            all_tags.update(c.tags)

        return {
            "total_conversations": len(conversations),
            "total_messages": total_messages,
            "avg_engagement_rank": round(avg_engagement, 3),
            "unique_users": unique_users,
            "unique_tags": sorted(list(all_tags)),
        }
