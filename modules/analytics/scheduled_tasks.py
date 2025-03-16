"""Scheduled tasks module for analytics"""
import asyncio
import logging
from datetime import datetime, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy.ext.asyncio import AsyncSession

from config.config import settings
from modules.analytics.batch_analytics import process_hourly_traffic_images
from database import get_db

# Configure logging
logger = logging.getLogger(__name__)

# Create a scheduler
scheduler = AsyncIOScheduler()

async def hourly_traffic_analysis_task():
    """
    Task to run hourly traffic image analysis.
    This will process 5 evenly spaced images from the previous hour.
    """
    logger.info("Starting hourly traffic image analysis task")
    
    # Get the previous hour
    previous_hour = datetime.utcnow().replace(minute=0, second=0, microsecond=0) - timedelta(hours=1)
    
    try:
        # Get database session
        async for db in get_db():
            # Process the images from the previous hour
            results = await process_hourly_traffic_images(
                db=db,
                gemini_api_key=settings.GEMINI_API_KEY,
                target_hour=previous_hour
            )
            
            logger.info(f"Successfully processed {len(results)} traffic images for hour {previous_hour}")
    except Exception as e:
        logger.error(f"Error in hourly traffic analysis task: {e}")

def schedule_tasks():
    """
    Set up all scheduled analytics tasks.
    """
    # Schedule the hourly traffic analysis task to run at the beginning of each hour
    scheduler.add_job(
        hourly_traffic_analysis_task,
        'cron',
        hour='*',  # Run at the start of every hour
        minute=1,  # Run at 1 minute past the hour to allow for any lag in data ingestion
        id='hourly_traffic_analysis'
    )
    
    logger.info("Scheduled hourly traffic analysis task")
    
    # Start the scheduler
    scheduler.start()
    logger.info("Task scheduler started")

def shutdown_tasks():
    """
    Shutdown the scheduler.
    """
    scheduler.shutdown()
    logger.info("Task scheduler shutdown") 