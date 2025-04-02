"""
Initial schema migration

Revision ID: 001
Revises: 
Create Date: 2024-04-02 18:00:00.000000
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic
revision = '001'
down_revision = None
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Create user_activity table
    op.create_table(
        'user_activity',
        sa.Column('event_id', sa.String(36), primary_key=True),
        sa.Column('user_id', sa.String(50), nullable=False),
        sa.Column('session_id', sa.String(50), nullable=False),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.Column('event_type', sa.String(20), nullable=False),
        sa.Column('page_url', sa.Text(), nullable=False),
        sa.Column('referrer_url', sa.Text()),
        sa.Column('device_type', sa.String(20)),
        sa.Column('browser', sa.String(20)),
        sa.Column('os', sa.String(20)),
        sa.Column('screen_resolution', sa.String(20)),
        sa.Column('ip_address', sa.String(45)),
        sa.Column('country', sa.String(2)),
        sa.Column('city', sa.String(100)),
        sa.Column('latitude', sa.Numeric(10, 8)),
        sa.Column('longitude', sa.Numeric(11, 8)),
        sa.Column('product_id', sa.String(50)),
        sa.Column('product_category', sa.String(50)),
        sa.Column('product_price', sa.Numeric(10, 2)),
        sa.Column('quantity', sa.Integer()),
        sa.Column('custom_attributes', postgresql.JSONB()),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'))
    )

    # Create hourly_metrics table
    op.create_table(
        'hourly_metrics',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('hour_timestamp', sa.DateTime(), nullable=False),
        sa.Column('total_events', sa.Integer(), nullable=False),
        sa.Column('unique_users', sa.Integer(), nullable=False),
        sa.Column('purchase_count', sa.Integer(), nullable=False),
        sa.Column('revenue', sa.Numeric(10, 2), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.UniqueConstraint('hour_timestamp')
    )

    # Create dashboard_metadata table
    op.create_table(
        'dashboard_metadata',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('last_processed_timestamp', sa.DateTime(), nullable=False),
        sa.Column('total_records_processed', sa.BigInteger(), nullable=False),
        sa.Column('processing_duration_seconds', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(20), nullable=False),
        sa.Column('error_message', sa.Text()),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'))
    )

    # Create data_quality_checks table
    op.create_table(
        'data_quality_checks',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('check_name', sa.String(100), nullable=False),
        sa.Column('check_type', sa.String(50), nullable=False),
        sa.Column('status', sa.String(20), nullable=False),
        sa.Column('failure_count', sa.Integer(), nullable=False),
        sa.Column('total_records', sa.Integer(), nullable=False),
        sa.Column('check_timestamp', sa.DateTime(), nullable=False),
        sa.Column('details', postgresql.JSONB()),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'))
    )

    # Create anomaly_detection_results table
    op.create_table(
        'anomaly_detection_results',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('metric_name', sa.String(100), nullable=False),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.Column('value', sa.Numeric(10, 2), nullable=False),
        sa.Column('expected_value', sa.Numeric(10, 2), nullable=False),
        sa.Column('deviation_percentage', sa.Numeric(5, 2), nullable=False),
        sa.Column('severity', sa.String(20), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'))
    )

    # Create indexes
    op.create_index('idx_user_activity_timestamp', 'user_activity', ['timestamp'])
    op.create_index('idx_user_activity_user_id', 'user_activity', ['user_id'])
    op.create_index('idx_user_activity_event_type', 'user_activity', ['event_type'])
    op.create_index('idx_hourly_metrics_timestamp', 'hourly_metrics', ['hour_timestamp'])

def downgrade() -> None:
    # Drop indexes
    op.drop_index('idx_user_activity_timestamp')
    op.drop_index('idx_user_activity_user_id')
    op.drop_index('idx_user_activity_event_type')
    op.drop_index('idx_hourly_metrics_timestamp')

    # Drop tables
    op.drop_table('anomaly_detection_results')
    op.drop_table('data_quality_checks')
    op.drop_table('dashboard_metadata')
    op.drop_table('hourly_metrics')
    op.drop_table('user_activity') 