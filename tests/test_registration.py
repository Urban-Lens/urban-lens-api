#!/usr/bin/env python
"""
Simple test script to check if user registration is working
"""
import os
import sys
import uuid
from pathlib import Path

# Add the parent directory to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from .utils import make_request
from .config import API_URL, TEST_USER

def test_user_registration():
    """Test user registration endpoint"""
    # Generate a unique email to avoid conflicts with existing users
    unique_email = f"test_{uuid.uuid4().hex[:8]}@example.com"
    
    # Registration data
    registration_data = {
        "email": unique_email,
        "password": "TestPassword123!",
        "first_name": "Test",
        "last_name": "User"
    }
    
    # Make the registration request
    response = make_request(
        method="POST",
        url=f"{API_URL}/auth/register",
        json=registration_data
    )
    
    # Assert response status code is 201 (Created)
    assert response.status_code == 201, f"Expected status code 201, got {response.status_code}"
    
    # Assert response contains user data
    response_data = response.json()
    assert "id" in response_data, "Response should contain user ID"
    assert "email" in response_data, "Response should contain email"
    assert response_data["email"] == unique_email, "Email in response should match registration email"
    assert "first_name" in response_data, "Response should contain first_name"
    assert response_data["first_name"] == "Test", "First name in response should match registration data"
    assert "last_name" in response_data, "Response should contain last_name"
    assert response_data["last_name"] == "User", "Last name in response should match registration data"
    
    # Password should not be returned in the response
    assert "password" not in response_data, "Response should not contain password"
    
    # Return the created user data for potential use in other tests
    return response_data

def test_duplicate_registration():
    """Test registration with an email that already exists"""
    # Use the TEST_USER email which should already exist
    registration_data = {
        "email": TEST_USER["email"],
        "password": "TestPassword123!",
        "first_name": "Duplicate",
        "last_name": "User"
    }
    
    # Make the registration request
    response = make_request(
        method="POST",
        url=f"{API_URL}/auth/register",
        json=registration_data
    )
    
    # Assert response status code is 400 (Bad Request)
    assert response.status_code == 400, f"Expected status code 400, got {response.status_code}"
    
    # Assert response contains error message about duplicate email
    response_data = response.json()
    assert "detail" in response_data, "Response should contain error detail"
    assert "email already exists" in response_data["detail"].lower(), "Error should mention duplicate email"

def test_invalid_registration_data():
    """Test registration with invalid data"""
    # Missing required fields
    registration_data = {
        "email": "incomplete@example.com",
        # Missing password
        "first_name": "Incomplete"
        # Missing last_name
    }
    
    # Make the registration request
    response = make_request(
        method="POST",
        url=f"{API_URL}/auth/register",
        json=registration_data
    )
    
    # Assert response status code is 422 (Unprocessable Entity)
    assert response.status_code == 422, f"Expected status code 422, got {response.status_code}"
    
    # Invalid email format
    registration_data = {
        "email": "not-an-email",
        "password": "TestPassword123!",
        "first_name": "Invalid",
        "last_name": "Email"
    }
    
    response = make_request(
        method="POST",
        url=f"{API_URL}/auth/register",
        json=registration_data
    )
    
    # Assert response status code is 422 (Unprocessable Entity)
    assert response.status_code == 422, f"Expected status code 422, got {response.status_code}"

if __name__ == "__main__":
    print("=" * 60)
    print("TESTING USER REGISTRATION".center(60))
    print("=" * 60)
    
    # Run the test
    result = test_user_registration()
    
    print("\n" + "=" * 60)
    print(f"Registration test {'PASSED' if result else 'FAILED'}")
    print("=" * 60) 