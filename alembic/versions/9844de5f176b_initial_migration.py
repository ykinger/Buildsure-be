"""initial_migration

Revision ID: 9844de5f176b
Revises: 
Create Date: 2025-09-03 20:17:19.679479

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9844de5f176b'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create projects table with curr_task column
    op.create_table('projects',
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('name', sa.String(length=255), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('due_date', sa.Date(), nullable=True),
    sa.Column('organization_id', sa.String(length=36), nullable=False),
    sa.Column('status', sa.String(length=32), nullable=False, server_default='not_started'),
    sa.Column('curr_task', sa.String(length=255), nullable=True),
    sa.Column('created_by', sa.String(length=36), nullable=True),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    schema='buildsure'
    )
    
    # Create code_matrix_status table
    op.create_table('code_matrix_status',
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('org_id', sa.String(length=36), nullable=False),
    sa.Column('project_id', sa.String(length=36), nullable=False),
    sa.Column('code_matrix_questions', sa.Text(), nullable=True),
    sa.Column('clarifying_questions', sa.Text(), nullable=True),
    sa.Column('curr_section', sa.String(length=255), nullable=True),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['project_id'], ['buildsure.projects.id'], ),
    sa.PrimaryKeyConstraint('id'),
    schema='buildsure'
    )


def downgrade() -> None:
    """Downgrade schema."""
    # Drop code_matrix_status table
    op.drop_table('code_matrix_status', schema='buildsure')
    
    # Drop projects table
    op.drop_table('projects', schema='buildsure')
