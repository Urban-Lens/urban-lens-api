from typing import Optional
from pydantic import BaseModel, EmailStr, Field


class Token(BaseModel):
    """Token schema for authentication response"""
    access_token: str
    token_type: str
    
    
class TokenData(BaseModel):
    """Token data schema for JWT payload"""
    user_id: Optional[str] = None
    
    
class LoginRequest(BaseModel):
    """Login request schema"""
    email: EmailStr
    password: str
    
    
class PasswordResetRequest(BaseModel):
    """Password reset request schema"""
    email: EmailStr
    
    
class PasswordResetConfirm(BaseModel):
    """Password reset confirmation schema"""
    token: str = Field(..., min_length=32)
    new_password: str = Field(..., min_length=8)
    
    
class ChangePasswordRequest(BaseModel):
    """Change password request schema"""
    current_password: str
    new_password: str = Field(..., min_length=8)
