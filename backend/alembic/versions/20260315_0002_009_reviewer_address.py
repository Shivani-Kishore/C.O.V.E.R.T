"""Add reviewer_address to reports

Revision ID: 009
Revises: 008
Create Date: 2026-03-15

Stores the wallet address of the reviewer who assessed the report,
enabling reviewer penalty logic when moderator decision contradicts.
"""
from alembic import op
import sqlalchemy as sa

revision = '009'
down_revision = '008a'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('reports', sa.Column('reviewer_address', sa.String(42), nullable=True))


def downgrade() -> None:
    op.drop_column('reports', 'reviewer_address')
