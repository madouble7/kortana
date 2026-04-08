#!/usr/bin/env python3
"""Database initialization and setup"""

import asyncio
import os
import sys

import asyncpg

sys.path.insert(0, os.path.dirname(__file__))

from src.kortana.config import get_settings


async def init_db():
    """Initialize database connection and create tables"""
    settings = get_settings()

    print("\n" + "=" * 60)
    print("DATABASE INITIALIZATION")
    print("=" * 60)

    print("\n[1] Database Configuration:")
    print(f"    Host: {settings.DB_HOST}")
    print(f"    Port: {settings.DB_PORT}")
    print(f"    Database: {settings.DB_NAME}")
    print(f"    User: {settings.DB_USER}")

    print("\n[2] Checking PostgreSQL Connection...")
    try:
        # Try to connect to target database
        try:
            conn = await asyncpg.connect(
                host=settings.DB_HOST,
                port=settings.DB_PORT,
                user=settings.DB_USER,
                password=settings.DB_PASSWORD,
                database=settings.DB_NAME,
                timeout=5,
            )
            print(f"    ✓ Connection to '{settings.DB_NAME}' successful")
            await conn.close()
        except asyncpg.InvalidCatalogNameError:
            print(
                f"    ⚠ Database '{settings.DB_NAME}' not found. Attempting to create..."
            )
            # Connect to default 'postgres' database to create the new one
            sys_conn = await asyncpg.connect(
                host=settings.DB_HOST,
                port=settings.DB_PORT,
                user=settings.DB_USER,
                password=settings.DB_PASSWORD,
                database="postgres",
                timeout=5,
            )
            # DATABASE CREATION cannot be run in a transaction block
            await sys_conn.execute(f'CREATE DATABASE "{settings.DB_NAME}"')
            await sys_conn.close()
            print(f"    ✓ Database '{settings.DB_NAME}' created successfully")

        # Verify connection again
        conn = await asyncpg.connect(
            host=settings.DB_HOST,
            port=settings.DB_PORT,
            user=settings.DB_USER,
            password=settings.DB_PASSWORD,
            database=settings.DB_NAME,
            timeout=5,
        )

        version = await conn.fetchval("SELECT version()")
        await conn.close()

        print("    ✓ All connections verified")
        print(f"    ✓ PostgreSQL version: {version.split(',')[0]}")
        return True

    except ImportError:
        print("    ⓘ asyncpg not installed")
        print("       Install with: pip install asyncpg")
        return False
    except ConnectionRefusedError:
        print("    ✗ Connection refused")
        print(f"       Is PostgreSQL running on {settings.DB_HOST}:{settings.DB_PORT}?")
        return False
    except asyncpg.InvalidCatalogNameError:
        print(f"    ⚠ Database '{settings.DB_NAME}' not found")
        print("       You may need to create it with:")
        print(f"       createdb -U {settings.DB_USER} {settings.DB_NAME}")
        return False
    except Exception as e:
        print(f"    ✗ Connection error: {e}")
        return False


def print_next_steps():
    """Print instructions for next steps"""
    print("\n" + "=" * 60)
    print("NEXT STEPS")
    print("=" * 60)

    print(
        """
[1] Start PostgreSQL
    Windows (WSL): sudo service postgresql start
    Docker: docker run --name kortana-db -e POSTGRES_PASSWORD=supersecretpassword -p 5432:5432 postgres:16

[2] Create database
    createdb -U postgres kortana

[3] Install SQLAlchemy and Alembic
    pip install sqlalchemy alembic

[4] Create initial migration
    alembic init alembic

[5] Run migrations
    alembic upgrade head

[6] Initialize Redis (separate)
    docker run --name kortana-redis -p 6379:6379 redis:7

[7] Start backend with database
    python -m uvicorn src.kortana.main:app --reload
    """
    )


async def main():
    success = await init_db()
    print_next_steps()

    if success:
        print("\n✓ Database ready for migration setup!")
    else:
        print("\n⚠ Database connection failed - see instructions above")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nSetup cancelled")
        sys.exit(0)
