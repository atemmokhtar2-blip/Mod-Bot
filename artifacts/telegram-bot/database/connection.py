"""
Database connection and session management.
Uses SQLAlchemy 2.x async engine + session factory.
Future: read-replica support, connection pooling tuning, pgBouncer.
"""

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

engine: AsyncEngine = create_async_engine(
    _config.database_url,
    echo=False,          # set True for SQL query logging in dev
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,  # detect stale connections
    # Replit's internal Postgres does not use SSL; disable it explicitly
    connect_args={"ssl": None},
)

async_session: async_sessionmaker[AsyncSession] = async_sessionmaker(
    engine,
    expire_on_commit=False,
    class_=AsyncSession,
)


async def init_db() -> None:
    """Create all tables that do not yet exist."""
    from database.models import Base  # avoid circular import at module level

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    log.info("Database tables initialised.")
