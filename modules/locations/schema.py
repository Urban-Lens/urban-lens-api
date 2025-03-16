from typing import Optional, List
from pydantic import BaseModel, Field, validator
from datetime import datetime
import uuid

class LocationBase(BaseModel):
    """Base schema for location data"""
    address: str
    latitude: float
    longitude: float
    description: Optional[str] = None
    tags: Optional[List[str]] = None
    input_stream_url: Optional[str] = None
    output_stream_url: Optional[str] = None
    thumbnail: Optional[str] = None

class LocationCreate(LocationBase):
    """Schema for creating a new location"""
    pass

class LocationUpdate(BaseModel):
    """Schema for updating an existing location"""
    address: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    description: Optional[str] = None
    tags: Optional[List[str]] = None
    input_stream_url: Optional[str] = None
    output_stream_url: Optional[str] = None
    thumbnail: Optional[str] = None

class LocationResponse(LocationBase):
    """Schema for location response data"""
    id: uuid.UUID
    user_id: Optional[uuid.UUID] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        orm_mode = True
        from_attributes = True 