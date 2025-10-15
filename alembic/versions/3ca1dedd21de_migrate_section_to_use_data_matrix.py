"""migrate_section_to_use_data_matrix

Revision ID: 3ca1dedd21de
Revises: 4c7749ea073d
Create Date: 2025-10-14 19:55:35.003008

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3ca1dedd21de'
down_revision: Union[str, Sequence[str], None] = '4c7749ea073d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema to use data_matrix instead of form_section_template."""
    # SQLite requires special handling for foreign key changes
    with op.batch_alter_table('section', schema=None) as batch_op:
        # Drop the foreign key to form_section_template
        batch_op.drop_constraint('fk_section_form_template', type_='foreignkey')
        # Create new foreign key to data_matrix
        batch_op.create_foreign_key(
            'fk_section_data_matrix',
            'data_matrix',
            ['form_section_number'],
            ['number']
        )
    
    # Drop the form_section_template table
    op.drop_table('form_section_template')


def downgrade() -> None:
    """Downgrade schema to use form_section_template."""
    # Recreate form_section_template table
    op.create_table(
        'form_section_template',
        sa.Column('question_number', sa.String(10), nullable=False),
        sa.Column('form_title', sa.String(255), nullable=False),
        sa.Column('question_to_answer', sa.Text(), nullable=True),
        sa.Column('obc_reference', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('question_number')
    )
    
    # Update section foreign key back to form_section_template
    with op.batch_alter_table('section', schema=None) as batch_op:
        batch_op.drop_constraint('fk_section_data_matrix', type_='foreignkey')
        batch_op.create_foreign_key(
            'fk_section_form_template',
            'form_section_template',
            ['form_section_number'],
            ['question_number']
        )
