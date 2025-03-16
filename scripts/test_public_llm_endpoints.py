"""
Script to test the public LLM analytics endpoints.
This script will:
1. Trigger the LLM analysis endpoint
2. Get the LLM analytics data from the endpoint
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
    print("Testing public LLM analytics endpoints...")
    
    # Trigger LLM analysis
    print("\nTriggering LLM analysis...")
    success = await trigger_llm_analysis()
    if not success:
        print("Failed to trigger LLM analysis. Exiting.")
        return
    
    print("LLM analysis triggered successfully!")
    
    # Wait for processing to complete
    print("\nWaiting for LLM processing to complete (5 seconds)...")
    time.sleep(5)
    
    # Get LLM analytics
    print("\nGetting LLM analytics data...")
    analytics_data = await get_llm_analytics()
    
    print("\nTest completed!")

if __name__ == "__main__":
    asyncio.run(main()) 