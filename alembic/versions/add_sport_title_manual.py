"""Add sport_title to user_arbitrage_history

Revision ID: add_sport_title_column
Revises: 
Create Date: 2026-01-22 22:35:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_sport_title_column'
down_revision = None  # You might need to check the latest migration in versions folder and set this!
branch_labels = None
depends_on = None


def upgrade():
    # Attempt to add the column, catch error if it exists (safe migration)
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [c['name'] for c in inspector.get_columns('user_arbitrage_history')]
    
    if 'sport_title' not in columns:
        op.add_column('user_arbitrage_history', sa.Column('sport_title', sa.String(), nullable=True))


def downgrade():
    op.drop_column('user_arbitrage_history', 'sport_title')
