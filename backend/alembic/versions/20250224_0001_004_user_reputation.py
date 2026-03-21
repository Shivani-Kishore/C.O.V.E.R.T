"""Add user_reputation table

Tracks reputation score, tier, strikes, and slash history for every wallet.
Replaces the per-moderator rep tracking with a universal table (spec §1-§6).

Revision ID: 004
Revises: 003
Create Date: 2025-02-24
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '004'
down_revision = '003'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'user_reputation',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False,
                  server_default=sa.text('gen_random_uuid()')),
        sa.Column('wallet_address', sa.String(42), nullable=False),
        sa.Column('reputation_score', sa.Integer(), nullable=False,
                  server_default='0'),
        sa.Column('tier', sa.String(20), nullable=False,
                  server_default='tier_0'),
        sa.Column('strikes', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('last_strike_at', sa.DateTime(), nullable=True),
        sa.Column('last_slash_at', sa.DateTime(), nullable=True),
        sa.Column('account_created_at', sa.DateTime(), nullable=False,
                  server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False,
                  server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('wallet_address', name='uq_user_reputation_wallet'),
        sa.CheckConstraint(
            "wallet_address ~ '^0x[a-fA-F0-9]{40}$'",
            name='urep_valid_address',
        ),
        sa.CheckConstraint(
            "tier IN ('tier_0','tier_1','tier_2','tier_3')",
            name='urep_valid_tier',
        ),
        sa.CheckConstraint(
            'reputation_score >= 0',
            name='urep_non_negative_score',
        ),
    )

    op.create_index('idx_urep_wallet',  'user_reputation', ['wallet_address'])
    op.create_index('idx_urep_score',   'user_reputation', ['reputation_score'])
    op.create_index('idx_urep_tier',    'user_reputation', ['tier'])


def downgrade() -> None:
    op.drop_table('user_reputation')
