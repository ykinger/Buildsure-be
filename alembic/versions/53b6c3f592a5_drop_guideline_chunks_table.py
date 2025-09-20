"""drop_guideline_chunks_table

Revision ID: 53b6c3f592a5
Revises: 501fdf9c34ae
Create Date: 2025-09-19 22:57:00.864278

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '53b6c3f592a5'
down_revision: Union[str, Sequence[str], None] = '501fdf9c34ae'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Drop the guideline_chunks table as it's been replaced by ontario_chunks."""
    # Drop the guideline_chunks table
    op.drop_table('guideline_chunks')


def downgrade() -> None:
    """Recreate the guideline_chunks table if needed."""
    # Recreate the guideline_chunks table structure
    op.create_table(
        'guideline_chunks',
        sa.Column('id', sa.VARCHAR(length=36), nullable=False),
        sa.Column('section_reference', sa.VARCHAR(length=20), nullable=False),
        sa.Column('section_title', sa.VARCHAR(length=500), nullable=True),
        sa.Column('section_level', sa.INTEGER(), nullable=False),
        sa.Column('chunk_text', sa.TEXT(), nullable=False),
        sa.Column('embedding', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DATETIME(), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_guideline_chunks_section_reference', 'guideline_chunks', ['section_reference'], unique=False)
