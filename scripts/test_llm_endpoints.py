"""
Script to test the LLM analytics endpoints.
This script will:
1. Create a test user if it doesn't exist
2. Login with the test user
3. Trigger the LLM analysis endpoint
4. Get the LLM analytics data from the endpoint
"""
import asyncio
import json
import os
import sys
import time
import uuid
from datetime import datetime

# Add the parent directory to sys.path to make imports work
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import aiohttp
from sqlalchemy import text
from database import get_db
from config.config import settings
from passlib.context import CryptContext

# Configuration
BASE_URL = "http://localhost:8000"
API_PATH = f"{settings.API_V1_STR}"

# Test user credentials
TEST_EMAIL = "test@example.com"
TEST_PASSWORD = "testpassword123"

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

async def create_test_user():
    """Create a test user if it doesn't exist."""
    hashed_password = pwd_context.hash(TEST_PASSWORD)
    user_id = str(uuid.uuid4())
    
    async for db in get_db():
        try:
            # Check if user exists
            result = await db.execute(
                text("SELECT id FROM \"user\" WHERE email = :email"),
                {"email": TEST_EMAIL}
            )
            user = result.scalar_one_or_none()
            
            if user:
                print(f"Test user {TEST_EMAIL} already exists, skipping creation.")
                return True
            
            # Create user
            await db.execute(
                text("""
                    INSERT INTO "user" (id, email, password_hash, is_active, is_verified, first_name, last_name)
                    VALUES (:id, :email, :password, true, true, 'Test', 'User')
                """),
                {"id": user_id, "email": TEST_EMAIL, "password": hashed_password}
            )
            await db.commit()
            print(f"Created test user {TEST_EMAIL} with ID {user_id}")
            return True
        except Exception as e:
            print(f"Error creating test user: {e}")
            await db.rollback()
            return False

async def login():
    """Login and get access token."""
    async with aiohttp.ClientSession() as session:
        login_data = {
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD,
        }
        async with session.post(f"{BASE_URL}{API_PATH}/auth/login", json=login_data) as response:
            if response.status != 200:
                print(f"Login failed: {response.status}")
                response_text = await response.text()
                print(response_text)
                return None
            
            response_data = await response.json()
            token = response_data.get("access_token")
            return token

async def trigger_llm_analysis(token):
    """Trigger the LLM analysis endpoint."""
    headers = {"Authorization": f"Bearer {token}"}
    
    async with aiohttp.ClientSession() as session:
        async with session.post(f"{BASE_URL}{API_PATH}/analytics/llm-analysis", headers=headers) as response:
            status = response.status
            response_data = await response.json()
            
            print(f"Trigger LLM Analysis Response (Status {status}):")
            print(json.dumps(response_data, indent=2))
            
            return status in [200, 202]

async def get_llm_analytics(token, limit=5):
    """Get LLM analytics data."""
    headers = {"Authorization": f"Bearer {token}"}
    
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{BASE_URL}{API_PATH}/analytics/llm-analytics?limit={limit}", headers=headers) as response:
            status = response.status
            response_data = await response.json()
            
            print(f"Get LLM Analytics Response (Status {status}):")
            print(json.dumps(response_data, indent=2))
            
            return response_data

async def main():
    # Create test user if needed
    if not await create_test_user():
        print("Failed to create test user. Exiting.")
        return
    
    # Login
    print("\nLogging in...")
    token = await login()
    if not token:
        print("Failed to login. Exiting.")
        return
    
    print("Login successful!")
    
    # Trigger LLM analysis
    print("\nTriggering LLM analysis...")
    success = await trigger_llm_analysis(token)
    if not success:
        print("Failed to trigger LLM analysis. Exiting.")
        return
    
    print("LLM analysis triggered successfully!")
    
    # Wait for processing to complete
    print("\nWaiting for LLM processing to complete (5 seconds)...")
    time.sleep(5)
    
    # Get LLM analytics
    print("\nGetting LLM analytics data...")
    analytics_data = await get_llm_analytics(token)
    
    print("\nTest completed!")

if __name__ == "__main__":
    asyncio.run(main()) 