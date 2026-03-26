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
            try:
                await session.rollback()
            except Exception as rb_exc:
                logger.warning("[db] rollback error (ignored): %s", rb_exc)
            raise
        finally:
            try:
                await session.close()
            except Exception as cl_exc:
                logger.warning("[db] session close error (ignored): %s", cl_exc)


async def ensure_tables():
    """
    Idempotent table creation — creates any tables that may be missing on the
    current DB (e.g. because a migration ran but DDL wasn't actually applied).
    Uses CREATE TABLE IF NOT EXISTS so it is safe to call on every startup.
    """
    stmts = [
        # ── migration 004: user_reputation ──────────────────────────────────
        """CREATE TABLE IF NOT EXISTS user_reputation (
            id UUID NOT NULL DEFAULT gen_random_uuid(),
            wallet_address VARCHAR(42) NOT NULL,
            reputation_score INTEGER NOT NULL DEFAULT 0,
            tier VARCHAR(20) NOT NULL DEFAULT 'tier_0',
            strikes INTEGER NOT NULL DEFAULT 0,
            last_strike_at TIMESTAMP,
            last_slash_at TIMESTAMP,
            account_created_at TIMESTAMP NOT NULL DEFAULT now(),
            updated_at TIMESTAMP NOT NULL DEFAULT now(),
            PRIMARY KEY (id),
            CONSTRAINT uq_user_reputation_wallet UNIQUE (wallet_address),
            CONSTRAINT urep_valid_address CHECK (wallet_address ~ '^0x[a-fA-F0-9]{40}$'),
            CONSTRAINT urep_valid_tier CHECK (tier IN ('tier_0','tier_1','tier_2','tier_3')),
            CONSTRAINT urep_non_negative_score CHECK (reputation_score >= 0)
        )""",
        "CREATE INDEX IF NOT EXISTS idx_urep_wallet ON user_reputation (wallet_address)",
        "CREATE INDEX IF NOT EXISTS idx_urep_score ON user_reputation (reputation_score)",
        "CREATE INDEX IF NOT EXISTS idx_urep_tier ON user_reputation (tier)",
        # ── migration 005: moderation_notes ─────────────────────────────────
        """CREATE TABLE IF NOT EXISTS moderation_notes (
            id UUID NOT NULL DEFAULT gen_random_uuid(),
            report_id INTEGER NOT NULL,
            moderator_address VARCHAR(42) NOT NULL,
            content TEXT NOT NULL DEFAULT '',
            created_at TIMESTAMP NOT NULL DEFAULT now(),
            updated_at TIMESTAMP NOT NULL DEFAULT now(),
            PRIMARY KEY (id),
            CONSTRAINT uq_note_report_moderator UNIQUE (report_id, moderator_address)
        )""",
        "CREATE INDEX IF NOT EXISTS ix_moderation_notes_report_id ON moderation_notes (report_id)",
        # ── migration 011: departments ───────────────────────────────────────
        """CREATE TABLE IF NOT EXISTS departments (
            id UUID NOT NULL DEFAULT gen_random_uuid(),
            name VARCHAR NOT NULL,
            short_name VARCHAR,
            jurisdiction_city VARCHAR DEFAULT 'Bangalore',
            categories TEXT[],
            contact_email VARCHAR,
            is_active BOOLEAN DEFAULT true,
            created_at TIMESTAMPTZ DEFAULT now(),
            PRIMARY KEY (id)
        )""",
        # ── migration 011: report_routing ────────────────────────────────────
        """CREATE TABLE IF NOT EXISTS report_routing (
            id UUID NOT NULL DEFAULT gen_random_uuid(),
            report_id UUID NOT NULL REFERENCES reports(id) ON DELETE CASCADE,
            department_id UUID NOT NULL REFERENCES departments(id) ON DELETE CASCADE,
            routed_at TIMESTAMPTZ DEFAULT now(),
            notification_sent BOOLEAN DEFAULT false,
            notification_sent_at TIMESTAMPTZ,
            status VARCHAR DEFAULT 'PENDING',
            department_response TEXT,
            response_token UUID DEFAULT gen_random_uuid() UNIQUE,
            responded_at TIMESTAMPTZ,
            followup_count INTEGER DEFAULT 0,
            last_followup_at TIMESTAMPTZ,
            PRIMARY KEY (id)
        )""",
        "CREATE INDEX IF NOT EXISTS idx_report_routing_report ON report_routing (report_id)",
        "CREATE INDEX IF NOT EXISTS idx_report_routing_dept ON report_routing (department_id)",
        "CREATE UNIQUE INDEX IF NOT EXISTS idx_report_routing_token ON report_routing (response_token)",
    ]
    async with engine.begin() as conn:
        for stmt in stmts:
            try:
                await conn.execute(text(stmt))
            except Exception as exc:
                logger.warning("[db] Table/index creation skipped: %s", exc)
    logger.info("[db] Table safety-net applied.")


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
        # reports — columns added by migration 010 (routing)
        "ALTER TABLE IF EXISTS reports ADD COLUMN IF NOT EXISTS scheduled_for TIMESTAMPTZ",
        "ALTER TABLE IF EXISTS reports ADD COLUMN IF NOT EXISTS chain_submitted BOOLEAN NOT NULL DEFAULT TRUE",
        # reports — column added by migration 013 (final label)
        "ALTER TABLE IF EXISTS reports ADD COLUMN IF NOT EXISTS final_label VARCHAR(30)",
        # user_reputation — extra columns (table created above by ensure_tables)
        "ALTER TABLE IF EXISTS user_reputation ADD COLUMN IF NOT EXISTS strikes INTEGER NOT NULL DEFAULT 0",
        "ALTER TABLE IF EXISTS user_reputation ADD COLUMN IF NOT EXISTS last_strike_at TIMESTAMPTZ",
        "ALTER TABLE IF EXISTS user_reputation ADD COLUMN IF NOT EXISTS last_slash_at TIMESTAMPTZ",
        "ALTER TABLE IF EXISTS user_reputation ADD COLUMN IF NOT EXISTS account_created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()",
        "ALTER TABLE IF EXISTS user_reputation ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()",
        # constraint patches — drop stale constraints then re-add with correct values
        "ALTER TABLE IF EXISTS reports DROP CONSTRAINT IF EXISTS uq_reports_reporter_nullifier",
        "ALTER TABLE IF EXISTS reports DROP CONSTRAINT IF EXISTS valid_chain",
        "ALTER TABLE IF EXISTS reports ADD CONSTRAINT valid_chain CHECK (chain_id IN (137, 42161, 80001, 421613, 31337, 84532))",
    ]
    async with engine.begin() as conn:
        for stmt in patches:
            try:
                await conn.execute(text(stmt))
            except Exception as exc:
                logger.warning("Schema patch skipped (%s): %s", stmt, exc)
    logger.info("[db] Schema patches applied.")


