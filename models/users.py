from sqlalchemy import Column, String, Boolean, select
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession

from models.base import BaseModel
from database import Base

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class User(BaseModel, Base):
    """User model for the application"""
    
    # Basic user information
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    company_name = Column(String(255), nullable=True)
    
    # Account status
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    
    # Helper methods for password hashing
    @property
    def full_name(self):
        """Return user's full name"""
        return f"{self.first_name} {self.last_name}"
    
    @staticmethod
    def get_password_hash(password: str) -> str:
        """Hash a password for storage"""
        return pwd_context.hash(password)
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify a password against a hash"""
        return pwd_context.verify(plain_password, hashed_password)
    
    @classmethod
    async def create_user(cls, db, **kwargs):
        """Create a new user with proper password hashing"""
        # Hash the password if provided
        if "password" in kwargs:
            password = kwargs.pop("password")
            kwargs["password_hash"] = cls.get_password_hash(password)
        
        return await super().create(db, **kwargs)
    
    @classmethod
    async def get_by_email(cls, db: AsyncSession, email: str):
        """Get a user by email address"""
        query = select(cls).where(cls.email == email)
        result = await db.execute(query)
        return result.scalars().first()
    
    def __repr__(self):
        return f"<User {self.email} ({self.full_name})>"
