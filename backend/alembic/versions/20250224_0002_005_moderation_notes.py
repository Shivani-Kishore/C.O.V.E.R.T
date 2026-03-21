"""moderation_notes table

Revision ID: 005
Revises: 004
Create Date: 2025-02-24
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '005'
down_revision = '004'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'moderation_notes',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('report_id', sa.Integer(), nullable=False),
        sa.Column('moderator_address', sa.String(42), nullable=False),
        sa.Column('content', sa.Text(), nullable=False, server_default=''),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('report_id', 'moderator_address', name='uq_note_report_moderator'),
    )
    op.create_index('ix_moderation_notes_report_id', 'moderation_notes', ['report_id'])


def downgrade() -> None:
    op.drop_index('ix_moderation_notes_report_id', table_name='moderation_notes')
    op.drop_table('moderation_notes')
