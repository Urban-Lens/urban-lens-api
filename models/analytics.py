"""Analytics models for the application."""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Index
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func

from models.base import Base


class LLMAnalytics(Base):
    """LLM Analytics model for storing LLM run data."""
    
    __tablename__ = "llm_analytics"
    
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    prompt = Column(Text, nullable=False)
    response = Column(Text, nullable=False)
    execution_time_ms = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=True)
    
    # Add indexes
    __table_args__ = (
        Index('idx_llm_analytics_timestamp', 'timestamp'),
    )
    
    def __repr__(self):
        """Return string representation."""
        return f"<LLMAnalytics(id={self.id}, timestamp={self.timestamp})>"
