"""change text columns to array

Revision ID: 521193414770
Revises: 9844de5f176b
Create Date: 2025-09-04 22:36:16.083891

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '521193414770'
down_revision: Union[str, Sequence[str], None] = '9844de5f176b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Change code_matrix_questions from TEXT to TEXT[]
    op.alter_column('code_matrix_status', 'code_matrix_questions',
                   type_=sa.ARRAY(sa.Text()),
                   schema='buildsure',
                   postgresql_using='ARRAY[code_matrix_questions]::TEXT[]')
    
    # Change clarifying_questions from TEXT to TEXT[]
    op.alter_column('code_matrix_status', 'clarifying_questions',
                   type_=sa.ARRAY(sa.Text()),
                   schema='buildsure',
                   postgresql_using='ARRAY[clarifying_questions]::TEXT[]')


def downgrade() -> None:
    """Downgrade schema."""
    # Change code_matrix_questions back from TEXT[] to TEXT
    op.alter_column('code_matrix_status', 'code_matrix_questions',
                   type_=sa.Text(),
                   schema='buildsure',
                   postgresql_using='code_matrix_questions[1]')
    
    # Change clarifying_questions back from TEXT[] to TEXT
    op.alter_column('code_matrix_status', 'clarifying_questions',
                   type_=sa.Text(),
                   schema='buildsure',
                   postgresql_using='clarifying_questions[1]')
