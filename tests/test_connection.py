"""Basic connection tests for the API"""
import sys
import os
from pathlib import Path
import requests

# Add the parent directory to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

from tests.config import API_URL, API_BASE_URL

def test_api_connection():
    """Test that we can connect to the API"""
    try:
        # Try the root endpoint first
        response = requests.get(f"{API_BASE_URL}/")
        print(f"API root endpoint response: {response.status_code}")
        print(f"API response: {response.text[:100]}..." if len(response.text) > 100 else f"API response: {response.text}")
        
        # Then try the API version endpoint
        response = requests.get(f"{API_URL}/")
        print(f"API version endpoint response: {response.status_code}")
        print(f"API response: {response.text[:100]}..." if len(response.text) > 100 else f"API response: {response.text}")
        
        return True
    except Exception as e:
        print(f"Error connecting to API: {e}")
        return False

def check_server_status():
    """Check if server is running on port 8000"""
    import socket
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = s.connect_ex(('localhost', 8000))
    s.close()
    return result == 0

if __name__ == "__main__":
    print("Checking API server status...")
    if check_server_status():
        print("API server is running on port 8000.")
        print("\nTesting API connection...")
        if test_api_connection():
            print("\nAPI connection successful.")
        else:
            print("\nAPI connection failed.")
    else:
        print("API server is NOT running on port 8000.")
        
    print("\nTroubleshooting recommendations:")
    print("1. Ensure the API server is running on port 8000")
    print("2. Check API server logs for errors")
    print("3. Verify database configuration is correct")
    print("4. Check that required endpoints are implemented")
    print("5. Update API_BASE_URL and API_V1_PREFIX in tests/config.py if needed") 