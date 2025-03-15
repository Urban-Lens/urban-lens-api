"""Fix missing migration

Revision ID: 71a0e5ce0d49
Revises: fcb05a4d9b2d
Create Date: 2025-03-15 15:25:11.870281

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '71a0e5ce0d49'
down_revision: Union[str, None] = 'fcb05a4d9b2d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
