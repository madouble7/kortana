# --- MODIFICATION START ---
# Ensure the project root is in sys.path for imports
import sys
from logging.config import fileConfig
from pathlib import Path

from sqlalchemy import engine_from_config, pool

from alembic import context

project_root = str(Path(__file__).resolve().parents[1])
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from kortana.config.settings import settings  # Import your app settings
from kortana.services.database import Base  # Import your Base

# --- MODIFICATION END ---

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
# --- MODIFICATION START ---
target_metadata = Base.metadata  # Point to your app's Base.metadata
# --- MODIFICATION END ---

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
    # --- MODIFICATION START ---
    # Use the database URL from application settings
    url = settings.ALEMBIC_DATABASE_URL
    # --- MODIFICATION END ---
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
    # --- MODIFICATION START ---
    # Ensure alembic.ini's sqlalchemy.url is set to your app's DB URL
    # This makes engine_from_config use the correct URL
    db_url = settings.ALEMBIC_DATABASE_URL
    if not config.get_main_option("sqlalchemy.url"):
        config.set_main_option("sqlalchemy.url", db_url)

    # If your settings object directly provides engine parameters, you could use:
    # connectable = create_engine(settings.ALEMBIC_DATABASE_URL)
    # However, using engine_from_config is standard if alembic.ini is the source of truth

    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
        # Ensure the URL from settings is used if not overridden by alembic.ini
        # This might be redundant if set_main_option above works as expected
        # url=db_url
    )
    # --- MODIFICATION END ---

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
