from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from src.kortana.config.settings import settings

sync_engine = create_engine(settings.ALEMBIC_DATABASE_URL, echo=True)
SyncSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=sync_engine)
Base = declarative_base()


def get_db_sync():
    db = SyncSessionLocal()
    try:
        yield db
    finally:
        db.close()
