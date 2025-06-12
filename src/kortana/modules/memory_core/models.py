import enum

from sqlalchemy import JSON, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy import Enum as SQLAlchemyEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from src.kortana.services.database import Base


class MemoryType(enum.Enum):
    INTERACTION = "interaction"
    OBSERVATION = "observation"
    LEARNED_FACT = "learned_fact"
    PERSONAL_PREFERENCE = "personal_preference"
    EMOTIONAL_RESONANCE = "emotional_resonance"
    CORE_BELIEF = "core_belief"


class CoreMemory(Base):
    __tablename__ = "core_memories"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    memory_type = Column(
        SQLAlchemyEnum(MemoryType),
        nullable=False,
        index=True,
        default=MemoryType.INTERACTION,
    )
    title = Column(String(255), nullable=True, index=True)
    content = Column(Text, nullable=False)
    embedding = Column(JSON, nullable=True)
    memory_metadata = Column(JSON, nullable=True)  # Renamed from metadata
    sentiments = relationship(
        "MemorySentiment", back_populates="memory", cascade="all, delete-orphan"
    )
    related_to_id = Column(Integer, ForeignKey("core_memories.id"), nullable=True)
    related_from = relationship(
        "CoreMemory", remote_side=[id], backref="related_to_links"
    )
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    accessed_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    def __repr__(self):
        return f"<CoreMemory(id={self.id}, type='{self.memory_type.value}', title='{self.title[:30]}...')>"


class MemorySentiment(Base):
    __tablename__ = "memory_sentiments"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    memory_id = Column(Integer, ForeignKey("core_memories.id"), nullable=False)
    emotion = Column(String(50), nullable=False, index=True)
    intensity = Column(Integer, nullable=True)
    source_text_span = Column(JSON, nullable=True)
    memory = relationship("CoreMemory", back_populates="sentiments")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return f"<MemorySentiment(id={self.id}, memory_id={self.memory_id}, emotion='{self.emotion}')>"
