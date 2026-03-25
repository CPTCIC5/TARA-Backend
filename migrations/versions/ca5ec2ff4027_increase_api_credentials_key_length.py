"""increase_api_credentials_key_length

Revision ID: ca5ec2ff4027
Revises: 6690198318e6
Create Date: 2026-03-25 14:19:02.657914

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ca5ec2ff4027'
down_revision: Union[str, Sequence[str], None] = '6690198318e6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Increase varchar length for all key columns in api_credentials
    op.alter_column('api_credentials', 'key_1', type_=sa.String(500), existing_type=sa.String(255))
    op.alter_column('api_credentials', 'key_2', type_=sa.String(500), existing_type=sa.String(255))
    op.alter_column('api_credentials', 'key_3', type_=sa.String(500), existing_type=sa.String(255))
    op.alter_column('api_credentials', 'key_4', type_=sa.String(500), existing_type=sa.String(255))
    op.alter_column('api_credentials', 'key_5', type_=sa.String(500), existing_type=sa.String(255))
    op.alter_column('api_credentials', 'key_6', type_=sa.String(500), existing_type=sa.String(255))


def downgrade() -> None:
    """Downgrade schema."""
    # Revert to original varchar length
    op.alter_column('api_credentials', 'key_1', type_=sa.String(255), existing_type=sa.String(500))
    op.alter_column('api_credentials', 'key_2', type_=sa.String(255), existing_type=sa.String(500))
    op.alter_column('api_credentials', 'key_3', type_=sa.String(255), existing_type=sa.String(500))
    op.alter_column('api_credentials', 'key_4', type_=sa.String(255), existing_type=sa.String(500))
    op.alter_column('api_credentials', 'key_5', type_=sa.String(255), existing_type=sa.String(500))
    op.alter_column('api_credentials', 'key_6', type_=sa.String(255), existing_type=sa.String(500))
