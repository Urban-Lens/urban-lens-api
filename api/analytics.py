"""Analytics API endpoints"""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Dict, Any, Optional
import uuid
from datetime import datetime, timedelta

from database import get_db
from config.config import settings
from modules.analytics.batch_analytics import (
    process_hourly_traffic_images, 
    get_hourly_images, 
    run_llm_analysis,
    get_llm_analytics,
    get_traffic_metrics
)
from api.auth import get_current_active_user

router = APIRouter(
    prefix="/analytics",
    tags=["analytics"],
)

@router.post("/traffic-analysis", status_code=status.HTTP_202_ACCEPTED)
async def trigger_traffic_analysis(
    hours_ago: int = Query(1, description="Process images from X hours ago"),
    custom_prompt: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """
    Trigger traffic image analysis for a specific hour.
    This is an asynchronous operation - it returns immediately but processing continues in the background.
    
    - **hours_ago**: Process images from X hours ago
    - **custom_prompt**: Optional custom prompt for the Gemini API analysis
    """
    # Calculate the target hour
    target_hour = datetime.utcnow().replace(minute=0, second=0, microsecond=0) - timedelta(hours=hours_ago)
    
    # Start the processing in the background
    async def process_in_background():
        if custom_prompt:
            # Custom processing with provided prompt
            from modules.analytics.batch_analytics import get_hourly_images, analyze_image_with_gemini_base64, store_analysis_results
            
            records = await get_hourly_images(db, target_hour)
            
            for record in records:
                analysis_result = analyze_image_with_gemini_base64(
                    record["output_img_path"], 
                    settings.GEMINI_API_KEY, 
                    custom_prompt
                )
                await store_analysis_results(db, record["id"], analysis_result)
        else:
            # Use standard processing
            await process_hourly_traffic_images(
                db=db,
                gemini_api_key=settings.GEMINI_API_KEY,
                target_hour=target_hour
            )
    
    # Schedule the background task
    import asyncio
    task = asyncio.create_task(process_in_background())
    
    return {
        "message": f"Traffic analysis started for hour {target_hour}",
        "target_hour": target_hour.isoformat(),
        "custom_prompt": custom_prompt is not None
    }

@router.get("/traffic-analysis")
async def get_traffic_analysis(
    source_id: Optional[str] = None,
    hours_ago: int = Query(24, description="Get analysis from the last X hours"),
    limit: int = Query(10, description="Maximum number of records to return"),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """
    Get traffic analysis results from the database.
    Filter by source_id and time range.
    """
    # Calculate the time range
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(hours=hours_ago)
    
    # Build the query
    query = text("""
        SELECT 
            id, timestamp, source_id, output_img_path, 
            people_ct, vehicle_ct, analysis_result
        FROM 
            timeseries_analytics
        WHERE 
            timestamp >= :start_time
            AND timestamp <= :end_time
            AND analysis_result IS NOT NULL
            AND output_img_path IS NOT NULL
    """)
    
    params = {"start_time": start_time, "end_time": end_time}
    
    # Add source_id filter if provided
    if source_id:
        query = text(query.text + " AND source_id = :source_id")
        params["source_id"] = source_id
    
    # Add limit and order
    query = text(query.text + " ORDER BY timestamp DESC LIMIT :limit")
    params["limit"] = limit
    
    # Execute the query
    result = await db.execute(query, params)
    records = result.mappings().all()
    
    # Convert to list of dicts
    return [dict(record) for record in records]

@router.get("/traffic-sources")
async def get_traffic_sources(
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """
    Get a list of all traffic sources (cameras) in the system.
    """
    query = text("""
        SELECT DISTINCT source_id
        FROM timeseries_analytics
        WHERE output_img_path IS NOT NULL
        ORDER BY source_id
    """)
    
    result = await db.execute(query)
    sources = [row[0] for row in result.fetchall()]
    
    return {"sources": sources}

@router.post("/llm-analysis", status_code=status.HTTP_202_ACCEPTED)
async def trigger_llm_analysis(
    db: AsyncSession = Depends(get_db)
):
    """
    Trigger LLM analysis with a hard-coded prompt.
    This is an asynchronous operation - it returns immediately but processing continues in the background.
    """
    # Start the processing in the background
    async def process_in_background():
        await run_llm_analysis(db=db, gemini_api_key=settings.GEMINI_API_KEY)
    
    # Schedule the background task
    import asyncio
    task = asyncio.create_task(process_in_background())
    
    return {
        "message": "LLM analysis started",
        "timestamp": datetime.utcnow().isoformat()
    }

@router.get("/llm-analytics")
async def get_llm_analysis_data(
    limit: int = Query(10, description="Maximum number of records to return"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get LLM analytics data from the database.
    """
    records = await get_llm_analytics(db=db, limit=limit)
    return records

@router.get("/metrics")
async def get_metrics(
    skip: int = 0,
    limit: Optional[int] = None,
    address_filter: Optional[str] = None,
    location_id: Optional[uuid.UUID] = None,
    time_aggregation: Optional[str] = Query(
        None, 
        description="Time aggregation level (hour, day, or None for raw data)"
    ),
    db: AsyncSession = Depends(get_db)
):
    """
    Get traffic metrics from the timeseries_analytics table.
    
    Parameters:
        - skip: Number of records to skip (for pagination)
        - limit: Maximum number of records to return (None for unlimited)
        - address_filter: Filter by location address (partial match)
        - location_id: Filter by location ID (UUID)
        - time_aggregation: Aggregate data by time interval (hour, day) or None for raw data
    
    Returns:
        - totals: sum of people_ct and vehicle_ct
        - timeseries: people_ct and vehicle_ct over time, ordered by latest timestamp
        - pagination: metadata for pagination
        - aggregation: the time aggregation level used
    """
    metrics = await get_traffic_metrics(
        db, 
        skip, 
        limit, 
        address_filter, 
        location_id, 
        time_aggregation
    )
    return metrics 