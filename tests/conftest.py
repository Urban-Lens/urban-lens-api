"""pytest configuration and fixtures"""
import pytest
import requests
import time
from tests.config import TEST_USER, TEST_USER_2, AUTH_DATA, API_URL
from tests.utils import make_request


@pytest.fixture(scope="session", autouse=True)
def cleanup_after_tests():
    """Fixture to clean up after all tests have run"""
    # This is executed before any tests
    yield
    # This is executed after all tests
    
    # Clean up any test users or data
    # Only do this if we've created a user during tests
    if AUTH_DATA.get("user_id"):
        try:
            print(f"\nCleaning up test data...")
            # If we have an access token, try to delete the test user
            if AUTH_DATA.get("access_token"):
                # Delete user endpoint would be needed for this
                # make_request("delete", f"/users/{AUTH_DATA['user_id']}", auth=True)
                pass
        except Exception as e:
            print(f"Error during cleanup: {e}")
    
    print("Test cleanup complete")


@pytest.fixture(scope="session")
def registered_user():
    """Fixture to ensure a test user is registered"""
    from tests.test_users import test_register_user
    
    # Register a user if not already registered
    if not AUTH_DATA.get("user_id"):
        test_register_user()
    
    return AUTH_DATA["user_id"]


@pytest.fixture(scope="session")
def auth_token():
    """Fixture to ensure we have an authentication token"""
    from tests.test_auth import test_login
    
    # Login if not already logged in
    if not AUTH_DATA.get("access_token"):
        test_login()
    
    return AUTH_DATA["access_token"]


@pytest.fixture(scope="session")
def auth_headers(auth_token):
    """Fixture to get authentication headers"""
    return {
        "Authorization": f"Bearer {auth_token}"
    }


@pytest.fixture
def second_test_user():
    """Fixture to create a second test user when needed"""
    from tests.test_users import register_test_user
    
    # Create a second test user
    user_id = register_test_user(TEST_USER_2)
    
    # Return the user ID
    return user_id 