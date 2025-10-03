"""rename_section_number_to_form_section_number

Revision ID: 1e86788e7e49
Revises: 301af3446445
Create Date: 2025-10-01 23:15:05.676020

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1e86788e7e49'
down_revision: Union[str, Sequence[str], None] = '301af3446445'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - no backwards compatibility needed."""
    connection = op.get_bind()
    
    # Drop and recreate sections table with new schema
    op.drop_table('sections')
    op.create_table('sections',
        sa.Column('id', sa.String(36), primary_key=True, nullable=False),
        sa.Column('project_id', sa.String(36), sa.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False),
        sa.Column('form_section_number', sa.String(), nullable=False),
        sa.Column('status', sa.Enum('PENDING', 'READY_TO_START', 'IN_PROGRESS', 'COMPLETED', name='sectionstatus'), nullable=False),
        sa.Column('draft_output', sa.JSON(), nullable=True),
        sa.Column('final_output', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), nullable=False)
    )
    op.create_index('ix_sections_project_id', 'sections', ['project_id'])
    
    # Drop and recreate projects table with new current_section type
    op.drop_table('projects')
    op.create_table('projects',
        sa.Column('id', sa.String(36), primary_key=True, nullable=False),
        sa.Column('org_id', sa.String(36), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('status', sa.Enum('NOT_STARTED', 'IN_PROGRESS', 'COMPLETED', 'ON_HOLD', name='projectstatus'), nullable=False),
        sa.Column('current_section', sa.String(), nullable=False, default='3.01'),
        sa.Column('total_sections', sa.Integer(), nullable=False, default=0),
        sa.Column('completed_sections', sa.Integer(), nullable=False, default=0),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), nullable=False)
    )
    op.create_index('ix_projects_org_id', 'projects', ['org_id'])
    op.create_index('ix_projects_user_id', 'projects', ['user_id'])


def downgrade() -> None:
    """Downgrade schema - not supported since we don't need backwards compatibility."""
    raise NotImplementedError("No downgrade path - backwards compatibility not required")
