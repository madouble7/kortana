"""Database models for product categorization."""
import enum

from sqlalchemy import JSON, Column, DateTime, Float, Integer, String, Text
from sqlalchemy import Enum as SQLAlchemyEnum
from sqlalchemy.sql import func

from src.kortana.services.database import Base


class CategoryType(enum.Enum):
    """Product category types."""
    ELECTRONICS = "electronics"
    FASHION = "fashion"
    HOME = "home"
    FOOD = "food"
    BOOKS = "books"
    SPORTS = "sports"
    HEALTH = "health"
    AUTOMOTIVE = "automotive"
    OTHER = "other"


class Product(Base):
    """Product model for categorization."""
    __tablename__ = "products"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    category = Column(
        SQLAlchemyEnum(CategoryType),
        nullable=True,
        index=True,
    )
    confidence_score = Column(Float, nullable=True)
    embedding = Column(JSON, nullable=True)
    metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    def __repr__(self):
        return f"<Product(id={self.id}, name='{self.name[:30]}...', category='{self.category}')>"
