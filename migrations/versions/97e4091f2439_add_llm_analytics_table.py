"""add_llm_analytics_table

Revision ID: 97e4091f2439
Revises: 275be6e147f0
Create Date: 2025-03-15 20:51:00.507596

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '97e4091f2439'
down_revision: Union[str, None] = '275be6e147f0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create llm_analytics table."""
    op.create_table(
        'llm_analytics',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('timestamp', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('prompt', sa.Text(), nullable=False),
        sa.Column('response', sa.Text(), nullable=False),
        sa.Column('execution_time_ms', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create index on timestamp
    op.create_index('idx_llm_analytics_timestamp', 'llm_analytics', ['timestamp'])


def downgrade() -> None:
    """Drop llm_analytics table."""
    op.drop_index('idx_llm_analytics_timestamp', table_name='llm_analytics')
    op.drop_table('llm_analytics')
