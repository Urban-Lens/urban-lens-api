"""add_analysis_result_column

Revision ID: a4e5b7c8d9f0
Revises: 97e4091f2439
Create Date: 2025-03-16 03:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect, text


# revision identifiers, used by Alembic.
revision: str = 'a4e5b7c8d9f0'
down_revision: Union[str, None] = '97e4091f2439'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add analysis_result column to timeseries_analytics table."""
    # Get connection
    conn = op.get_bind()
    
    # Check if the column already exists before trying to add it
    inspector = inspect(conn)
    columns = [col['name'] for col in inspector.get_columns('timeseries_analytics')]
    
    if 'analysis_result' not in columns:
        op.add_column('timeseries_analytics', sa.Column('analysis_result', sa.Text(), nullable=True))
    
    # Check if indexes exist before creating them
    result = conn.execute(text("""
        SELECT indexname FROM pg_indexes 
        WHERE tablename = 'timeseries_analytics' 
        AND indexname IN ('idx_timeseries_analytics_source_id', 'idx_timeseries_analytics_timestamp')
    """))
    existing_indexes = [row[0] for row in result]
    
    # Create source_id index if it doesn't exist
    if 'idx_timeseries_analytics_source_id' not in existing_indexes:
        op.create_index(
            op.f('idx_timeseries_analytics_source_id'), 
            'timeseries_analytics', 
            ['source_id'], 
            unique=False
        )
    
    # Create timestamp index if it doesn't exist
    if 'idx_timeseries_analytics_timestamp' not in existing_indexes:
        op.create_index(
            op.f('idx_timeseries_analytics_timestamp'), 
            'timeseries_analytics', 
            ['timestamp'], 
            unique=False
        )


def downgrade() -> None:
    """Remove analysis_result column from timeseries_analytics table."""
    # Check if column exists before dropping
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [col['name'] for col in inspector.get_columns('timeseries_analytics')]
    
    if 'analysis_result' in columns:
        op.drop_column('timeseries_analytics', 'analysis_result') 