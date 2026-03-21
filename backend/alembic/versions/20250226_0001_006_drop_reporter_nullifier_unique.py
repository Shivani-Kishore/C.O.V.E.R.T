"""Drop unique constraint on reporter_nullifier

Revision ID: 006
Revises: 005
Create Date: 2026-02-26

A wallet (reporter) must be able to submit multiple reports.
The unique constraint on reporter_nullifier was incorrectly limiting
each wallet to a single report submission.
"""
from typing import Sequence, Union

from alembic import op

revision: str = '006'
down_revision: Union[str, None] = '005'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Drop the erroneous unique constraint — reporter_nullifier (wallet address)
    # is not unique; one wallet can submit many reports.
    # The regular index idx_reports_nullifier is kept for query performance.
    op.drop_constraint('uq_reports_reporter_nullifier', 'reports', type_='unique')


def downgrade() -> None:
    op.create_unique_constraint(
        'uq_reports_reporter_nullifier', 'reports', ['reporter_nullifier']
    )
