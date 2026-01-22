"""Database models for recommendation engine."""
from sqlalchemy import JSON, Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from src.kortana.services.database import Base


class UserPreference(Base):
    """User preference model for recommendations."""
    __tablename__ = "user_preferences"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(String(255), nullable=False, index=True)
    preferences = Column(JSON, nullable=True)
    embedding = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    def __repr__(self):
        return f"<UserPreference(id={self.id}, user_id='{self.user_id}')>"


class Recommendation(Base):
    """Recommendation model."""
    __tablename__ = "recommendations"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(String(255), nullable=False, index=True)
    product_id = Column(Integer, nullable=True, index=True)
    product_name = Column(String(255), nullable=False)
    recommendation_score = Column(Float, nullable=False)
    reasoning = Column(Text, nullable=True)
    metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return f"<Recommendation(id={self.id}, user='{self.user_id}', product='{self.product_name}', score={self.recommendation_score})>"
