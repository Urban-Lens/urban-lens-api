#!/usr/bin/env python
"""
Test script for the JSON login endpoint
"""
import sys
import os
from pathlib import Path
import requests
import json

# Add the parent directory to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

# API base URL - change if needed
API_BASE_URL = "http://localhost:8000"
API_V1_PREFIX = "/api/v1"
API_URL = f"{API_BASE_URL}{API_V1_PREFIX}"

def test_json_login():
    """Test the JSON login endpoint"""
    print("Testing JSON login endpoint...")
    
    # Login data
    login_data = {
        "email": "user@example.com",
        "password": "Password2@"
    }
    
    # Set headers with proper content type
    headers = {"Content-Type": "application/json"}
    
    # Make request
    url = f"{API_URL}/auth/login"
    print(f"Making POST request to {url}")
    print(f"With data: {json.dumps(login_data)}")
    
    try:
        response = requests.post(url, json=login_data, headers=headers)
        print(f"Status code: {response.status_code}")
        print(f"Response headers: {response.headers}")
        print(f"Response body: {response.text}")
        
        # Try to parse response as JSON
        try:
            data = response.json()
            print(f"Parsed JSON response: {data}")
        except json.JSONDecodeError:
            print("Response is not valid JSON")
    
    except Exception as e:
        print(f"Error making request: {e}")

if __name__ == "__main__":
    test_json_login() 