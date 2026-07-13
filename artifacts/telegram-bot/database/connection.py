"""
Database connection and session management.
Uses SQLAlchemy 2.x async engine + session factory.
Future: read-replica support, connection pooling tuning, pgBouncer.
"""

import os

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from config import load_config
from utils.logger import get_logger

log = get_logger(__name__)

_config = load_config()

# SSL control:
#   DATABASE_SSL=false  → disable SSL (Replit internal Postgres, local dev)
#   DATABASE_SSL=true   → enable SSL  (Zeabur, Supabase, Railway, etc.)
#   unset               → disable SSL (safe default for most VPS/internal DBs)
_ssl_env = os.environ.get("DATABASE_SSL", "false").strip().lower()
_ssl = True if _ssl_env == "true" else None

engine: AsyncEngine = create_async_engine(
    _config.database_url,
    echo=False,          # set True for SQL query logging in dev
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,  # detect stale connections
    connect_args={"ssl": _ssl},
)

async_session: async_sessionmaker[AsyncSession] = async_sessionmaker(
    engine,
    expire_on_commit=False,
    class_=AsyncSession,
)


async def init_db() -> None:
    """Create all tables that do not yet exist, then apply safe column migrations."""
    from database.models import Base  # avoid circular import at module level

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # V3 safe column migrations — ADD COLUMN IF NOT EXISTS is idempotent.
    migrations = [
        "ALTER TABLE group_settings ADD COLUMN IF NOT EXISTS auto_protect_enabled BOOLEAN DEFAULT FALSE",
        "ALTER TABLE statistics ADD COLUMN IF NOT EXISTS warned_members INTEGER DEFAULT 0",
    ]
    async with engine.begin() as conn:
        for sql in migrations:
            try:
                await conn.execute(__import__("sqlalchemy").text(sql))
            except Exception as exc:
                log.warning("Migration skipped: %s", exc)

    log.info("Database tables initialised.")
