"""Test configuration and constants"""

# API base URL
API_BASE_URL = "http://localhost:8000"
API_V1_PREFIX = "/api/v1"  # Updated: API uses /api/v1 prefix

# Full API URL
API_URL = f"{API_BASE_URL}{API_V1_PREFIX}"

# Test user credentials
TEST_USER = {
    "first_name": "Test",
    "last_name": "User",
    "email": "testuser@example.com",
    "password": "Test1234!",
    "company_name": "Test Company"
}

# Additional test users
TEST_USER_2 = {
    "first_name": "John",
    "last_name": "Doe",
    "email": "johndoe@example.com",
    "password": "Secure123!",
    "company_name": "Acme Inc"
}

# Store tokens and user data during tests
AUTH_DATA = {
    "access_token": None,
    "token_type": None,
    "user_id": None,
    "reset_token": None,
    "api_url": API_URL  # Add API URL for direct requests
} 