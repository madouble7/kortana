from sqlalchemy import Column, Integer, String, DateTime, Text
from sqlalchemy.sql import func
from src.kortana.services.database import Base


class CoreMemory(Base):
    __tablename__ = "core_memories"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False, index=True)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    def __repr__(self):
        return f"<CoreMemory(id={self.id}, title='{self.title[:30]}...')>"
