"""Add bm25_indexed column to documents

Revision ID: add_bm25_indexed_004
Revises: add_system_metrics_003
Create Date: 2026-01-02

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'add_bm25_indexed_004'
down_revision: Union[str, None] = 'add_system_metrics_003'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'documents',
        sa.Column('bm25_indexed', sa.Boolean(), nullable=False, server_default='false')
    )


def downgrade() -> None:
    op.drop_column('documents', 'bm25_indexed')
