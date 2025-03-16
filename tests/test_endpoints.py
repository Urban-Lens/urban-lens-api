"""Tests for API endpoints"""
import sys
import os
from pathlib import Path
import requests
import json

# Add the parent directory to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

from tests.config import API_URL, TEST_USER

def test_user_endpoints():
    """Test user-related endpoints"""
    print("\nTesting user endpoints:")
    
    # Test user creation (POST /api/v1/users/)
    user_data = {
        "first_name": TEST_USER["first_name"],
        "last_name": TEST_USER["last_name"],
        "email": f"test_{os.urandom(4).hex()}@example.com",  # Random email to avoid conflicts
        "password": TEST_USER["password"],
        "company_name": TEST_USER["company_name"]
    }
    
    print(f"- Creating user with email: {user_data['email']}")
    response = requests.post(f"{API_URL}/users/", json=user_data)
    print(f"  Status: {response.status_code}")
    
    if response.status_code == 201:
        user_id = response.json()["id"]
        print(f"  Created user ID: {user_id}")
        
        # Test getting user by ID (GET /api/v1/users/{user_id})
        print(f"- Getting user with ID: {user_id}")
        response = requests.get(f"{API_URL}/users/{user_id}")
        print(f"  Status: {response.status_code}")
        
        # Test user login (POST /api/v1/auth/login)
        print(f"- Logging in as user: {user_data['email']}")
        login_data = {
            "email": user_data["email"],
            "password": user_data["password"]
        }
        response = requests.post(
            f"{API_URL}/auth/login", 
            json=login_data,
            headers={"Content-Type": "application/json"}
        )
        print(f"  Status: {response.status_code}")
        
        if response.status_code == 200:
            token_data = response.json()
            access_token = token_data["access_token"]
            print(f"  Got access token: {access_token[:10]}...")
            
            # Test auth/me endpoint (GET /api/v1/auth/me)
            print(f"- Getting current user profile")
            auth_header = {"Authorization": f"Bearer {access_token}"}
            response = requests.get(f"{API_URL}/auth/me", headers=auth_header)
            print(f"  Status: {response.status_code}")
    else:
        print(f"  Error creating user: {response.text}")


def test_auth_endpoints():
    """Test authentication-related endpoints"""
    print("\nTesting auth endpoints:")
    
    # Test forgot password (POST /api/v1/auth/forgot-password)
    print("- Testing forgot password endpoint")
    forgot_data = {"email": "test@example.com"}
    response = requests.post(f"{API_URL}/auth/forgot-password", json=forgot_data)
    print(f"  Status: {response.status_code}")
    
    # Test reset password endpoint exists (POST /api/v1/auth/reset-password)
    print("- Testing reset password endpoint")
    reset_data = {"token": "dummy_token", "new_password": "NewPassword123!"}
    response = requests.post(f"{API_URL}/auth/reset-password", json=reset_data)
    print(f"  Status: {response.status_code}")


if __name__ == "__main__":
    print("TESTING API ENDPOINTS")
    print("=" * 50)
    
    try:
        test_user_endpoints()
        test_auth_endpoints()
        
        print("\nEndpoint testing completed.")
    except Exception as e:
        print(f"\nError during testing: {str(e)}")
        print("Please ensure the API server is running and configured correctly.") 