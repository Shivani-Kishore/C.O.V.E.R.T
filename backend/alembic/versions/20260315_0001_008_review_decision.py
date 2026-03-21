"""Add review_decision column to reports

Revision ID: 008
Revises: 007
Create Date: 2026-03-15

Stores the reviewer's decision string so moderators can see it from the
DB without hitting the blockchain, and so the finalize endpoint can use
it for reviewer penalty calculations.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = '008'
down_revision: Union[str, None] = '007'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('reports', sa.Column('review_decision', sa.String(20), nullable=True))


def downgrade() -> None:
    op.drop_column('reports', 'review_decision')
