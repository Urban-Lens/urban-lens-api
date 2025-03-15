"""Add industry field to User model

Revision ID: 275be6e147f0
Revises: 77db7e958a41
Create Date: 2025-03-15 16:58:45.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '275be6e147f0'
down_revision: Union[str, None] = '77db7e958a41'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add the industry column to the user table
    op.add_column('user', sa.Column('industry', sa.String(255), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    # Remove the industry column
    op.drop_column('user', 'industry')
