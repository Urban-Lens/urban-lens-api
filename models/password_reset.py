from sqlalchemy import Column, String, DateTime, ForeignKey, select
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession

from models.base import BaseModel
from database import Base


class PasswordReset(BaseModel, Base):
    """Model for storing password reset tokens"""
    
    # Link to the user
    user_id = Column(UUID(as_uuid=True), ForeignKey("user.id"), nullable=False)
    
    # The reset token
    token = Column(String(100), nullable=False, index=True, unique=True)
    
    # Expiration time (typically 24 hours)
    expires_at = Column(DateTime, nullable=False)
    
    # Additional fields
    is_used = Column(String(1), default="N", nullable=False)
    
    @property
    def is_expired(self) -> bool:
        """Check if the token has expired"""
        return datetime.utcnow() > self.expires_at
    
    @property
    def is_valid(self) -> bool:
        """Check if the token is valid (not expired and not used)"""
        return not self.is_expired and self.is_used == "N"
    
    @classmethod
    async def create_token(cls, db: AsyncSession, user_id: uuid.UUID, token: str, expires_in_hours: int = 24):
        """Create a new password reset token"""
        expires_at = datetime.utcnow() + timedelta(hours=expires_in_hours)
        return await cls.create(db, user_id=user_id, token=token, expires_at=expires_at)
    
    @classmethod
    async def get_by_token(cls, db: AsyncSession, token: str):
        """Get a password reset by token"""
        query = select(cls).where(cls.token == token)
        result = await db.execute(query)
        return result.scalars().first()
    
    async def mark_as_used(self, db: AsyncSession):
        """Mark the token as used"""
        return await self.update(db, is_used="Y") 