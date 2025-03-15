"""Tests for user registration and management"""
import pytest
import requests
import time
import uuid

from tests.config import TEST_USER, TEST_USER_2, AUTH_DATA, API_URL
from tests.utils import make_request, is_valid_uuid

def register_test_user(user_data=None):
    """Register a test user and return the user ID"""
    if user_data is None:
        user_data = TEST_USER.copy()  # Use a copy to avoid modifying the original
    
    # Create a unique email to avoid conflicts
    timestamp = int(time.time())
    user_data["email"] = f"test_user_{timestamp}@example.com"
    
    # Register the test user
    register_data = {
        "email": user_data["email"],
        "password": user_data["password"],
        "first_name": user_data["first_name"],
        "last_name": user_data["last_name"],
        "company_name": user_data["company_name"]
    }
    
    response_data, status_code = make_request(
        "post", 
        "/users/", 
        data=register_data,
        expected_status=201
    )
    
    assert status_code == 201, f"Expected status 201, got {status_code}"
    assert "id" in response_data, "User ID not found in response"
    assert is_valid_uuid(response_data["id"]), f"Invalid UUID: {response_data['id']}"
    
    # Save the user ID and email for testing
    AUTH_DATA["user_id"] = response_data["id"]
    TEST_USER["email"] = user_data["email"]  # Update the test email
    
    print(f"Registered test user: {user_data['email']} with ID: {response_data['id']}")
    return response_data["id"]

def test_register_user():
    """Test registering a new user"""
    user_id = register_test_user()
    assert user_id, "Failed to register user"
    print(f"Successfully registered user with ID: {user_id}")
    return user_id


def test_register_duplicate_user():
    """Test registering a duplicate user fails"""
    # Make sure we have a registered user
    if not AUTH_DATA.get("user_id"):
        test_register_user()
    
    # Try to register the same user again
    register_data = {
        "email": TEST_USER["email"],
        "password": TEST_USER["password"],
        "first_name": TEST_USER["first_name"],
        "last_name": TEST_USER["last_name"],
        "company_name": TEST_USER["company_name"]
    }
    
    response_data, status_code = make_request(
        "post", 
        "/users/", 
        data=register_data, 
        expected_status=400
    )
    
    assert status_code == 400, f"Expected status 400, got {status_code}"
    assert "detail" in response_data, "Error detail not found in response"
    
    # Check if the error message contains something about duplicate or already exists
    error_message = response_data.get("detail", "").lower()
    assert any(word in error_message for word in ["duplicate", "already exists", "already registered"]), \
        f"Unexpected error message: {error_message}"


def test_register_invalid_user():
    """Test registering a user with invalid data fails"""
    # Register with missing required fields
    register_data = {
        "email": "invalid_test@example.com",
        # Missing password and other required fields
    }
    
    response_data, status_code = make_request(
        "post", 
        "/users/", 
        data=register_data, 
        expected_status=422
    )
    
    assert status_code == 422, f"Expected status 422, got {status_code}"
    assert "detail" in response_data, "Error detail not found in response"


def test_get_user_by_id():
    """Test getting a user by ID"""
    # Make sure we have a registered user
    if not AUTH_DATA.get("user_id"):
        test_register_user()
    
    # Get the user by ID
    response_data, status_code = make_request(
        "get", 
        f"/users/{AUTH_DATA['user_id']}", 
        auth=True
    )
    
    assert status_code == 200, f"Expected status 200, got {status_code}"
    assert "id" in response_data, "User ID not found in response"
    assert "email" in response_data, "Email not found in response"
    
    # Validate data
    assert response_data["id"] == AUTH_DATA["user_id"]
    assert response_data["email"] == TEST_USER["email"]


def test_get_nonexistent_user():
    """Test getting a nonexistent user"""
    nonexistent_id = str(uuid.uuid4())
    
    response_data, status_code = make_request(
        "get", 
        f"/users/{nonexistent_id}", 
        auth=True, 
        expected_status=404
    )
    
    assert status_code == 404, f"Expected status 404, got {status_code}"
    assert "detail" in response_data, "Error detail not found in response"


def test_update_user():
    """Test updating a user"""
    # Make sure we have a registered user
    if not AUTH_DATA.get("user_id"):
        test_register_user()
    
    # Make sure we have a token
    if not AUTH_DATA.get("access_token"):
        from tests.test_auth import test_login
        test_login()
    
    # Update the user
    updated_name = f"Updated Name {int(time.time())}"
    update_data = {
        "first_name": updated_name
    }
    
    response_data, status_code = make_request(
        "put",
        f"/users/{AUTH_DATA['user_id']}",
        data=update_data,
        auth=True
    )
    
    assert status_code == 200, f"Expected status 200, got {status_code}"
    assert "id" in response_data, "User ID not found in response"
    assert "first_name" in response_data, "Name not found in response"
    
    # Validate data
    assert response_data["id"] == AUTH_DATA["user_id"]
    assert response_data["first_name"] == updated_name


def test_update_user_unauthorized():
    """Test updating a user without authentication fails"""
    # Make sure we have a registered user
    if not AUTH_DATA.get("user_id"):
        test_register_user()
    
    # Try to update without authentication
    update_data = {
        "first_name": "Updated without auth"
    }
    
    response_data, status_code = make_request(
        "put",
        f"/users/{AUTH_DATA['user_id']}",
        data=update_data,
        auth=False,
        expected_status=401
    )
    
    assert status_code == 401, f"Expected status 401, got {status_code}"


def test_list_users():
    """Test listing users"""
    # Make sure we have a registered user
    if not AUTH_DATA.get("user_id"):
        test_register_user()
    
    # Make sure we have a token
    if not AUTH_DATA.get("access_token"):
        from tests.test_auth import test_login
        test_login()
    
    # List users
    response_data, status_code = make_request(
        "get", 
        "/users/", 
        auth=True
    )
    
    assert status_code == 200, f"Expected status 200, got {status_code}"
    assert isinstance(response_data, list), "Expected a list of users"
    
    # Check if our test user is in the list
    user_ids = [user.get("id") for user in response_data]
    assert AUTH_DATA["user_id"] in user_ids, "Test user not found in user list"


def run_tests():
    """Run all user tests in sequence"""
    # Start with a clean slate
    AUTH_DATA["user_id"] = None
    AUTH_DATA["access_token"] = None
    
    # Run the tests
    try:
        test_register_user()
        test_register_duplicate_user()
        test_register_invalid_user()
        test_get_user_by_id()
        test_get_nonexistent_user()
        
        # These tests require authentication
        from tests.test_auth import test_login
        test_login()
        
        test_update_user()
        test_list_users()
        print("All user tests completed successfully!")
    except Exception as e:
        print(f"Error in user tests: {e}")


if __name__ == "__main__":
    # Run all tests
    run_tests() 