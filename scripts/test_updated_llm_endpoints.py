"""
Script to test the updated LLM analytics endpoints.
"""
import asyncio
import json
import os
import sys
import time
from datetime import datetime

# Add the parent directory to sys.path to make imports work
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import aiohttp
from config.config import settings

# Configuration
BASE_URL = "http://localhost:8000"
API_PATH = f"{settings.API_V1_STR}"

# Test image URL
TEST_IMAGE_URL = "https://intellibus-hackathon-bucket.s3.amazonaws.com/detections/rnXIjl_Rzy4_detection_20250316_015117.png"

async def manually_insert_test_data():
    """
    Insert a test record in the timeseries_analytics table to ensure there's data for the LLM to analyze.
    """
    from database import get_db
    from sqlalchemy import text
    
    current_time = datetime.utcnow()
    
    async for db in get_db():
        try:
            # Check if there are any records with output_img_path not null
            result = await db.execute(text("""
                SELECT COUNT(*) FROM timeseries_analytics WHERE output_img_path IS NOT NULL
            """))
            count = result.scalar_one()
            
            if count == 0:
                # Insert a test record
                query = text("""
                    INSERT INTO timeseries_analytics 
                    (timestamp, source_id, output_img_path, people_ct, vehicle_ct, detections)
                    VALUES (:timestamp, :source_id, :output_img_path, :people_ct, :vehicle_ct, :detections)
                    RETURNING id
                """)
                result = await db.execute(
                    query,
                    {
                        "timestamp": current_time,
                        "source_id": "test-camera",
                        "output_img_path": TEST_IMAGE_URL,
                        "people_ct": 2,
                        "vehicle_ct": 3,
                        "detections": json.dumps({"cars": 3, "people": 2})
                    }
                )
                record_id = result.scalar_one()
                await db.commit()
                print(f"Inserted test record with ID {record_id}")
                return True
            else:
                print(f"Found {count} existing records with images, no need to insert test data")
                
                # Update the most recent record to use our test image
                query = text("""
                    UPDATE timeseries_analytics
                    SET output_img_path = :output_img_path
                    WHERE id = (
                        SELECT id FROM timeseries_analytics 
                        WHERE output_img_path IS NOT NULL 
                        ORDER BY timestamp DESC LIMIT 1
                    )
                    RETURNING id
                """)
                result = await db.execute(query, {"output_img_path": TEST_IMAGE_URL})
                record_id = result.scalar_one()
                await db.commit()
                print(f"Updated record {record_id} to use test image URL")
                return True
        except Exception as e:
            await db.rollback()
            print(f"Error inserting/updating test data: {e}")
            return False

async def trigger_llm_analysis():
    """Trigger the LLM analysis endpoint."""
    async with aiohttp.ClientSession() as session:
        async with session.post(f"{BASE_URL}{API_PATH}/analytics/llm-analysis") as response:
            status = response.status
            response_data = await response.json()
            
            print(f"Trigger LLM Analysis Response (Status {status}):")
            print(json.dumps(response_data, indent=2))
            
            return status == 202

async def get_llm_analytics(limit=5):
    """Get LLM analytics data."""
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{BASE_URL}{API_PATH}/analytics/llm-analytics?limit={limit}") as response:
            status = response.status
            response_data = await response.json()
            
            print(f"Get LLM Analytics Response (Status {status}):")
            print(json.dumps(response_data, indent=2))
            
            return response_data

async def main():
    print("Testing updated LLM analytics endpoints...")
    
    # Insert test data if needed
    print("\nChecking and inserting test data if needed...")
    success = await manually_insert_test_data()
    if not success:
        print("Failed to insert/update test data. Continuing anyway...")
    
    # Trigger LLM analysis
    print("\nTriggering LLM analysis...")
    success = await trigger_llm_analysis()
    if not success:
        print("Failed to trigger LLM analysis. Exiting.")
        return
    
    print("LLM analysis triggered successfully!")
    
    # Wait for processing to complete
    print("\nWaiting for LLM processing to complete (10 seconds)...")
    time.sleep(10)
    
    # Get LLM analytics
    print("\nGetting LLM analytics data...")
    analytics_data = await get_llm_analytics()
    
    print("\nTest completed!")

if __name__ == "__main__":
    asyncio.run(main()) 