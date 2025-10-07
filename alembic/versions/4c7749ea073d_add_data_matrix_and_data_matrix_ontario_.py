"""Add data_matrix and data_matrix_ontario_chunk tables

Revision ID: 4c7749ea073d
Revises: de88b817ca2c
Create Date: 2025-10-06 17:47:12.536221

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4c7749ea073d'
down_revision: Union[str, Sequence[str], None] = 'de88b817ca2c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create data_matrix table
    op.create_table('data_matrix',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('guide', sa.Text(), nullable=False),
        sa.Column('number', sa.String(10), nullable=False),
        sa.Column('alternate_number', sa.String(10), nullable=True),
        sa.Column('title', sa.String(200), nullable=False),
        sa.Column('question', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes for data_matrix
    op.create_index(op.f('ix_data_matrix_number'), 'data_matrix', ['number'], unique=False)
    op.create_index(op.f('ix_data_matrix_alternate_number'), 'data_matrix', ['alternate_number'], unique=False)

    # Create data_matrix_ontario_chunk pivot table
    op.create_table('data_matrix_ontario_chunk',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('data_matrix_id', sa.String(36), nullable=False),
        sa.Column('ontario_chunk_id', sa.String(36), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['data_matrix_id'], ['data_matrix.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['ontario_chunk_id'], ['ontario_chunk.id'], ondelete='CASCADE')
    )

    # Create indexes for pivot table
    op.create_index(op.f('ix_data_matrix_ontario_chunk_data_matrix_id'), 'data_matrix_ontario_chunk', ['data_matrix_id'], unique=False)
    op.create_index(op.f('ix_data_matrix_ontario_chunk_ontario_chunk_id'), 'data_matrix_ontario_chunk', ['ontario_chunk_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    # Drop indexes first
    op.drop_index(op.f('ix_data_matrix_ontario_chunk_ontario_chunk_id'), table_name='data_matrix_ontario_chunk')
    op.drop_index(op.f('ix_data_matrix_ontario_chunk_data_matrix_id'), table_name='data_matrix_ontario_chunk')
    op.drop_index(op.f('ix_data_matrix_alternate_number'), table_name='data_matrix')
    op.drop_index(op.f('ix_data_matrix_number'), table_name='data_matrix')

    # Drop tables
    op.drop_table('data_matrix_ontario_chunk')
    op.drop_table('data_matrix')
