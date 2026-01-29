"""add missing odds_format column to user_profiles

Revision ID: 7f8e9d1a2b3c
Revises: b4ba5accb799
Create Date: 2024-01-15 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '7f8e9d1a2b3c'
down_revision = 'b4ba5accb799'
branch_labels = None
depends_on = None


def upgrade():
    # Add odds_format column to user_profiles table
    try:
        op.add_column('user_profiles', sa.Column('odds_format', sa.String(), nullable=True))
        # Set default value for existing records
        op.execute("UPDATE user_profiles SET odds_format = 'decimal' WHERE odds_format IS NULL")
    except Exception as e:
        print(f"Migration warning: {e}")
        # Column might already exist, ignore error


def downgrade():
    # Remove odds_format column
    try:
        op.drop_column('user_profiles', 'odds_format')
    except Exception as e:
        print(f"Downgrade warning: {e}")