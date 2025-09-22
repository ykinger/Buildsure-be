"""remove_user_input_column_from_sections

Revision ID: remove_user_input_column
Revises: 53b6c3f592a5
Create Date: 2025-09-21 20:22:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite

# revision identifiers, used by Alembic.
revision: str = 'remove_user_input_column'
down_revision: Union[str, Sequence[str], None] = '53b6c3f592a5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - remove user_input column from sections table."""
    # Only drop the user_input column from sections table
    op.drop_column('sections', 'user_input')


def downgrade() -> None:
    """Downgrade schema - add back user_input column to sections table."""
    # Add back the user_input column
    op.add_column('sections', sa.Column('user_input', sqlite.JSON(), nullable=True))
