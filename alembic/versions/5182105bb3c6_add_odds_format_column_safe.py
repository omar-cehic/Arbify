"""add_odds_format_column_safe

Revision ID: 5182105bb3c6
Revises: b4ba5accb799
Create Date: 2025-08-12 22:58:01.238502

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5182105bb3c6'
down_revision: Union[str, None] = 'b4ba5accb799'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Check if table exists and if column doesn't already exist
    connection = op.get_bind()
    inspector = sa.inspect(connection)
    
    if 'user_profiles' in inspector.get_table_names():
        existing_columns = [col['name'] for col in inspector.get_columns('user_profiles')]
        if 'odds_format' not in existing_columns:
            op.add_column('user_profiles', sa.Column('odds_format', sa.String(), nullable=True, default='decimal'))


def downgrade() -> None:
    """Downgrade schema."""
    # Check if table and column exist before trying to drop
    connection = op.get_bind()
    inspector = sa.inspect(connection)
    
    if 'user_profiles' in inspector.get_table_names():
        existing_columns = [col['name'] for col in inspector.get_columns('user_profiles')]
        if 'odds_format' in existing_columns:
            op.drop_column('user_profiles', 'odds_format')
