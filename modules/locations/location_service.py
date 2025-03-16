from typing import List, Optional
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from models.locations import Location
from modules.locations.schema import LocationCreate, LocationUpdate

class LocationService:
    """Service for handling location-related operations"""
    
    @staticmethod
    async def create_location(db: AsyncSession, location_data: LocationCreate, user_id: Optional[uuid.UUID] = None) -> Location:
        """Create a new location"""
        location_dict = location_data.dict()
        if user_id:
            location_dict["user_id"] = user_id
        location = await Location.create(db, **location_dict)
        return location
    
    @staticmethod
    async def get_location_by_id(db: AsyncSession, location_id: uuid.UUID) -> Location:
        """Get a location by ID"""
        location = await Location.get_by_id(db, location_id)
        if not location:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Location not found"
            )
        return location
    
    @staticmethod
    async def get_locations(db: AsyncSession, skip: int = 0, limit: int = 100) -> List[Location]:
        """Get a list of locations with pagination"""
        return await Location.get_all(db, skip=skip, limit=limit)
    
    @staticmethod
    async def get_user_locations(db: AsyncSession, user_id: uuid.UUID) -> List[Location]:
        """Get all locations for a specific user"""
        return await Location.get_by_user_id(db, user_id)
    
    @staticmethod
    async def update_location(db: AsyncSession, location_id: uuid.UUID, location_data: LocationUpdate) -> Location:
        """Update a location"""
        location = await LocationService.get_location_by_id(db, location_id)
        
        # Filter out None values from the update data
        update_data = {k: v for k, v in location_data.dict().items() if v is not None}
        
        # Update the location attributes
        for key, value in update_data.items():
            setattr(location, key, value)
        
        # Commit changes
        db.add(location)
        await db.commit()
        await db.refresh(location)
        
        return location
    
    @staticmethod
    async def delete_location(db: AsyncSession, location_id: uuid.UUID) -> None:
        """Delete a location"""
        location = await LocationService.get_location_by_id(db, location_id)
        await db.delete(location)
        await db.commit() 