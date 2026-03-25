"""Add new report lifecycle status values to reportstatus enum

Revision ID: 012
Revises: 011
Create Date: 2026-03-25

Adds new status values to support the v2 report lifecycle:
  pending_review        – submitted, awaiting reviewer
  needs_evidence        – reviewer returned: needs more supporting evidence
  rejected_by_reviewer  – reviewer flagged as spam / reject
  pending_moderation    – reviewer passed; awaiting moderator finalization
  appealed              – reporter appealed the reviewer decision
"""
import sqlalchemy as sa
from alembic import op


revision = '012'
down_revision = '011'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # PostgreSQL requires ALTER TYPE ADD VALUE to run outside a transaction
    # (or at minimum as its own statement before any DML uses the new value).
    # Using autocommit_block ensures the enum values are committed and visible
    # immediately, even on PostgreSQL < 14 or with asyncpg drivers.
    conn = op.get_bind()
    conn.execute(sa.text("COMMIT"))  # end Alembic's open transaction
    conn.execute(sa.text("ALTER TYPE reportstatus ADD VALUE IF NOT EXISTS 'pending_review'"))
    conn.execute(sa.text("ALTER TYPE reportstatus ADD VALUE IF NOT EXISTS 'needs_evidence'"))
    conn.execute(sa.text("ALTER TYPE reportstatus ADD VALUE IF NOT EXISTS 'rejected_by_reviewer'"))
    conn.execute(sa.text("ALTER TYPE reportstatus ADD VALUE IF NOT EXISTS 'pending_moderation'"))
    conn.execute(sa.text("ALTER TYPE reportstatus ADD VALUE IF NOT EXISTS 'appealed'"))
    conn.execute(sa.text("BEGIN"))  # re-open transaction so Alembic can stamp the version


def downgrade() -> None:
    # PostgreSQL does not support removing values from an enum type.
    # A full downgrade would require recreating the type; left as no-op.
    pass
