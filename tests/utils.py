"""Test utilities and helper functions"""
import requests
import json
import uuid
from typing import Dict, Any, Optional, Tuple

from tests.config import API_URL, AUTH_DATA


def get_auth_header() -> Dict[str, str]:
    """Get authorization header with access token"""
    if not AUTH_DATA["access_token"]:
        raise ValueError("No access token found. Login first.")
    
    return {"Authorization": f"Bearer {AUTH_DATA['access_token']}"}


def make_request(
    method: str,
    endpoint: str,
    data: Optional[Dict[str, Any]] = None,
    headers: Optional[Dict[str, str]] = None,
    auth: bool = False,
    expected_status: int = 200
) -> Tuple[Dict[str, Any], int]:
    """Make an HTTP request to the API with proper error handling"""
    url = f"{API_URL}{endpoint}"
    
    # Add auth header if needed
    request_headers = headers or {}
    if auth and AUTH_DATA["access_token"]:
        request_headers.update(get_auth_header())
    
    # Make the request
    if method.lower() == "get":
        response = requests.get(url, headers=request_headers)
    elif method.lower() == "post":
        response = requests.post(url, json=data, headers=request_headers)
    elif method.lower() == "put":
        response = requests.put(url, json=data, headers=request_headers)
    elif method.lower() == "patch":
        response = requests.patch(url, json=data, headers=request_headers)
    elif method.lower() == "delete":
        response = requests.delete(url, headers=request_headers)
    else:
        raise ValueError(f"Unsupported HTTP method: {method}")
    
    # Check status code
    if response.status_code != expected_status:
        print(f"Expected status {expected_status}, got {response.status_code}")
        print(f"Response: {response.text}")
    
    # Parse response data
    try:
        response_data = response.json() if response.text else {}
    except json.JSONDecodeError:
        response_data = {"text": response.text}
    
    return response_data, response.status_code


def is_valid_uuid(val: str) -> bool:
    """Check if a string is a valid UUID"""
    try:
        uuid.UUID(str(val))
        return True
    except ValueError:
        return False 