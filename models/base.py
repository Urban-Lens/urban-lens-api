import uuid
from datetime import datetime
from sqlalchemy import Column, DateTime, Boolean, String, select
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.ext.asyncio import AsyncSession

class BaseModel:
    """Base class for all models to inherit common fields and methods"""
    
    # Generate a UUID primary key for all models
    @declared_attr
    def id(cls):
        return Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Timestamps
    @declared_attr
    def created_at(cls):
        return Column(DateTime, default=datetime.utcnow)
    
    @declared_attr
    def updated_at(cls):
        return Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
        
    # Generate tablename from class name
    @declared_attr
    def __tablename__(cls):
        return cls.__name__.lower()
    
    # Common string representation
    def __repr__(self):
        return f"<{self.__class__.__name__} {self.id}>"
    
    # Helper methods for CRUD operations
    @classmethod
    async def get_by_id(cls, db: AsyncSession, id):
        """Get a record by ID"""
        query = select(cls).where(cls.id == id)
        result = await db.execute(query)
        return result.scalars().first()
    
    @classmethod
    async def get_all(cls, db: AsyncSession, skip=0, limit=100):
        """Get all records with pagination"""
        query = select(cls).offset(skip).limit(limit)
        result = await db.execute(query)
        return result.scalars().all()
    
    @classmethod
    async def create(cls, db: AsyncSession, **kwargs):
        """Create a new record"""
        obj = cls(**kwargs)
        db.add(obj)
        await db.commit()
        await db.refresh(obj)
        return obj
    
    async def update(self, db: AsyncSession, **kwargs):
        """Update an existing record"""
        for key, value in kwargs.items():
            setattr(self, key, value)
        await db.commit()
        await db.refresh(self)
        return self
    
    async def delete(self, db: AsyncSession):
        """Delete a record"""
        await db.delete(self)
        await db.commit()
        return True

