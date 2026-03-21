"""Create dead man's switch tables

Revision ID: 008
Revises: 007
Create Date: 2026-03-15

Creates four tables that power the automated report-release system:
  dead_mans_switches  – DMS configuration & state per report
  dms_check_ins       – Reporter check-in history
  dms_release_logs    – Audit trail of every release attempt
  dms_watchdog        – Background service health monitoring
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '008a'
down_revision = '008'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── Enums (safe create — no-op if already exist) ───────────────────────
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE dmsstatus AS ENUM
                ('active','triggered','released','cancelled','extended','failed');
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE dmstriggertype AS ENUM
                ('time_based','activity_based','manual','emergency');
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """)

    # Reference types with create_type=False so SQLAlchemy won't try to create them again
    dms_status_enum = postgresql.ENUM(
        'active', 'triggered', 'released', 'cancelled', 'extended', 'failed',
        name='dmsstatus', create_type=False,
    )
    dms_trigger_type_enum = postgresql.ENUM(
        'time_based', 'activity_based', 'manual', 'emergency',
        name='dmstriggertype', create_type=False,
    )

    # ── dead_mans_switches ─────────────────────────────────────────────────
    op.create_table(
        'dead_mans_switches',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text('gen_random_uuid()')),
        sa.Column('report_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('reports.id', ondelete='CASCADE'),
                  nullable=False, unique=True),
        # Reporter identity
        sa.Column('reporter_nullifier', sa.String(66), nullable=False),
        sa.Column('reporter_commitment', sa.String(66), nullable=True),
        # Trigger config
        sa.Column('trigger_type', dms_trigger_type_enum, nullable=False,
                  server_default='time_based'),
        sa.Column('trigger_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('inactivity_days', sa.Integer(), nullable=True),
        # Status
        sa.Column('status', dms_status_enum, nullable=False, server_default='active'),
        sa.Column('last_check_in', sa.DateTime(timezone=True), nullable=True),
        sa.Column('check_in_count', sa.Integer(), nullable=False, server_default='0'),
        # Release config
        sa.Column('auto_release_public', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('auto_pin_ipfs', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('notify_contacts', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('encrypted_contacts', postgresql.JSONB(), nullable=True),
        sa.Column('contacts_encryption_key_hash', sa.String(66), nullable=True),
        # Release history
        sa.Column('trigger_reached_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('released_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('release_transaction_hash', sa.String(66), nullable=True),
        sa.Column('release_ipfs_cid', sa.String(100), nullable=True),
        # Failure tracking
        sa.Column('release_attempts', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('last_release_attempt', sa.DateTime(timezone=True), nullable=True),
        sa.Column('failure_reason', sa.Text(), nullable=True),
        # Emergency override
        sa.Column('emergency_override', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('override_reason', sa.Text(), nullable=True),
        sa.Column('override_by', sa.String(42), nullable=True),
        sa.Column('override_at', sa.DateTime(timezone=True), nullable=True),
        # Timestamps
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text('NOW()')),
        sa.Column('cancelled_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index('idx_dms_report_id', 'dead_mans_switches', ['report_id'])
    op.create_index('idx_dms_nullifier', 'dead_mans_switches', ['reporter_nullifier'])
    op.create_index('idx_dms_trigger_date', 'dead_mans_switches', ['trigger_date'])
    op.create_index('idx_dms_status', 'dead_mans_switches', ['status'])

    # ── dms_check_ins ──────────────────────────────────────────────────────
    op.create_table(
        'dms_check_ins',
        sa.Column('id', sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column('dms_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('dead_mans_switches.id', ondelete='CASCADE'),
                  nullable=False),
        sa.Column('check_in_timestamp', sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text('NOW()')),
        sa.Column('proof_of_life', sa.String(200), nullable=True),
        sa.Column('ip_address_hash', sa.String(64), nullable=True),
        sa.Column('user_agent_hash', sa.String(64), nullable=True),
        sa.Column('zkp_nullifier', sa.String(66), nullable=True),
        sa.Column('zkp_proof', postgresql.JSONB(), nullable=True),
        sa.Column('extended_trigger_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('extension_reason', sa.Text(), nullable=True),
    )
    op.create_index('idx_dms_check_ins_dms_id', 'dms_check_ins', ['dms_id'])
    op.create_index('idx_dms_check_ins_timestamp', 'dms_check_ins', ['check_in_timestamp'])

    # ── dms_release_logs ───────────────────────────────────────────────────
    op.create_table(
        'dms_release_logs',
        sa.Column('id', sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column('dms_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('dead_mans_switches.id', ondelete='CASCADE'),
                  nullable=False),
        sa.Column('attempt_number', sa.Integer(), nullable=False),
        sa.Column('attempt_timestamp', sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text('NOW()')),
        sa.Column('action_type', sa.String(50), nullable=False),
        sa.Column('action_success', sa.Boolean(), nullable=False),
        sa.Column('action_details', postgresql.JSONB(), nullable=True),
        # Blockchain
        sa.Column('transaction_hash', sa.String(66), nullable=True),
        sa.Column('block_number', sa.BigInteger(), nullable=True),
        sa.Column('gas_used', sa.BigInteger(), nullable=True),
        # IPFS
        sa.Column('ipfs_cid', sa.String(100), nullable=True),
        sa.Column('ipfs_gateway_url', sa.Text(), nullable=True),
        sa.Column('pin_status', sa.String(20), nullable=True),
        # Notifications
        sa.Column('notifications_sent', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('notification_status', postgresql.JSONB(), nullable=True),
        # Errors
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('error_code', sa.String(50), nullable=True),
        sa.Column('stack_trace', sa.Text(), nullable=True),
        # Retry
        sa.Column('retry_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('next_retry_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index('idx_dms_release_logs_dms_id', 'dms_release_logs', ['dms_id'])

    # ── dms_watchdog ───────────────────────────────────────────────────────
    op.create_table(
        'dms_watchdog',
        sa.Column('id', sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column('service_name', sa.String(100), nullable=False, server_default='dms_watchdog'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('last_heartbeat', sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text('NOW()')),
        sa.Column('total_checks', sa.BigInteger(), nullable=False, server_default='0'),
        sa.Column('triggers_found', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('releases_attempted', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('releases_succeeded', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('releases_failed', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('avg_check_duration_ms', sa.Integer(), nullable=True),
        sa.Column('last_check_duration_ms', sa.Integer(), nullable=True),
        sa.Column('queue_size', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('last_error', sa.Text(), nullable=True),
        sa.Column('last_error_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('consecutive_errors', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('check_interval_seconds', sa.Integer(), nullable=False, server_default='300'),
        sa.Column('batch_size', sa.Integer(), nullable=False, server_default='100'),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True,
                  server_default=sa.text('NOW()')),
        sa.Column('stopped_at', sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_table('dms_watchdog')
    op.drop_table('dms_release_logs')
    op.drop_table('dms_check_ins')
    op.drop_table('dead_mans_switches')

    op.execute("DROP TYPE IF EXISTS dmstriggertype")
    op.execute("DROP TYPE IF EXISTS dmsstatus")
