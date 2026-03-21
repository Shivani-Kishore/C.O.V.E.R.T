"""Initial reports schema

Revision ID: 001
Revises:
Create Date: 2024-11-19

C.O.V.E.R.T Database Schema - Week 2 Implementation
Creates the core tables for encrypted report storage and moderation
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ===== Reports Table =====
    op.create_table(
        'reports',
        # Primary Key
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()')),

        # Blockchain Integration
        sa.Column('commitment_hash', sa.String(66), nullable=False),
        sa.Column('transaction_hash', sa.String(66), nullable=True),
        sa.Column('block_number', sa.BigInteger(), nullable=True),
        sa.Column('chain_id', sa.Integer(), nullable=False),

        # IPFS Storage
        sa.Column('ipfs_cid', sa.String(100), nullable=False),
        sa.Column('ipfs_gateway_url', sa.Text(), nullable=True),

        # Encrypted Metadata
        sa.Column('encrypted_category', sa.String(500), nullable=True),
        sa.Column('encrypted_title', sa.String(1000), nullable=True),
        sa.Column('encrypted_summary', sa.Text(), nullable=True),
        sa.Column('encrypted_file_hash', sa.String(100), nullable=True),

        # Report Metadata
        sa.Column('file_size', sa.BigInteger(), nullable=False),
        sa.Column('file_type', sa.String(50), nullable=True),
        sa.Column('submission_timestamp', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),

        # Privacy Settings
        sa.Column('visibility', sa.Enum('private', 'moderated', 'public', name='reportvisibility'), nullable=False, server_default='moderated'),
        sa.Column('anonymous', sa.Boolean(), nullable=False, server_default=sa.text('true')),

        # Status Tracking
        sa.Column('status', sa.Enum('pending', 'under_review', 'verified', 'rejected', 'disputed', 'archived', name='reportstatus'), nullable=False, server_default='pending'),
        sa.Column('verification_score', sa.Numeric(3, 2), nullable=True),
        sa.Column('risk_level', sa.Enum('low', 'medium', 'high', 'critical', name='risklevel'), nullable=True),

        # Reporter Identity (Anonymous)
        sa.Column('reporter_nullifier', sa.String(66), nullable=True),
        sa.Column('reporter_commitment', sa.String(66), nullable=True),
        sa.Column('burner_address', sa.String(42), nullable=True),

        # Temporal Protection
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('last_accessed_at', sa.DateTime(timezone=True), nullable=True),

        # Dead Man's Switch
        sa.Column('dms_enabled', sa.Boolean(), nullable=True, server_default=sa.text('false')),
        sa.Column('dms_trigger_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('dms_released', sa.Boolean(), nullable=True, server_default=sa.text('false')),

        # Soft Delete
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deletion_reason', sa.Text(), nullable=True),

        # Primary Key
        sa.PrimaryKeyConstraint('id'),

        # Unique Constraints
        sa.UniqueConstraint('commitment_hash', name='uq_reports_commitment_hash'),
        sa.UniqueConstraint('ipfs_cid', name='uq_reports_ipfs_cid'),
        sa.UniqueConstraint('reporter_nullifier', name='uq_reports_reporter_nullifier'),

        # Check Constraints
        sa.CheckConstraint('verification_score >= 0.00 AND verification_score <= 1.00', name='valid_score'),
        sa.CheckConstraint("commitment_hash ~ '^0x[a-fA-F0-9]{64}$'", name='commitment_format'),
        sa.CheckConstraint('chain_id IN (137, 42161, 80001, 421613, 31337)', name='valid_chain'),
    )

    # Reports Indexes
    op.create_index('idx_reports_commitment', 'reports', ['commitment_hash'])
    op.create_index('idx_reports_ipfs', 'reports', ['ipfs_cid'])
    op.create_index('idx_reports_status', 'reports', ['status'])
    op.create_index('idx_reports_timestamp', 'reports', ['submission_timestamp'])
    op.create_index('idx_reports_chain', 'reports', ['chain_id', 'block_number'])
    op.create_index('idx_reports_nullifier', 'reports', ['reporter_nullifier'])
    op.create_index('idx_reports_tx', 'reports', ['transaction_hash'])

    # Partial indexes
    op.execute('''
        CREATE INDEX idx_reports_status_active ON reports(status)
        WHERE deleted_at IS NULL
    ''')
    op.execute('''
        CREATE INDEX idx_reports_dms ON reports(dms_trigger_date)
        WHERE dms_enabled = TRUE AND dms_released = FALSE
    ''')

    # ===== Report Logs Table =====
    op.create_table(
        'report_logs',
        # Primary Key
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),

        # Foreign Keys
        sa.Column('report_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('actor_id', postgresql.UUID(as_uuid=True), nullable=True),

        # Event Details
        sa.Column('event_type', sa.Enum('created', 'status_changed', 'accessed', 'modified', 'deleted', 'moderation_started', 'moderation_completed', 'disputed', 'released', 'dms_triggered', name='logeventtype'), nullable=False),
        sa.Column('event_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True),

        # Change Tracking
        sa.Column('old_value', sa.Text(), nullable=True),
        sa.Column('new_value', sa.Text(), nullable=True),
        sa.Column('field_changed', sa.String(100), nullable=True),

        # Context
        sa.Column('ip_address_hash', sa.String(64), nullable=True),
        sa.Column('user_agent_hash', sa.String(64), nullable=True),

        # Timestamp
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),

        # Primary Key
        sa.PrimaryKeyConstraint('id'),

        # Foreign Key
        sa.ForeignKeyConstraint(['report_id'], ['reports.id'], ondelete='CASCADE'),
    )

    # Report Logs Indexes
    op.create_index('idx_report_logs_report', 'report_logs', ['report_id', 'created_at'])
    op.create_index('idx_report_logs_event', 'report_logs', ['event_type'])
    op.create_index('idx_report_logs_timestamp', 'report_logs', ['created_at'])

    # ===== Anchors Table =====
    op.create_table(
        'anchors',
        # Primary Key
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),

        # Blockchain Data
        sa.Column('merkle_root', sa.String(66), nullable=False),
        sa.Column('transaction_hash', sa.String(66), nullable=False),
        sa.Column('block_number', sa.BigInteger(), nullable=False),
        sa.Column('chain_id', sa.Integer(), nullable=False),

        # Anchor Metadata
        sa.Column('anchor_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('report_count', sa.Integer(), nullable=False, server_default='0'),

        # Merkle Tree Data
        sa.Column('merkle_tree', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('leaf_hashes', postgresql.ARRAY(sa.Text()), nullable=True),

        # Timestamps
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('anchored_at', sa.DateTime(timezone=True), nullable=True),

        # Primary Key
        sa.PrimaryKeyConstraint('id'),

        # Unique Constraints
        sa.UniqueConstraint('merkle_root', name='uq_anchors_merkle_root'),
        sa.UniqueConstraint('anchor_date', name='uq_anchors_anchor_date'),
    )

    # Anchors Indexes
    op.create_index('idx_anchors_date', 'anchors', ['anchor_date'])
    op.create_index('idx_anchors_block', 'anchors', ['chain_id', 'block_number'])
    op.create_index('idx_anchors_root', 'anchors', ['merkle_root'])

    # ===== ZKP Nullifiers Table =====
    op.create_table(
        'zkp_nullifiers',
        # Primary Key
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),

        # ZKP Data
        sa.Column('nullifier', sa.String(66), nullable=False),
        sa.Column('commitment', sa.String(66), nullable=False),

        # Usage Tracking
        sa.Column('first_used_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('last_used_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('usage_count', sa.Integer(), nullable=False, server_default='1'),

        # Rate Limiting
        sa.Column('daily_report_count', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('last_daily_reset', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_DATE')),

        # Associated Report
        sa.Column('report_id', postgresql.UUID(as_uuid=True), nullable=True),

        # Primary Key
        sa.PrimaryKeyConstraint('id'),

        # Unique Constraint
        sa.UniqueConstraint('nullifier', name='uq_zkp_nullifiers_nullifier'),

        # Foreign Key
        sa.ForeignKeyConstraint(['report_id'], ['reports.id'], ondelete='SET NULL'),

        # Check Constraints
        sa.CheckConstraint("nullifier ~ '^0x[a-fA-F0-9]{64}$'", name='valid_nullifier'),
        sa.CheckConstraint("commitment ~ '^0x[a-fA-F0-9]{64}$'", name='valid_commitment'),
    )

    # ZKP Nullifiers Indexes
    op.create_index('idx_zkp_nullifiers_nullifier', 'zkp_nullifiers', ['nullifier'])
    op.create_index('idx_zkp_nullifiers_commitment', 'zkp_nullifiers', ['commitment'])
    op.create_index('idx_zkp_nullifiers_daily', 'zkp_nullifiers', ['last_daily_reset', 'daily_report_count'])

    # ===== Helper Functions =====

    # Update timestamp trigger function
    op.execute('''
        CREATE OR REPLACE FUNCTION update_timestamp()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = NOW();
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    ''')

    # Apply trigger to reports table
    op.execute('''
        CREATE TRIGGER update_reports_timestamp
        BEFORE UPDATE ON reports
        FOR EACH ROW
        EXECUTE FUNCTION update_timestamp();
    ''')


def downgrade() -> None:
    # Drop triggers
    op.execute('DROP TRIGGER IF EXISTS update_reports_timestamp ON reports')
    op.execute('DROP FUNCTION IF EXISTS update_timestamp()')

    # Drop tables in reverse order
    op.drop_table('zkp_nullifiers')
    op.drop_table('anchors')
    op.drop_table('report_logs')
    op.drop_table('reports')

    # Drop enums
    op.execute('DROP TYPE IF EXISTS logeventtype')
    op.execute('DROP TYPE IF EXISTS risklevel')
    op.execute('DROP TYPE IF EXISTS reportstatus')
    op.execute('DROP TYPE IF EXISTS reportvisibility')