async def ensure_enum_values():
    """
    Idempotent enum patch — adds v2 lifecycle status values to the
    `reportstatus` enum type.  Must run with AUTOCOMMIT since PostgreSQL
    does not allow ALTER TYPE inside a transaction.
    """
    new_values = [
        "pending_review",
        "needs_evidence",
        "rejected_by_reviewer",
        "pending_moderation",
        "appealed",
    ]
    try:
        autocommit_engine = engine.execution_options(isolation_level="AUTOCOMMIT")
        async with autocommit_engine.connect() as conn:
            for value in new_values:
                try:
                    await conn.execute(
                        text(f"ALTER TYPE reportstatus ADD VALUE IF NOT EXISTS '{value}'")
                    )
                except Exception as exc:
                    logger.warning("[db] Enum patch skipped ('%s'): %s", value, exc)
        logger.info("[db] Enum values ensured.")
    except Exception as exc:
        logger.warning("[db] Enum patching skipped entirely: %s", exc)


async def init_db():
    max_retries = 10
    for attempt in range(1, max_retries + 1):
        try:
            async with engine.begin() as conn:
                await conn.execute(sa_text("SELECT 1"))
            print(f"[DB] Connected successfully on attempt {attempt}")
            await ensure_tables()
            await ensure_schema()
            await ensure_enum_values()
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
