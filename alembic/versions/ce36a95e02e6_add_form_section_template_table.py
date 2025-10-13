"""add_form_section_template_table

Revision ID: ce36a95e02e6
Revises: 4c7749ea073d
Create Date: 2025-10-13 17:20:48.237921

"""
from typing import Sequence, Union
import json
import os
from pathlib import Path

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite


# revision identifiers, used by Alembic.
revision: str = 'ce36a95e02e6'
down_revision: Union[str, Sequence[str], None] = '4c7749ea073d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create form_section_template table
    op.create_table(
        'form_section_template',
        sa.Column('question_number', sa.String(length=10), nullable=False),
        sa.Column('form_title', sa.String(length=255), nullable=False),
        sa.Column('question_to_answer', sa.Text(), nullable=True),
        sa.Column('obc_reference', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.PrimaryKeyConstraint('question_number')
    )
    
    # Seed data from questions.json
    questions_file = Path(__file__).parent.parent.parent / 'assets' / 'questions.json'
    if questions_file.exists():
        with open(questions_file, 'r') as f:
            questions = json.load(f)
        
        # Prepare bulk insert data
        form_templates = []
        for question in questions:
            form_templates.append({
                'question_number': question['question_number'],
                'form_title': question['original_title_in_code_matrix'],
                'question_to_answer': question.get('question_to_answer'),
                'obc_reference': json.dumps(question.get('obc_reference', []))
            })
        
        # Insert data
        if form_templates:
            op.bulk_insert(
                sa.table('form_section_template',
                    sa.column('question_number', sa.String),
                    sa.column('form_title', sa.String),
                    sa.column('question_to_answer', sa.Text),
                    sa.column('obc_reference', sa.String)
                ),
                form_templates
            )
    
    # Add foreign key constraint to section table
    with op.batch_alter_table('section', schema=None) as batch_op:
        batch_op.create_foreign_key(
            'fk_section_form_template',
            'form_section_template',
            ['form_section_number'],
            ['question_number']
        )


def downgrade() -> None:
    """Downgrade schema."""
    # Remove foreign key constraint from section table
    with op.batch_alter_table('section', schema=None) as batch_op:
        batch_op.drop_constraint('fk_section_form_template', type_='foreignkey')
    
    # Drop form_section_template table
    op.drop_table('form_section_template')
