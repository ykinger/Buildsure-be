"""create_new_schema

Revision ID: create_new_schema
Revises:
Create Date: 2025-10-26

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ea6030a04a41'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    # Organization
    op.create_table(
        'organization',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text),
        sa.Column('created_at', sa.DateTime, server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime, server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False)
    )
    op.create_index('ix_organization_name', 'organization', ['name'])

    # User
    op.create_table(
        'user',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('organization_id', sa.String(36), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('created_at', sa.DateTime, server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime, server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['organization_id'], ['organization.id'], ondelete='CASCADE')
    )
    op.create_index('ix_user_email', 'user', ['email'], unique=True)
    op.create_index('ix_user_organization_id', 'user', ['organization_id'])

    # Project
    op.create_table(
        'project',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('organization_id', sa.String(36), nullable=False),
        sa.Column('user_id', sa.String(36), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text),
        sa.Column('status', sa.String(20), nullable=False),
        sa.Column('created_at', sa.DateTime, server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime, server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['organization_id'], ['organization.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ondelete='CASCADE')
    )
    op.create_index('ix_project_organization_id', 'project', ['organization_id'])
    op.create_index('ix_project_user_id', 'project', ['user_id'])

    # DataMatrix
    op.create_table(
        'data_matrix',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('number', sa.String(10), nullable=False),
        sa.Column('alternate_number', sa.String(10)),
        sa.Column('title', sa.String(200), nullable=False),
        sa.Column('guide', sa.Text, nullable=False),
        sa.Column('question', sa.Text, nullable=False),
        sa.Column('created_at', sa.DateTime, server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False)
    )
    op.create_index('ix_data_matrix_number', 'data_matrix', ['number'])
    op.create_index('ix_data_matrix_alternate_number', 'data_matrix', ['alternate_number'])

    # ProjectDataMatrix
    op.create_table(
        'project_data_matrix',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('project_id', sa.String(36), nullable=False),
        sa.Column('data_matrix_id', sa.String(36), nullable=False),
        sa.Column('status', sa.String(20), nullable=False),
        sa.Column('output', sa.JSON),
        sa.Column('created_at', sa.DateTime, server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime, server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['project_id'], ['project.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['data_matrix_id'], ['data_matrix.id'], ondelete='CASCADE')
    )
    op.create_index('ix_project_data_matrix_project_id', 'project_data_matrix', ['project_id'])
    op.create_index('ix_project_data_matrix_data_matrix_id', 'project_data_matrix', ['data_matrix_id'])

    # Message
    op.create_table(
        'message',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('project_data_matrix_id', sa.String(36), nullable=False),
        sa.Column('user_id', sa.String(36)),
        sa.Column('role', sa.String(20), nullable=False),
        sa.Column('content', sa.Text, nullable=False),
        sa.Column('created_at', sa.DateTime, server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['project_data_matrix_id'], ['project_data_matrix.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ondelete='SET NULL')
    )
    op.create_index('ix_message_project_data_matrix_id', 'message', ['project_data_matrix_id'])
    op.create_index('ix_message_user_id', 'message', ['user_id'])

    # KnowledgeBase
    op.create_table(
        'knowledge_base',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('source', sa.String(100), nullable=False),
        sa.Column('reference', sa.String(20), nullable=False),
        sa.Column('alternate_reference', sa.String(20)),
        sa.Column('content', sa.Text, nullable=False)
    )
    op.create_index('ix_knowledge_base_reference', 'knowledge_base', ['reference'])
    op.create_index('ix_knowledge_base_alternate_reference', 'knowledge_base', ['alternate_reference'])

    # DataMatrixKnowledgeBase
    op.create_table(
        'data_matrix_knowledge_base',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('data_matrix_id', sa.String(36), nullable=False),
        sa.Column('knowledge_base_id', sa.String(36), nullable=False),
        sa.ForeignKeyConstraint(['data_matrix_id'], ['data_matrix.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['knowledge_base_id'], ['knowledge_base.id'], ondelete='CASCADE')
    )
    op.create_index('ix_data_matrix_knowledge_base_data_matrix_id', 'data_matrix_knowledge_base', ['data_matrix_id'])
    op.create_index('ix_data_matrix_knowledge_base_knowledge_base_id', 'data_matrix_knowledge_base', ['knowledge_base_id'])


def downgrade():
    op.drop_table('data_matrix_knowledge_base')
    op.drop_table('knowledge_base')
    op.drop_table('message')
    op.drop_table('project_data_matrix')
    op.drop_table('data_matrix')
    op.drop_table('project')
    op.drop_table('user')
    op.drop_table('organization')
