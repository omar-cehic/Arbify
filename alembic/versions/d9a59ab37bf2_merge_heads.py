"""merge_heads

Revision ID: d9a59ab37bf2
Revises: 5182105bb3c6, 7f8e9d1a2b3c
Create Date: 2025-08-17 20:20:18.711744

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd9a59ab37bf2'
down_revision: Union[str, None] = ('5182105bb3c6', '7f8e9d1a2b3c')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
