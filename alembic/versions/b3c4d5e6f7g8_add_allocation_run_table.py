"""add allocation run table

Revision ID: b3c4d5e6f7g8
Revises: a2b3c4d5e6f7
Create Date: 2026-01-13 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'b3c4d5e6f7g8'
down_revision: Union[str, None] = 'a2b3c4d5e6f7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'allocation_runs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('run_date', sa.Date(), nullable=False, unique=True),
        sa.Column('executed_at', sa.DateTime(), nullable=False),
        sa.Column('total_requests', sa.Integer(), default=0),
        sa.Column('groups_allocated', sa.Integer(), default=0),
        sa.Column('high_priority_allocated', sa.Integer(), default=0),
        sa.Column('medium_priority_allocated', sa.Integer(), default=0),
        sa.Column('low_priority_allocated', sa.Integer(), default=0),
        sa.Column('failed_allocations', sa.Integer(), default=0),
        sa.Column('status', sa.String(), default='RUNNING'),
        sa.Column('error_message', sa.String(), nullable=True),
    )


def downgrade() -> None:
    op.drop_table('allocation_runs')
