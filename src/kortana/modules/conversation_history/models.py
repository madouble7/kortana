"""Database models for conversation history."""
import enum

from sqlalchemy import JSON, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy import Enum as SQLAlchemyEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from src.kortana.services.database import Base


class ConversationStatus(enum.Enum):
    ACTIVE = "active"
    ARCHIVED = "archived"
    DELETED = "deleted"


class Conversation(Base):
    """Represents a conversation session."""
    __tablename__ = "conversations"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(String(255), nullable=False, index=True)
    title = Column(String(255), nullable=True)
    status = Column(
        SQLAlchemyEnum(ConversationStatus),
        nullable=False,
        default=ConversationStatus.ACTIVE,
        index=True,
    )
    metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    archived_at = Column(DateTime(timezone=True), nullable=True, index=True)
    
    # Relationship to messages
    messages = relationship(
        "ConversationMessage",
        back_populates="conversation",
        cascade="all, delete-orphan",
        order_by="ConversationMessage.created_at",
    )

    def __repr__(self):
        return f"<Conversation(id={self.id}, user_id='{self.user_id}', status='{self.status.value}')>"


class ConversationMessage(Base):
    """Represents a message in a conversation."""
    __tablename__ = "conversation_messages"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"), nullable=False, index=True)
    role = Column(String(50), nullable=False, index=True)  # user, assistant, system
    content = Column(Text, nullable=False)
    metadata = Column(JSON, nullable=True)  # Store performance stats, etc.
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    # Relationship to conversation
    conversation = relationship("Conversation", back_populates="messages")

    def __repr__(self):
        return f"<ConversationMessage(id={self.id}, conversation_id={self.conversation_id}, role='{self.role}')>"
