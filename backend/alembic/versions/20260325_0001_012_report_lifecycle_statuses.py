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
    # ALTER TYPE ADD VALUE must run outside a transaction (or the new values
    # won't be visible on PostgreSQL < 14).  autocommit_block() temporarily
    # commits, switches to AUTOCOMMIT, runs the DDL, then restores the
    # previous transaction state so Alembic can stamp alembic_version.
    with op.get_context().autocommit_block():
        op.execute(sa.text("ALTER TYPE reportstatus ADD VALUE IF NOT EXISTS 'pending_review'"))
        op.execute(sa.text("ALTER TYPE reportstatus ADD VALUE IF NOT EXISTS 'needs_evidence'"))
        op.execute(sa.text("ALTER TYPE reportstatus ADD VALUE IF NOT EXISTS 'rejected_by_reviewer'"))
        op.execute(sa.text("ALTER TYPE reportstatus ADD VALUE IF NOT EXISTS 'pending_moderation'"))
        op.execute(sa.text("ALTER TYPE reportstatus ADD VALUE IF NOT EXISTS 'appealed'"))


def downgrade() -> None:
    # PostgreSQL does not support removing values from an enum type.
    # A full downgrade would require recreating the type; left as no-op.
    pass
