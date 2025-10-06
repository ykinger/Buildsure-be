"""rename_tables_plural_to_singular

Revision ID: de88b817ca2c
Revises: a60785074581
Create Date: 2025-10-05 22:12:15.908377

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'de88b817ca2c'
down_revision: Union[str, Sequence[str], None] = 'a60785074581'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Rename tables from plural to singular
    op.rename_table('organizations', 'organization')
    op.rename_table('users', 'user')
    op.rename_table('answers', 'answer')
    op.rename_table('ontario_chunks', 'ontario_chunk')
    op.rename_table('sections', 'section')
    op.rename_table('projects', 'project')
    # 'conversation' is already singular, no need to rename


def downgrade() -> None:
    """Downgrade schema."""
    # Revert table names back to plural
    op.rename_table('project', 'projects')
    op.rename_table('section', 'sections')
    op.rename_table('ontario_chunk', 'ontario_chunks')
    op.rename_table('answer', 'answers')
    op.rename_table('user', 'users')
    op.rename_table('organization', 'organizations')
    # 'conversation' remains unchanged
