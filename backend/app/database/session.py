"""
Async SQLAlchemy engine and session factory.

Uses NullPool so every request gets a fresh connection from Supabase's
connection pooler (pgbouncer). This avoids pool_size / max_overflow
issues when connecting through the Supabase Transaction or Session pooler.
"""

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.core.config import settings

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    pool_pre_ping=True,
    # NullPool: don't maintain a persistent pool.
    # Required when using Supabase's pgbouncer connection pooler.
    poolclass=NullPool,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)


async def get_db() -> AsyncSession:  # type: ignore[return]
    """FastAPI dependency — yields an async DB session per request."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
