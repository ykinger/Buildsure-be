"""add_ready_to_start_section_status

Revision ID: 301af3446445
Revises: remove_user_input_column
Create Date: 2025-09-23 21:56:06.094795

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '301af3446445'
down_revision: Union[str, Sequence[str], None] = 'remove_user_input_column'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # For SQLite, we need to handle enum changes differently
    # Since SQLite doesn't support ALTER TYPE, we'll use a more compatible approach
    
    # First, let's add the new enum value by recreating the constraint
    # This is handled automatically by SQLAlchemy when the model is updated
    
    # Update existing sections: set section 1 of each project to READY_TO_START if it's currently PENDING
    op.execute("""
        UPDATE sections 
        SET status = 'ready_to_start' 
        WHERE section_number = 1 
        AND status = 'pending'
        AND project_id IN (
            SELECT DISTINCT project_id 
            FROM sections 
            WHERE section_number = 1
        )
    """)


def downgrade() -> None:
    """Downgrade schema."""
    # Revert READY_TO_START back to PENDING
    op.execute("""
        UPDATE sections 
        SET status = 'pending' 
        WHERE status = 'ready_to_start'
    """)
