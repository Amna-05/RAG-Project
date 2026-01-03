"""Add system metrics table

Revision ID: add_system_metrics_003
Revises: add_request_logs_002
Create Date: 2026-01-02

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'add_system_metrics_003'
down_revision: Union[str, None] = 'add_request_logs_002'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Note: metrictype enum already exists in the database
    # Skip enum creation as it will be handled by the table creation below

    op.create_table(
        'system_metrics',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('metric_name', sa.String(100), nullable=False),
        sa.Column('metric_type', sa.Enum('counter', 'gauge', 'histogram', name='metrictype', create_type=False), nullable=False),
        sa.Column('value', sa.Float(), nullable=False),
        sa.Column('labels', postgresql.JSONB(), nullable=True),
        sa.Column('recorded_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_metric_name_recorded', 'system_metrics', ['metric_name', 'recorded_at'], unique=False)


def downgrade() -> None:
    op.drop_index('idx_metric_name_recorded', table_name='system_metrics')
    op.drop_table('system_metrics')
    # Drop enum type
    op.execute('DROP TYPE IF EXISTS metrictype')
