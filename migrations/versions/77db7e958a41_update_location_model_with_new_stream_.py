"""Update location model with new stream fields

Revision ID: 77db7e958a41
Revises: de62cc077806
Create Date: 2025-03-15 16:47:46.089358

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '77db7e958a41'
down_revision: Union[str, None] = 'de62cc077806'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Remove the stream_link column
    op.drop_column('location', 'stream_link')
    
    # Add new columns
    op.add_column('location', sa.Column('input_stream_url', sa.String(255), nullable=True))
    op.add_column('location', sa.Column('output_stream_url', sa.String(255), nullable=True))
    op.add_column('location', sa.Column('thumbnail', sa.String(255), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    # Remove the new columns
    op.drop_column('location', 'input_stream_url')
    op.drop_column('location', 'output_stream_url')
    op.drop_column('location', 'thumbnail')
    
    # Add back the stream_link column
    op.add_column('location', sa.Column('stream_link', sa.String(255), nullable=True))
