"""Drop reputation_token_id column from moderators

The ReputationSBT contract has been replaced by COVCredits, CovertBadges,
and CovertProtocol. The reputation_token_id column is no longer used; reputation
is tracked via database fields (reputation_score, tier) and on-chain via
the CovertBadges contract.

Revision ID: 003
Revises: 002
Create Date: 2025-02-21 00:01:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_column('moderators', 'reputation_token_id')


def downgrade() -> None:
    op.add_column(
        'moderators',
        sa.Column('reputation_token_id', sa.BigInteger, nullable=True)
    )
