#!/usr/bin/env python
"""
Script to make a direct request to a specified URL
"""
import sys
import requests
import json

def make_request(url):
    """Make a direct request to the specified URL"""
    print(f"Making request to: {url}")
    
    # Login data
    login_data = {
        "email": "user@example.com",
        "password": "Password2@"
    }
    
    # Set headers with proper content type
    headers = {"Content-Type": "application/json"}
    
    try:
        # Make the request
        response = requests.post(url, json=login_data, headers=headers, timeout=10)
        
        # Print response details
        print(f"Status code: {response.status_code}")
        print(f"Response headers: {response.headers}")
        print(f"Response body: {response.text}")
        
        # Try to parse as JSON
        try:
            data = response.json()
            print(f"Parsed JSON: {json.dumps(data, indent=2)}")
        except json.JSONDecodeError:
            print("Response is not valid JSON")
            
    except requests.exceptions.RequestException as e:
        print(f"Error making request: {e}")

if __name__ == "__main__":
    # Check if URL was provided as argument
    if len(sys.argv) > 1:
        url = sys.argv[1]
    else:
        # Default URL if none provided
        url = input("Enter the URL to send the request to: ")
    
    make_request(url) 