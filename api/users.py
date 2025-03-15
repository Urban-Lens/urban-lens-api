from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
import uuid

from database import get_db
from modules.users.schema import UserCreate, UserResponse, UserUpdate, UserPasswordUpdate
from modules.users.user_service import UserService

router = APIRouter(
    prefix="/users",
    tags=["users"],
)

@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new user"""
    user = await UserService.create_user(db, user_data)
    return user

@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get a user by ID"""
    user = await UserService.get_user_by_id(db, user_id)
    return user

@router.get("/", response_model=List[UserResponse])
async def get_users(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """Get a list of users with pagination"""
    users = await UserService.get_users(db, skip=skip, limit=limit)
    return users

@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: uuid.UUID,
    user_data: UserUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update a user's information"""
    user = await UserService.update_user(db, user_id, user_data)
    return user

@router.put("/{user_id}/password", response_model=UserResponse)
async def update_password(
    user_id: uuid.UUID,
    password_data: UserPasswordUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update a user's password"""
    user = await UserService.update_password(
        db, 
        user_id, 
        password_data.current_password, 
        password_data.new_password
    )
    return user

@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    """Delete a user"""
    await UserService.delete_user(db, user_id)
    return None 