"""Repair: ensure v2 lifecycle enum values exist in reportstatus

Revision ID: 014
Revises: 013
Create Date: 2026-03-25

Safety-net migration.  Migration 012 may have been marked as applied in
alembic_version on Railway while the enum changes were actually rolled back
(transaction wrapping issue with asyncpg).  This migration unconditionally
re-runs the same IF NOT EXISTS ALTER TYPE statements in autocommit_block so
the values are guaranteed to be present before new reports are created.
"""
import sqlalchemy as sa
from alembic import op


revision = '014'
down_revision = '013'
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.get_context().autocommit_block():
        op.execute(sa.text("ALTER TYPE reportstatus ADD VALUE IF NOT EXISTS 'pending_review'"))
        op.execute(sa.text("ALTER TYPE reportstatus ADD VALUE IF NOT EXISTS 'needs_evidence'"))
        op.execute(sa.text("ALTER TYPE reportstatus ADD VALUE IF NOT EXISTS 'rejected_by_reviewer'"))
        op.execute(sa.text("ALTER TYPE reportstatus ADD VALUE IF NOT EXISTS 'pending_moderation'"))
        op.execute(sa.text("ALTER TYPE reportstatus ADD VALUE IF NOT EXISTS 'appealed'"))


def downgrade() -> None:
    # PostgreSQL does not support removing enum values — no-op.
    pass
