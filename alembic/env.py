import os
import sys
from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool
from alembic import context

# --- 1. DYNAMIC PATH CONFIGURATION ---
# Ensures Python finds 'database.py' and 'core/' in the root folder
sys.path.append(os.getcwd())

# --- 2. IMPORT HARDENED SETTINGS AND BASE ---
from core.settings import settings
from database import Base 
import models  # Important: This registers your SQLAlchemy classes

# Alembic Config object
config = context.config

# Setup standard Alembic logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Set the metadata for autogenerate support
target_metadata = Base.metadata

def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode (using URL only)."""
    # Use the hardened Neon URL even in offline mode
    url = settings.DATABASE_URL
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
    """Run migrations in 'online' mode (Actual DB Connection)."""
    
    # --- 3. DYNAMIC CONFIGURATION OVERRIDE ---
    # We ignore alembic.ini's URL and use the NEON URL from settings.py
    configuration = config.get_section(config.config_ini_section, {})
    configuration["sqlalchemy.url"] = settings.DATABASE_URL
    
    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, 
            target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()