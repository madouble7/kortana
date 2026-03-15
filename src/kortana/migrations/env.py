import os
import sys
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool

from alembic import context

# This line allows for imports from the project root
sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
)


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
# --- KORTANA INTEGRATION START ---
from src.kortana.config.settings import settings  # Import settings for DB URL
from src.kortana.services.database import Base  # Import Base from your application

target_metadata = Base.metadata
# --- KORTANA INTEGRATION END ---

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
    # --- KORTANA INTEGRATION START ---
    url = settings.ALEMBIC_DATABASE_URL
    # --- KORTANA INTEGRATION END ---
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
    # --- KORTANA INTEGRATION START ---
    # This configuration section is modified to use Kortana's settings
    connectable_config = config.get_section(config.config_ini_section)
    if connectable_config is None:
        connectable_config = {}  # provide an empty dict if section not found
    connectable_config["sqlalchemy.url"] = settings.ALEMBIC_DATABASE_URL

    connectable = engine_from_config(
        connectable_config,  # Use the modified config
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    # --- KORTANA INTEGRATION END ---

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
