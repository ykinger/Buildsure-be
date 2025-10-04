"""Create conversation table

Revision ID: a60785074581
Revises: 1e86788e7e49
Create Date: 2025-10-03 21:12:02.539754

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import uuid


# revision identifiers, used by Alembic.
revision: str = 'a60785074581'
down_revision: Union[str, Sequence[str], None] = '1e86788e7e49'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'conversation',
        sa.Column('id', sa.String(length=36), primary_key=True, nullable=False, default=lambda: str(uuid.uuid4())),
        sa.Column('history', sa.Text, nullable=False)
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('conversation')
