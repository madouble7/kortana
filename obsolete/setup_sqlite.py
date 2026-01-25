import os
import sys

from sqlalchemy import create_engine

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), "backend"))

from config import get_settings
from models import Base


def setup_sqlite():
    settings = get_settings()
    db_url = settings.DATABASE_URL

    if "sqlite" not in db_url:
        print(f"Error: DATABASE_URL is not SQLite: {db_url}")
        return

    # Construct sync URL for table creation
    sync_url = db_url.replace("aiosqlite", "sqlite").replace("sqlite+sqlite", "sqlite")
    print(f"Initializing SQLite database at: {sync_url}")

    try:
        engine = create_engine(sync_url)
        Base.metadata.create_all(engine)
        print("Successfully created all tables in SQLite.")
    except Exception as e:
        print(f"Error creating tables: {e}")


if __name__ == "__main__":
    setup_sqlite()
