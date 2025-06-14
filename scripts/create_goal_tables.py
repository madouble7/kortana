#!/usr/bin/env python3
"""
Create Goal and PlanStep tables for Kor'tana
"""

from src.kortana.core.models import Goal, PlanStep
from src.kortana.services.database import Base, sync_engine


def create_tables():
    """Create all tables defined in the models"""
    print("Creating Goal and PlanStep tables...")

    # Import models to register them with Base
    _ = Goal, PlanStep

    # Create all tables
    Base.metadata.create_all(bind=sync_engine)

    print("✅ Tables created successfully!")

    # List the created tables
    from sqlalchemy import inspect

    inspector = inspect(sync_engine)
    tables = inspector.get_table_names()
    print(f"Available tables: {tables}")


if __name__ == "__main__":
    create_tables()
