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
from alembic import op


revision = '012'
down_revision = '011'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # PostgreSQL 12+ supports ALTER TYPE ADD VALUE inside a transaction.
    # IF NOT EXISTS guards against re-running on a DB that already has the value.
    op.execute("ALTER TYPE reportstatus ADD VALUE IF NOT EXISTS 'pending_review'")
    op.execute("ALTER TYPE reportstatus ADD VALUE IF NOT EXISTS 'needs_evidence'")
    op.execute("ALTER TYPE reportstatus ADD VALUE IF NOT EXISTS 'rejected_by_reviewer'")
    op.execute("ALTER TYPE reportstatus ADD VALUE IF NOT EXISTS 'pending_moderation'")
    op.execute("ALTER TYPE reportstatus ADD VALUE IF NOT EXISTS 'appealed'")


def downgrade() -> None:
    # PostgreSQL does not support removing values from an enum type.
    # A full downgrade would require recreating the type; left as no-op.
    pass
