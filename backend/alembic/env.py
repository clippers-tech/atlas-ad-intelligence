"""Alembic async environment for ATLAS migrations."""

import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy.ext.asyncio import create_async_engine

# Import the shared Base so target_metadata is populated
from app.database import Base  # noqa: F401

# Import all models so Alembic autogenerate can detect every table
import app.models  # noqa: F401 — registers all 22 model classes on Base.metadata

# Import settings to override sqlalchemy.url at runtime
from app.config import settings

# ---------------------------------------------------------------------------
# Alembic Config object — gives access to values in alembic.ini
# ---------------------------------------------------------------------------
config = context.config

# Interpret the config file's logging section, if present.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Override the URL from application settings (honours DATABASE_URL env var)
config.set_main_option("sqlalchemy.url", settings.database_url)

# The metadata object that Alembic compares against the live DB schema.
target_metadata = Base.metadata


# ---------------------------------------------------------------------------
# Offline migrations  (alembic upgrade head --sql)
# ---------------------------------------------------------------------------
def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL rather than an Engine, which
    skips the need for a real database connection.  Calls to context.execute()
    here emit the given string to the script output.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


# ---------------------------------------------------------------------------
# Online migrations  (alembic upgrade head)
# ---------------------------------------------------------------------------
def do_run_migrations(connection) -> None:
    """Configure the context and run migrations within a transaction."""
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Create an async engine, connect, and run migrations."""
    connectable = create_async_engine(
        settings.database_url,
        future=True,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Entry point for online migration mode."""
    asyncio.run(run_async_migrations())


# ---------------------------------------------------------------------------
# Dispatch
# ---------------------------------------------------------------------------
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
