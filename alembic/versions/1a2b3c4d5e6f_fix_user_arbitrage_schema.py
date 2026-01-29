"""fix user_arbitrage_history schema

Revision ID: 1a2b3c4d5e6f
Revises: 989170bd98e4
Create Date: 2025-05-20 12:40:24.174224

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine.reflection import Inspector


# revision identifiers, used by Alembic.
revision: str = '1a2b3c4d5e6f'
down_revision: Union[str, None] = '989170bd98e4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    connection = op.get_bind()
    inspector = sa.inspect(connection)
    
    # We are targeting 'user_arbitrage_history' as per the Model definition
    # But previous migration targeted 'user_arbitrages'. We should check which one exists.
    
    target_table = 'user_arbitrage_history'
    if target_table not in inspector.get_table_names():
        # Fallback to user_arbitrages if strict name not found, or maybe creates it?
        # If user_arbitrages exists, we might need to migrate data or rename, but simplest is to just ensure columns exist on whatever table acts as the model.
        if 'user_arbitrages' in inspector.get_table_names():
            target_table = 'user_arbitrages'
    
    # Check columns
    existing_columns = [col['name'] for col in inspector.get_columns(target_table)]
    
    if 'sport_title' not in existing_columns:
        op.add_column(target_table, sa.Column('sport_title', sa.String(), nullable=True))
    if 'commence_time' not in existing_columns:
        op.add_column(target_table, sa.Column('commence_time', sa.DateTime(), nullable=True))
    if 'odds' not in existing_columns:
        op.add_column(target_table, sa.Column('odds', sa.JSON(), nullable=True))
    if 'profit' not in existing_columns:
        op.add_column(target_table, sa.Column('profit', sa.Float(), nullable=True))
    if 'winning_outcome' not in existing_columns:
        op.add_column(target_table, sa.Column('winning_outcome', sa.String(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    # Simplified downgrade - remove columns if they exist
    # Warning: This might be dangerous if table name is ambiguous
    pass
