"""Add evidence_key column to reports

Revision ID: 007
Revises: 006
Create Date: 2026-03-02

Adds an optional AES-256 key (stored as 64-char hex) to each report.
Populated for PUBLIC and MODERATED reports so reviewers and moderators
can fetch and decrypt the IPFS evidence bundle in-browser.
PRIVATE reports leave this NULL (key stays in reporter's localStorage only).
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = '007'
down_revision: Union[str, None] = '006'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('reports', sa.Column('evidence_key', sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column('reports', 'evidence_key')
