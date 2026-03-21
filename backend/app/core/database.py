"""
C.O.V.E.R.T - Database Configuration

SQLAlchemy async database setup
"""

import asyncio
import logging
from sqlalchemy import text as sa_text, text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base

from app.core.config import settings

logger = logging.getLogger(__name__)

# Create async engine
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DB_ECHO,
    pool_size=20,
    max_overflow=40,
    pool_pre_ping=True,
)

# Create async session factory
async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# Base for models
Base = declarative_base()


async def get_db() -> AsyncSession:
    """
    Dependency for FastAPI endpoints to get database session

    Usage:
        @app.get("/items")
        async def get_items(db: AsyncSession = Depends(get_db)):
            ...
    """
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def ensure_schema():
    """
    Idempotent schema patch — adds any columns that were introduced after the
    initial migration but may not exist in the current DB (e.g. because
    `alembic upgrade head` could not run due to a missing dependency).

    Uses `ADD COLUMN IF NOT EXISTS` so it is safe to call on every startup.
    """
    patches = [
        # reports — columns added by migrations 007-009 and the DMS feature
        "ALTER TABLE IF EXISTS reports ADD COLUMN IF NOT EXISTS evidence_key TEXT",
        "ALTER TABLE IF EXISTS reports ADD COLUMN IF NOT EXISTS review_decision VARCHAR(20)",
        "ALTER TABLE IF EXISTS reports ADD COLUMN IF NOT EXISTS reviewer_address VARCHAR(42)",
        "ALTER TABLE IF EXISTS reports ADD COLUMN IF NOT EXISTS dms_enabled BOOLEAN DEFAULT FALSE",
        "ALTER TABLE IF EXISTS reports ADD COLUMN IF NOT EXISTS dms_trigger_date TIMESTAMPTZ",
        "ALTER TABLE IF EXISTS reports ADD COLUMN IF NOT EXISTS dms_released BOOLEAN DEFAULT FALSE",
        # user_reputation — base columns (table created by migration 004)
        "ALTER TABLE IF EXISTS user_reputation ADD COLUMN IF NOT EXISTS strikes INTEGER NOT NULL DEFAULT 0",
        "ALTER TABLE IF EXISTS user_reputation ADD COLUMN IF NOT EXISTS last_strike_at TIMESTAMPTZ",
        "ALTER TABLE IF EXISTS user_reputation ADD COLUMN IF NOT EXISTS last_slash_at TIMESTAMPTZ",
        "ALTER TABLE IF EXISTS user_reputation ADD COLUMN IF NOT EXISTS account_created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()",
        "ALTER TABLE IF EXISTS user_reputation ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()",
    ]
    async with engine.begin() as conn:
        for stmt in patches:
            try:
                await conn.execute(text(stmt))
            except Exception as exc:
                logger.warning("Schema patch skipped (%s): %s", stmt, exc)
    logger.info("[db] Schema patches applied.")


async def init_db():
    max_retries = 10
    for attempt in range(1, max_retries + 1):
        try:
            async with engine.begin() as conn:
                await conn.execute(sa_text("SELECT 1"))
            print(f"[DB] Connected successfully on attempt {attempt}")
            await ensure_schema()
            return
        except Exception as e:
            if attempt == max_retries:
                print(f"[DB] Failed to connect after {max_retries} attempts: {e}")
                raise
            wait = min(3 * attempt, 30)
            print(f"[DB] Attempt {attempt} failed: {e}. Retrying in {wait}s...")
            await asyncio.sleep(wait)


async def close_db():
    """
    Close database connections

    Run this on application shutdown
    """
    await engine.dispose()
