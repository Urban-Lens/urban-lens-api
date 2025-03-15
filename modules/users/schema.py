from typing import Optional
from pydantic import BaseModel, EmailStr, Field, validator
from datetime import datetime
import uuid


class UserBase(BaseModel):
    """Base schema for common user attributes"""
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    company_name: Optional[str] = Field(None, max_length=255)
    industry: Optional[str] = Field(None, max_length=255)


class UserCreate(UserBase):
    """Schema for creating a new user"""
    password: str = Field(..., min_length=8)
    
    @validator('password')
    def password_strength(cls, v):
        """Validate password strength"""
        if not any(char.isdigit() for char in v):
            raise ValueError('Password must contain at least one digit')
        if not any(char.isupper() for char in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(char.islower() for char in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(char in "!@#$%^&*()-_=+[]{}|;:,.<>?/" for char in v):
            raise ValueError('Password must contain at least one special character')
        return v


class UserUpdate(BaseModel):
    """Schema for updating user information"""
    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    email: Optional[EmailStr] = None
    company_name: Optional[str] = Field(None, max_length=255)
    industry: Optional[str] = Field(None, max_length=255)


class UserPasswordUpdate(BaseModel):
    """Schema for updating user password"""
    current_password: str
    new_password: str = Field(..., min_length=8)
    
    @validator('new_password')
    def password_strength(cls, v):
        """Validate password strength"""
        if not any(char.isdigit() for char in v):
            raise ValueError('Password must contain at least one digit')
        if not any(char.isupper() for char in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(char.islower() for char in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(char in "!@#$%^&*()-_=+[]{}|;:,.<>?/" for char in v):
            raise ValueError('Password must contain at least one special character')
        return v


class UserResponse(UserBase):
    """Schema for returning user information"""
    id: uuid.UUID
    is_active: bool
    is_verified: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        orm_mode = True
        from_attributes = True
