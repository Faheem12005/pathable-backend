"""add user location and daily requests

Revision ID: a2b3c4d5e6f7
Revises: 1ef8fcb5fe63
Create Date: 2026-01-13 10:45:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'a2b3c4d5e6f7'
down_revision: Union[str, None] = '1ef8fcb5fe63'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add new columns to users table
    op.add_column('users', sa.Column('home_lat', sa.Float(), nullable=True))
    op.add_column('users', sa.Column('home_lng', sa.Float(), nullable=True))
    op.add_column('users', sa.Column('default_days', postgresql.ARRAY(sa.String()), nullable=True, server_default='{}'))

    # Create daily_requests table
    op.create_table(
        'daily_requests',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('request_lat', sa.Float(), nullable=False),
        sa.Column('request_lng', sa.Float(), nullable=False),
        sa.Column('is_default_day', sa.Boolean(), default=False),
        sa.Column('is_modified', sa.Boolean(), default=False),
        sa.Column('status', sa.String(), default='PENDING'),
        sa.Column('allocated_bus_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('buses.id'), nullable=True),
        sa.Column('allocated_seat_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('seats.id'), nullable=True),
        sa.UniqueConstraint('user_id', 'date', name='unique_user_date_request')
    )


def downgrade() -> None:
    op.drop_table('daily_requests')
    op.drop_column('users', 'default_days')
    op.drop_column('users', 'home_lng')
    op.drop_column('users', 'home_lat')
