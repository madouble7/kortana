"""Database models for inventory analysis."""
import enum

from sqlalchemy import JSON, Column, DateTime, Float, Integer, String, Text
from sqlalchemy import Enum as SQLAlchemyEnum
from sqlalchemy.sql import func

from src.kortana.services.database import Base


class StockStatus(enum.Enum):
    """Stock status indicators."""
    IN_STOCK = "in_stock"
    LOW_STOCK = "low_stock"
    OUT_OF_STOCK = "out_of_stock"
    OVERSTOCKED = "overstocked"


class Inventory(Base):
    """Inventory model for stock analysis."""
    __tablename__ = "inventory"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    product_name = Column(String(255), nullable=False, index=True)
    sku = Column(String(100), nullable=True, unique=True, index=True)
    quantity = Column(Integer, nullable=False, default=0)
    status = Column(
        SQLAlchemyEnum(StockStatus),
        nullable=False,
        index=True,
        default=StockStatus.IN_STOCK,
    )
    # Financial metrics from stock analysis
    pe_ratio = Column(Float, nullable=True)
    pb_ratio = Column(Float, nullable=True)
    de_ratio = Column(Float, nullable=True)
    roe = Column(Float, nullable=True)
    roa = Column(Float, nullable=True)
    recommendation = Column(String(50), nullable=True)  # "Buy" or "Do not buy"
    confidence_score = Column(Float, nullable=True)
    metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    def __repr__(self):
        return f"<Inventory(id={self.id}, product='{self.product_name}', status='{self.status}')>"
