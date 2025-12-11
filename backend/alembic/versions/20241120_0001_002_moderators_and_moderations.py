"""Create moderators and moderations tables

Revision ID: 002
Revises: 001
Create Date: 2024-11-20 00:01:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create moderators table
    op.create_table(
        'moderators',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('wallet_address', sa.String(42), nullable=False, unique=True),
        sa.Column('reputation_token_id', sa.BigInteger, nullable=True),
        sa.Column('reputation_score', sa.Integer, nullable=False, server_default='0'),
        sa.Column('tier', sa.String(20), nullable=False, server_default='bronze'),
        sa.Column('total_reviews', sa.Integer, nullable=False, server_default='0'),
        sa.Column('accurate_reviews', sa.Integer, nullable=False, server_default='0'),
        sa.Column('disputed_reviews', sa.Integer, nullable=False, server_default='0'),
        sa.Column('last_active_at', sa.DateTime, nullable=True),
        sa.Column('is_active', sa.Boolean, server_default='true'),
        sa.Column('suspension_until', sa.DateTime, nullable=True),
        sa.Column('suspension_reason', sa.Text, nullable=True),
        sa.Column('expertise_areas', postgresql.JSONB, nullable=True),
        sa.Column('preferred_categories', postgresql.ARRAY(sa.Text), nullable=True),
        sa.Column('average_review_time_seconds', sa.Integer, nullable=True),
        sa.Column('consistency_score', sa.Numeric(3, 2), nullable=True),
        sa.Column('public_key', sa.Text, nullable=True),
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("tier IN ('bronze', 'silver', 'gold', 'platinum')", name='valid_tier'),
        sa.CheckConstraint("wallet_address ~ '^0x[a-fA-F0-9]{40}$'", name='valid_address'),
        sa.CheckConstraint('consistency_score >= 0.00 AND consistency_score <= 1.00', name='valid_consistency')
    )

    # Create indexes for moderators
    op.create_index('idx_moderators_wallet', 'moderators', ['wallet_address'])
    op.create_index('idx_moderators_reputation', 'moderators', ['reputation_score'], postgresql_ops={'reputation_score': 'DESC'})
    op.create_index('idx_moderators_tier', 'moderators', ['tier'])
    op.create_index('idx_moderators_active', 'moderators', ['is_active', 'last_active_at'])

    # Create moderations table
    op.create_table(
        'moderations',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('report_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('moderator_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('action', sa.String(50), nullable=False),
        sa.Column('decision', sa.String(20), nullable=True),
        sa.Column('encrypted_notes', sa.Text, nullable=True),
        sa.Column('notes_encryption_key_hash', sa.String(66), nullable=True),
        sa.Column('ai_recommendation', sa.String(20), nullable=True),
        sa.Column('ai_confidence', sa.Numeric(3, 2), nullable=True),
        sa.Column('ai_flags', postgresql.JSONB, nullable=True),
        sa.Column('rejection_reason', sa.Text, nullable=True),
        sa.Column('verification_evidence', sa.Text, nullable=True),
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column('completed_at', sa.DateTime, nullable=True),
        sa.Column('time_spent_seconds', sa.Integer, nullable=True),
        sa.ForeignKeyConstraint(['report_id'], ['reports.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['moderator_id'], ['moderators.id'], ondelete='SET NULL'),
        sa.CheckConstraint("action IN ('review_started', 'request_info', 'verified', 'rejected', 'escalated')", name='valid_action'),
        sa.CheckConstraint("decision IN ('accept', 'reject', 'need_info', 'escalate') OR decision IS NULL", name='valid_decision'),
        sa.CheckConstraint('ai_confidence >= 0.00 AND ai_confidence <= 1.00', name='valid_ai_confidence')
    )

    # Create indexes for moderations
    op.create_index('idx_moderations_report', 'moderations', ['report_id'])
    op.create_index('idx_moderations_moderator', 'moderations', ['moderator_id'])
    op.create_index('idx_moderations_action', 'moderations', ['action'])
    op.create_index('idx_moderations_created', 'moderations', ['created_at'], postgresql_ops={'created_at': 'DESC'})
    op.create_index('idx_moderations_pending', 'moderations', ['completed_at'], postgresql_where='completed_at IS NULL')

    # Create trigger for updated_at on moderators
    op.execute("""
        CREATE OR REPLACE FUNCTION update_moderators_timestamp()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = NOW();
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)

    op.execute("""
        CREATE TRIGGER trigger_update_moderators_timestamp
        BEFORE UPDATE ON moderators
        FOR EACH ROW
        EXECUTE FUNCTION update_moderators_timestamp();
    """)


def downgrade() -> None:
    op.drop_table('moderations')
    op.drop_table('moderators')
    op.execute('DROP FUNCTION IF EXISTS update_moderators_timestamp CASCADE')
