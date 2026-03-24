"""Add scheduled_for and chain_submitted to reports

Revision ID: 010
Revises: 009
Create Date: 2026-03-21

Enables delayed (scheduled) report submissions for reporter safety.
"""
from alembic import op
import sqlalchemy as sa

revision = '010'
down_revision = '009'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('reports', sa.Column('scheduled_for', sa.DateTime(timezone=True), nullable=True))
    op.add_column('reports', sa.Column('chain_submitted', sa.Boolean(), nullable=False, server_default='true'))
    op.create_index('idx_reports_scheduled', 'reports', ['scheduled_for'],
                    postgresql_where=sa.text("chain_submitted = false"))


def downgrade() -> None:
    op.drop_index('idx_reports_scheduled', table_name='reports')
    op.drop_column('reports', 'chain_submitted')
    op.drop_column('reports', 'scheduled_for')
