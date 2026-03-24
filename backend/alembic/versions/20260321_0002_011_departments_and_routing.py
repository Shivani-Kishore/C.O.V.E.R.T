"""Add departments and report_routing tables

Revision ID: 011
Revises: 010
Create Date: 2026-03-21

Creates the departments table (seeded with 12 Bangalore departments) and
the report_routing table for tracking which department a report is forwarded to.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, ARRAY
import uuid

revision = '011'
down_revision = '010'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── departments ─────────────────────────────────────────────────────────
    op.create_table(
        'departments',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('short_name', sa.String(), nullable=True),
        sa.Column('jurisdiction_city', sa.String(), server_default='Bangalore'),
        sa.Column('categories', ARRAY(sa.String()), nullable=True),
        sa.Column('contact_email', sa.String(), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # ── report_routing ──────────────────────────────────────────────────────
    op.create_table(
        'report_routing',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('report_id', UUID(as_uuid=True), sa.ForeignKey('reports.id', ondelete='CASCADE'), nullable=False),
        sa.Column('department_id', UUID(as_uuid=True), sa.ForeignKey('departments.id', ondelete='CASCADE'), nullable=False),
        sa.Column('routed_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('notification_sent', sa.Boolean(), server_default='false'),
        sa.Column('notification_sent_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('status', sa.String(), server_default='PENDING'),
        sa.Column('department_response', sa.Text(), nullable=True),
        sa.Column('response_token', UUID(as_uuid=True), unique=True, default=uuid.uuid4),
        sa.Column('responded_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('followup_count', sa.Integer(), server_default='0'),
        sa.Column('last_followup_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index('idx_report_routing_report', 'report_routing', ['report_id'])
    op.create_index('idx_report_routing_dept', 'report_routing', ['department_id'])
    op.create_index('idx_report_routing_token', 'report_routing', ['response_token'], unique=True)

    # ── Seed 12 Bangalore departments ───────────────────────────────────────
    departments_table = sa.table(
        'departments',
        sa.column('id', UUID(as_uuid=True)),
        sa.column('name', sa.String()),
        sa.column('short_name', sa.String()),
        sa.column('jurisdiction_city', sa.String()),
        sa.column('categories', ARRAY(sa.String())),
        sa.column('contact_email', sa.String()),
        sa.column('is_active', sa.Boolean()),
    )

    op.bulk_insert(departments_table, [
        {
            'id': uuid.uuid4(),
            'name': 'BBMP Roads',
            'short_name': 'BBMP-ROADS',
            'jurisdiction_city': 'Bangalore',
            'categories': ['roads', 'footpaths', 'potholes', 'infrastructure'],
            'contact_email': None,
            'is_active': True,
        },
        {
            'id': uuid.uuid4(),
            'name': 'BBMP Solid Waste',
            'short_name': 'BBMP-SWM',
            'jurisdiction_city': 'Bangalore',
            'categories': ['garbage', 'waste', 'sanitation', 'dumping'],
            'contact_email': None,
            'is_active': True,
        },
        {
            'id': uuid.uuid4(),
            'name': 'BBMP Environment',
            'short_name': 'BBMP-ENV',
            'jurisdiction_city': 'Bangalore',
            'categories': ['parks', 'trees', 'encroachment', 'environment'],
            'contact_email': None,
            'is_active': True,
        },
        {
            'id': uuid.uuid4(),
            'name': 'BBMP Health',
            'short_name': 'BBMP-HEALTH',
            'jurisdiction_city': 'Bangalore',
            'categories': ['public_health', 'disease', 'hygiene', 'mosquito'],
            'contact_email': None,
            'is_active': True,
        },
        {
            'id': uuid.uuid4(),
            'name': 'BBMP Town Planning',
            'short_name': 'BBMP-TP',
            'jurisdiction_city': 'Bangalore',
            'categories': ['construction', 'building_violation', 'illegal_structure'],
            'contact_email': None,
            'is_active': True,
        },
        {
            'id': uuid.uuid4(),
            'name': 'BWSSB',
            'short_name': 'BWSSB',
            'jurisdiction_city': 'Bangalore',
            'categories': ['water', 'sewage', 'drainage', 'water_supply'],
            'contact_email': None,
            'is_active': True,
        },
        {
            'id': uuid.uuid4(),
            'name': 'BESCOM',
            'short_name': 'BESCOM',
            'jurisdiction_city': 'Bangalore',
            'categories': ['electricity', 'power_cut', 'streetlight', 'transformer'],
            'contact_email': None,
            'is_active': True,
        },
        {
            'id': uuid.uuid4(),
            'name': 'KSPCB',
            'short_name': 'KSPCB',
            'jurisdiction_city': 'Bangalore',
            'categories': ['pollution', 'air_quality', 'noise_pollution', 'industrial_waste'],
            'contact_email': None,
            'is_active': True,
        },
        {
            'id': uuid.uuid4(),
            'name': 'Lokayukta Karnataka',
            'short_name': 'LOKAYUKTA',
            'jurisdiction_city': 'Bangalore',
            'categories': ['corruption', 'bribery', 'misconduct', 'fraud'],
            'contact_email': None,
            'is_active': True,
        },
        {
            'id': uuid.uuid4(),
            'name': 'FSSAI Karnataka',
            'short_name': 'FSSAI-KA',
            'jurisdiction_city': 'Bangalore',
            'categories': ['food_safety', 'restaurant', 'adulteration'],
            'contact_email': None,
            'is_active': True,
        },
        {
            'id': uuid.uuid4(),
            'name': 'Bangalore Traffic Police',
            'short_name': 'BTP',
            'jurisdiction_city': 'Bangalore',
            'categories': ['traffic', 'signal', 'parking', 'accident'],
            'contact_email': None,
            'is_active': True,
        },
        {
            'id': uuid.uuid4(),
            'name': 'Bangalore City Police',
            'short_name': 'BCP',
            'jurisdiction_city': 'Bangalore',
            'categories': ['noise', 'law_order', 'harassment', 'theft'],
            'contact_email': None,
            'is_active': True,
        },
    ])


def downgrade() -> None:
    op.drop_table('report_routing')
    op.drop_table('departments')
