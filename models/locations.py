from sqlalchemy import Column, String, Float, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import relationship
from sqlalchemy.ext.asyncio import AsyncSession
import uuid

from models.base import BaseModel
from database import Base

class Location(BaseModel, Base):
    """Location model for storing geographical locations"""
    
    # Basic location information
    address = Column(String(255), nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    description = Column(Text, nullable=True)
    
    # Additional fields
    tags = Column(ARRAY(String(50)), nullable=True)
    
    # Streaming related fields
    input_stream_url = Column(String(255), nullable=True)
    output_stream_url = Column(String(255), nullable=True)
    thumbnail = Column(String(255), nullable=True)
    
    # Relationship with User
    user_id = Column(UUID(as_uuid=True), ForeignKey("user.id"), nullable=False)
    user = relationship("User", back_populates="locations")
    
    @classmethod
    async def get_by_user_id(cls, db: AsyncSession, user_id: uuid.UUID):
        """Get locations for a specific user"""
        from sqlalchemy import select
        query = select(cls).where(cls.user_id == user_id)
        result = await db.execute(query)
        return result.scalars().all() 