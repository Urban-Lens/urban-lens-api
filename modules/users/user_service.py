from typing import List, Optional
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from models.users import User
from modules.users.schema import UserCreate, UserUpdate


class UserService:
    """Service for handling user-related operations"""
    
    @staticmethod
    async def create_user(db: AsyncSession, user_data: UserCreate) -> User:
        """Create a new user"""
        # Check if user with this email already exists
        existing_user = await User.get_by_email(db, user_data.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User with this email already exists"
            )
        
        # Create the user
        user_dict = user_data.dict()
        user = await User.create_user(db, **user_dict)
        return user
    
    @staticmethod
    async def get_user_by_id(db: AsyncSession, user_id: uuid.UUID) -> User:
        """Get a user by ID"""
        user = await User.get_by_id(db, user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        return user
    
    @staticmethod
    async def get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
        """Get a user by email address"""
        return await User.get_by_email(db, email)
    
    @staticmethod
    async def get_users(db: AsyncSession, skip: int = 0, limit: int = 100) -> List[User]:
        """Get a list of users with pagination"""
        return await User.get_all(db, skip=skip, limit=limit)
    
    @staticmethod
    async def update_user(db: AsyncSession, user_id: uuid.UUID, user_data: UserUpdate) -> User:
        """Update a user's information"""
        user = await UserService.get_user_by_id(db, user_id)
        
        update_data = user_data.dict(exclude_unset=True)
        
        # If email is being updated, check if it's already in use
        if "email" in update_data and update_data["email"] != user.email:
            existing_user = await User.get_by_email(db, update_data["email"])
            if existing_user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already in use"
                )
        
        return await user.update(db, **update_data)
    
    @staticmethod
    async def update_password(db: AsyncSession, user_id: uuid.UUID, current_password: str, new_password: str) -> User:
        """Update a user's password"""
        user = await UserService.get_user_by_id(db, user_id)
        
        # Verify current password
        if not User.verify_password(current_password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Incorrect password"
            )
        
        # Update password
        password_hash = User.get_password_hash(new_password)
        return await user.update(db, password_hash=password_hash)
    
    @staticmethod
    async def delete_user(db: AsyncSession, user_id: uuid.UUID) -> bool:
        """Delete a user"""
        user = await UserService.get_user_by_id(db, user_id)
        return await user.delete(db)
