"""add thread_id to users

Revision ID: 6690198318e6
Revises: f9af4b6bee5f
Create Date: 2026-03-23 16:30:00.972549

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6690198318e6'
down_revision: Union[str, Sequence[str], None] = 'f9af4b6bee5f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add thread_id column to users table
    op.add_column('users', sa.Column('thread_id', sa.String(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    # Remove thread_id column from users table
    op.drop_column('users', 'thread_id')
