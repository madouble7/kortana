import asyncio
import os

# Import Kortana settings and database
import sys
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "..", ".."))

# Import models for autogenerate support
from kortana.modules.memory_core.models import CoreMemory  # noqa: F401

from kortana.config.settings import settings
from kortana.services.database import Base

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
target_metadata = Base.metadata

# Configure the database URL from settings
# For SQLite, we'll use sync mode for migrations
db_url = settings.ALEMBIC_DATABASE_URL
if db_url.startswith("sqlite"):
    # Use sync mode for SQLite migrations
    config.set_main_option("sqlalchemy.url", db_url)
else:
    # For other databases, configure async
    alembic_config_dict = config.get_section(config.config_ini_section, {})
    alembic_config_dict["sqlalchemy.url"] = db_url

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""

    # Check if we're using SQLite (sync) or other database (async)
    db_url = config.get_main_option("sqlalchemy.url")

    if db_url and db_url.startswith("sqlite"):
        # Use sync engine for SQLite
        from sqlalchemy import create_engine

        connectable = create_engine(db_url)

        with connectable.connect() as connection:
            do_run_migrations(connection)
    else:
        # Use async engine for other databases
        asyncio.run(run_async_migrations())


async def run_async_migrations() -> None:
    """In this scenario we need to create an Engine
    and associate a connection with the context.

    """

    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
