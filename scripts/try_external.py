#!/usr/bin/env python
"""
Simple script to test a GET request to a public API
"""
import requests
import json

# Use a simple public API endpoint
url = "https://httpbin.org/post"

print(f"Making POST request to {url}")

# Simple data
data = {
    "email": "test@example.com",
    "password": "password123"
}

# Set headers
headers = {"Content-Type": "application/json"}

try:
    # Make POST request
    response = requests.post(url, json=data, headers=headers, timeout=10)
    
    # Print response details
    print(f"Status code: {response.status_code}")
    print(f"Response headers: {dict(response.headers)}")
    print(f"Response body: {response.text}")
    
    # Try to parse as JSON
    try:
        data = response.json()
        print(f"Parsed JSON: {json.dumps(data, indent=2)}")
    except json.JSONDecodeError:
        print("Response is not valid JSON")
        
except requests.exceptions.RequestException as e:
    print(f"Error making request: {e}") 