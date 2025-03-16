#!/usr/bin/env python
"""
Test script for the traffic image analysis functionality
"""
import asyncio
import sys
import os
from pathlib import Path
import logging

# Add the parent directory to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

from database import get_db
from config.config import settings
from modules.analytics.batch_analytics import process_hourly_traffic_images, get_hourly_images
from datetime import datetime, timedelta

async def test_get_hourly_images():
    """Test the get_hourly_images function"""
    logger.info("Testing get_hourly_images...")
    
    # Use the current hour
    current_hour = datetime.utcnow().replace(minute=0, second=0, microsecond=0)
    
    async for db in get_db():
        try:
            # Get images from the last 5 hours
            for i in range(5):
                target_hour = current_hour - timedelta(hours=i)
                logger.info(f"Getting images for hour: {target_hour}")
                
                records = await get_hourly_images(db, target_hour)
                logger.info(f"Found {len(records)} records for hour {target_hour}")
                
                for record in records:
                    logger.info(f"  Source: {record['source_id']}, Timestamp: {record['timestamp']}")
        except Exception as e:
            logger.error(f"Error in test_get_hourly_images: {e}", exc_info=True)

async def test_process_images():
    """Test the process_hourly_traffic_images function"""
    logger.info("Testing process_hourly_traffic_images...")
    
    # Use the current hour
    current_hour = datetime.utcnow().replace(minute=0, second=0, microsecond=0) - timedelta(hours=1)
    
    async for db in get_db():
        try:
            # Process images
            logger.info(f"Processing images for hour: {current_hour}")
            results = await process_hourly_traffic_images(
                db=db,
                gemini_api_key=settings.GEMINI_API_KEY,
                target_hour=current_hour
            )
            
            logger.info(f"Processed {len(results)} images")
            
            for result in results:
                logger.info(f"Result for record {result['id']}:")
                logger.info(f"  Source: {result['source_id']}")
                logger.info(f"  Analysis: {result['analysis_result'][:100]}...")  # Show just the first 100 chars
        except Exception as e:
            logger.error(f"Error in test_process_images: {e}", exc_info=True)

async def main():
    """Run all tests"""
    await test_get_hourly_images()
    await test_process_images()

if __name__ == "__main__":
    asyncio.run(main()) 