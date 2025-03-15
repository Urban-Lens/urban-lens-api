# Urban Lens API Tests

This directory contains automated tests for the Urban Lens API.

## Setup

1. Install test dependencies:
   ```bash
   pip install -r tests/requirements.txt
   ```

2. Make sure the API is running at `http://localhost:8000`

## Running Tests

To run all tests:
```bash
python tests/run_tests.py
```

To run specific test files:
```bash
python -m pytest tests/test_users.py -v
python -m pytest tests/test_auth.py -v
```

## Test Structure

- `test_auth.py` - Tests for authentication functionality (login, password reset, etc.)
- `test_users.py` - Tests for user management (registration, retrieval, updates)
- `test_endpoints.py` - Tests for API endpoint availability and basic functionality
- `test_connection.py` - Tests for API connectivity
- `test_registration.py` - Specific tests for user registration

## Configuration

Test configuration is stored in `config.py`. You can modify the following settings:
- `API_URL` - Base URL for the API
- `TEST_USER` - Default test user credentials
- `TEST_USER_2` - Alternative test user credentials

## Test Report

After running tests, you can view a detailed report in `TEST_REPORT.md`. 