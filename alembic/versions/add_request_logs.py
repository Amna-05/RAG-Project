"""Add request logs table

Revision ID: add_request_logs_002
Revises: add_password_reset_001
Create Date: 2026-01-02

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'add_request_logs_002'
down_revision: Union[str, None] = 'add_password_reset_001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'request_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('request_id', sa.String(36), nullable=False),
        sa.Column('endpoint', sa.String(255), nullable=False),
        sa.Column('method', sa.String(10), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('status_code', sa.Integer(), nullable=False),
        sa.Column('duration_ms', sa.Float(), nullable=False),
        sa.Column('error_type', sa.String(50), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_request_log_request_id', 'request_logs', ['request_id'], unique=True)
    op.create_index('idx_request_log_user_id', 'request_logs', ['user_id'], unique=False)
    op.create_index('idx_request_log_created_at', 'request_logs', ['created_at'], unique=False)
    op.create_index('idx_request_log_status_code', 'request_logs', ['status_code'], unique=False)


def downgrade() -> None:
    op.drop_index('idx_request_log_status_code', table_name='request_logs')
    op.drop_index('idx_request_log_created_at', table_name='request_logs')
    op.drop_index('idx_request_log_user_id', table_name='request_logs')
    op.drop_index('idx_request_log_request_id', table_name='request_logs')
    op.drop_table('request_logs')
