"""add_missing_ontario_chunk_fields

Revision ID: 501fdf9c34ae
Revises: 17fe0f09d9c9
Create Date: 2025-09-19 22:26:23.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '501fdf9c34ae'
down_revision: Union[str, Sequence[str], None] = '17fe0f09d9c9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add missing fields to ontario_chunks table."""
    # Add chunk_type column with default value
    op.add_column('ontario_chunks', sa.Column('chunk_type', sa.String(length=20), nullable=False, server_default='article'))
    
    # Add title column
    op.add_column('ontario_chunks', sa.Column('title', sa.String(length=200), nullable=True))
    
    # Create indexes
    op.create_index(op.f('ix_ontario_chunks_chunk_type'), 'ontario_chunks', ['chunk_type'], unique=False)
    op.create_index(op.f('ix_ontario_chunks_division'), 'ontario_chunks', ['division'], unique=False)


def downgrade() -> None:
    """Remove added fields from ontario_chunks table."""
    op.drop_index(op.f('ix_ontario_chunks_division'), table_name='ontario_chunks')
    op.drop_index(op.f('ix_ontario_chunks_chunk_type'), table_name='ontario_chunks')
    
    op.drop_column('ontario_chunks', 'title')
    op.drop_column('ontario_chunks', 'chunk_type')
