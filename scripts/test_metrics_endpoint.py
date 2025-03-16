"""
Script to test the metrics endpoint.
"""
import asyncio
import json
import os
import sys
import time
import random
from datetime import datetime, timedelta

# Add the parent directory to sys.path to make imports work
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import aiohttp
from config.config import settings

# Configuration
BASE_URL = "http://localhost:8000"
API_PATH = f"{settings.API_V1_STR}"

async def get_metrics():
    """Get traffic metrics."""
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{BASE_URL}{API_PATH}/analytics/metrics") as response:
            status = response.status
            try:
                response_data = await response.json()
                print(f"Metrics Response (Status {status}):")
                
                # Format totals
                print("\nTotals:")
                print("-" * 40)
                for key, value in response_data.get("totals", {}).items():
                    print(f"{key}: {value}")
                
                # Format time series data
                timeseries = response_data.get("timeseries", [])
                print(f"\nTimeseries data ({len(timeseries)} records):")
                print("-" * 80)
                print(f"{'Timestamp':<25} {'Source ID':<15} {'People':<10} {'Vehicles':<10}")
                print("-" * 80)
                
                # Print the first 5 and last 5 records
                max_display = 10
                if len(timeseries) > max_display:
                    for record in timeseries[:5]:
                        print(f"{record.get('timestamp', 'N/A'):<25} {record.get('source_id', 'N/A'):<15} {record.get('people_count', 0):<10} {record.get('vehicle_count', 0):<10}")
                    
                    print(f"\n... {len(timeseries) - max_display} more records ...")
                    
                    for record in timeseries[-5:]:
                        print(f"{record.get('timestamp', 'N/A'):<25} {record.get('source_id', 'N/A'):<15} {record.get('people_count', 0):<10} {record.get('vehicle_count', 0):<10}")
                else:
                    for record in timeseries:
                        print(f"{record.get('timestamp', 'N/A'):<25} {record.get('source_id', 'N/A'):<15} {record.get('people_count', 0):<10} {record.get('vehicle_count', 0):<10}")
                
                return response_data
            except Exception as e:
                print(f"Error processing response: {e}")
                print(f"Response text: {await response.text()}")
                return None

async def insert_test_data():
    """
    Insert test records in the timeseries_analytics table to ensure there's data for metrics.
    """
    from database import get_db
    from sqlalchemy import text
    
    current_time = datetime.utcnow()
    
    async for db in get_db():
        try:
            # Check if there are enough records with metrics data
            result = await db.execute(text("""
                SELECT COUNT(*) FROM timeseries_analytics 
                WHERE people_ct IS NOT NULL OR vehicle_ct IS NOT NULL
            """))
            count = result.scalar_one()
            
            if count < 10:
                print(f"Found only {count} records with metrics data, inserting more test data...")
                
                # Generate some test data spanning different times
                for i in range(10):
                    # Random data from the last 24 hours
                    timestamp = current_time - timedelta(hours=i*2, minutes=random.randint(0, 59))
                    source_id = f"camera-{random.randint(1, 3):03d}"
                    people_ct = random.randint(0, 10)
                    vehicle_ct = random.randint(0, 15)
                    detections = json.dumps({
                        "cars": vehicle_ct,
                        "people": people_ct,
                        "timestamp": timestamp.isoformat()
                    })
                    
                    # Insert the record
                    query = text("""
                        INSERT INTO timeseries_analytics 
                        (timestamp, source_id, people_ct, vehicle_ct, detections)
                        VALUES (:timestamp, :source_id, :people_ct, :vehicle_ct, :detections)
                        RETURNING id
                    """)
                    result = await db.execute(
                        query,
                        {
                            "timestamp": timestamp,
                            "source_id": source_id,
                            "people_ct": people_ct,
                            "vehicle_ct": vehicle_ct,
                            "detections": detections
                        }
                    )
                    record_id = result.scalar_one()
                
                await db.commit()
                print(f"Inserted 10 test records with metrics data")
                return True
            else:
                print(f"Found {count} existing records with metrics data, no need to insert more")
                return True
        except Exception as e:
            await db.rollback()
            print(f"Error inserting test metrics data: {e}")
            return False

async def main():
    print("Testing metrics endpoint...")
    
    # Insert test data if needed
    print("\nChecking and inserting test data if needed...")
    success = await insert_test_data()
    if not success:
        print("Failed to insert test data. Continuing anyway...")
    
    # Get metrics
    print("\nGetting metrics data...")
    metrics_data = await get_metrics()
    
    if metrics_data:
        print("\nTest completed successfully!")
    else:
        print("\nTest failed!")

if __name__ == "__main__":
    asyncio.run(main()) 