"""Add final_label column to reports table

Revision ID: 013
Revises: 012
Create Date: 2026-03-25

Stores the moderator's final decision label on the report:
  CORROBORATED | NEEDS_EVIDENCE | DISPUTED | FALSE_OR_MANIPULATED
"""
from alembic import op
import sqlalchemy as sa


revision = '013'
down_revision = '012'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('reports', sa.Column('final_label', sa.String(30), nullable=True))


def downgrade() -> None:
    op.drop_column('reports', 'final_label')
