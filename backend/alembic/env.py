import os
import sys
from logging.config import fileConfig

from alembic import context

# Add backend directory to sys.path so we can import config
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)

from sqlalchemy import engine_from_config, pool  # noqa: E402

# Import our models and config
from src.kortana.config import get_settings  # noqa: E402
from src.kortana.models import Base  # noqa: E402

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Get settings
settings = get_settings()

# Set sqlalchemy.url dynamically from settings
db_url = settings.DATABASE_URL
if "sqlite" in db_url:
    sync_url = db_url.replace("aiosqlite", "sqlite").replace("sqlite+sqlite", "sqlite")
else:
    sync_url = db_url.replace("+asyncpg", "")
    # Verify the sync driver is available; fall back to SQLite for local dev
    # when psycopg2 / psycopg isn't installed in the current environment.
    import importlib

    _has_sync_driver = (
        importlib.util.find_spec("psycopg2") is not None
        or importlib.util.find_spec("psycopg") is not None
    )
    if not _has_sync_driver:
        import os as _os

        if _os.getenv("ENVIRONMENT", "development") != "production":
            import warnings

            warnings.warn(
                "No sync Postgres driver (psycopg2/psycopg) found — "
                "running Alembic against local SQLite fallback. "
                "Install psycopg2-binary to run migrations against Postgres.",
                stacklevel=1,
            )
            sync_url = "sqlite:///./kortana.db"

config.set_main_option("sqlalchemy.url", sync_url)

# add your model's MetaData object here
# for 'autogenerate' support
target_metadata = Base.metadata

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


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
