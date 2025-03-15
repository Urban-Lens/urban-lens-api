from datetime import datetime, timedelta
from typing import Optional, Tuple
import uuid
from fastapi import HTTPException, status
from jose import jwt, JWTError
from sqlalchemy.ext.asyncio import AsyncSession
import secrets
import string

from config.config import settings
from models.users import User
from models.password_reset import PasswordReset
from modules.auth.schema import TokenData


class AuthService:
    """Service for handling authentication operations"""
    
    @staticmethod
    async def authenticate_user(db: AsyncSession, email: str, password: str) -> Optional[User]:
        """Authenticate a user with email and password"""
        user = await User.get_by_email(db, email)
        if not user:
            return None
        if not User.verify_password(password, user.password_hash):
            return None
        return user
    
    @staticmethod
    def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """Create a JWT access token"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        return encoded_jwt
    
    @staticmethod
    async def get_current_user(db: AsyncSession, token: str) -> User:
        """Get current user from JWT token"""
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            user_id: str = payload.get("sub")
            if user_id is None:
                raise credentials_exception
            token_data = TokenData(user_id=user_id)
        except JWTError:
            raise credentials_exception
        
        user = await User.get_by_id(db, uuid.UUID(token_data.user_id))
        if user is None:
            raise credentials_exception
        return user
    
    @staticmethod
    async def get_active_user(db: AsyncSession, token: str) -> User:
        """Get current active user from JWT token"""
        current_user = await AuthService.get_current_user(db, token)
        if not current_user.is_active:
            raise HTTPException(status_code=400, detail="Inactive user")
        return current_user
    
    @staticmethod
    def generate_password_reset_token(length: int = 32) -> str:
        """Generate a secure token for password reset"""
        alphabet = string.ascii_letters + string.digits
        return ''.join(secrets.choice(alphabet) for _ in range(length))
    
    @staticmethod
    async def request_password_reset(db: AsyncSession, email: str) -> Optional[Tuple[str, User]]:
        """Request a password reset and store the reset token in the database"""
        user = await User.get_by_email(db, email)
        if not user:
            # Don't reveal that the user doesn't exist
            return None
        
        # Generate a reset token
        reset_token = AuthService.generate_password_reset_token()
        
        # Store the reset token in the database
        await PasswordReset.create_token(db, user.id, reset_token)
        
        # Return the token and user (for email sending in a real app)
        return (reset_token, user)
    
    @staticmethod
    async def reset_password(db: AsyncSession, reset_token: str, new_password: str) -> bool:
        """Reset a user's password using a reset token"""
        # Check if the token exists and is valid
        token_record = await PasswordReset.get_by_token(db, reset_token)
        if not token_record or not token_record.is_valid:
            return False
        
        # Get the user
        user = await User.get_by_id(db, token_record.user_id)
        if not user:
            return False
        
        # Update the password
        password_hash = User.get_password_hash(new_password)
        await user.update(db, password_hash=password_hash)
        
        # Mark the token as used
        await token_record.mark_as_used(db)
        
        return True
