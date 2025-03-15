"""Merge branches

Revision ID: de62cc077806
Revises: 71a0e5ce0d49, f4b3c102e7e3
Create Date: 2025-03-15 16:34:32.572732

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'de62cc077806'
down_revision: Union[str, None] = ('71a0e5ce0d49', 'f4b3c102e7e3')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
