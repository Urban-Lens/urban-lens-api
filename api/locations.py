from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
import uuid

from database import get_db
from modules.locations.schema import LocationCreate, LocationResponse, LocationUpdate, PublicLocationResponse
from modules.locations.location_service import LocationService
from api.auth import get_current_active_user
from models.users import User

router = APIRouter(
    prefix="/locations",
    tags=["locations"],
)

@router.post("/", response_model=LocationResponse, status_code=status.HTTP_201_CREATED)
async def create_location(
    location_data: LocationCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new location for the current user"""
    location = await LocationService.create_location(db, location_data, current_user.id)
    return location

@router.get("/{location_id}", response_model=PublicLocationResponse)
async def get_location(
    location_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get a location by ID (public endpoint)"""
    location = await LocationService.get_location_by_id(db, location_id)
    return location

@router.get("/", response_model=List[PublicLocationResponse])
async def get_locations(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """Get a list of all locations with pagination (public endpoint)"""
    # Get all locations
    locations = await LocationService.get_locations(db, skip, limit)
    return locations

@router.post("/attach-location", response_model=LocationResponse)
async def attach_location_to_user(
    location_id: uuid.UUID,
    user_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Attach a location to a specific user.
    Requires authentication and admin privileges if attaching to a different user.
    """
    # Check permissions: user can only attach locations to themselves unless they're an admin
    if current_user.id != user_id and not hasattr(current_user, 'is_admin'):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to attach locations to other users"
        )
    
    # Attach the location to the user
    location = await LocationService.attach_location_to_user(db, location_id, user_id)
    return location

@router.get("/user/{user_id}", response_model=List[LocationResponse])
async def get_user_locations(
    user_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get all locations for a specific user (requires authentication)"""
    # Check if the current user is accessing their own locations or is an admin
    if current_user.id != user_id and not hasattr(current_user, 'is_admin'):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to access locations for this user"
        )
    
    locations = await LocationService.get_user_locations(db, user_id)
    return locations

@router.get("/me/", response_model=List[LocationResponse])
async def get_my_locations(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get all locations for the current user"""
    locations = await LocationService.get_user_locations(db, current_user.id)
    return locations

@router.put("/{location_id}", response_model=LocationResponse)
async def update_location(
    location_id: uuid.UUID,
    location_data: LocationUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Update a location"""
    location = await LocationService.get_location_by_id(db, location_id)
    
    # Make sure the user owns this location
    if location.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to update this location"
        )
    
    updated_location = await LocationService.update_location(db, location_id, location_data)
    return updated_location

@router.delete("/{location_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_location(
    location_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete a location"""
    location = await LocationService.get_location_by_id(db, location_id)
    
    # Make sure the user owns this location
    if location.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to delete this location"
        )
    
    await LocationService.delete_location(db, location_id)
    return None 