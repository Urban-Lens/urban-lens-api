"""Tests for location operations"""
import sys
import os
from pathlib import Path
import pytest
import requests
import time
import uuid

# Add the parent directory to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

from tests.config import TEST_USER, TEST_USER_2, AUTH_DATA
from tests.utils import make_request, is_valid_uuid
from tests.test_auth import test_login

# Test data for locations
TEST_LOCATION = {
    "address": "123 Test Street, Test City",
    "latitude": 40.7128,
    "longitude": -74.0060,
    "description": "Test location for API testing",
    "tags": ["test", "api", "location"],
    "input_stream_url": "https://example.com/input/test",
    "output_stream_url": "https://example.com/output/test",
    "thumbnail": "https://example.com/thumbnails/test.jpg"
}

TEST_LOCATION_2 = {
    "address": "456 Sample Avenue, Sample Town",
    "latitude": 37.7749,
    "longitude": -122.4194,
    "description": "Another test location",
    "tags": ["sample", "api", "testing"],
    "input_stream_url": "https://example.com/input/sample",
    "output_stream_url": "https://example.com/output/sample",
    "thumbnail": "https://example.com/thumbnails/sample.jpg"
}

# Store location data during tests
LOCATION_DATA = {
    "location_id": None,
    "location_2_id": None
}

def test_create_location():
    """Test creating a new location"""
    # First ensure we have a logged-in user
    if not AUTH_DATA["access_token"]:
        test_login()
    
    # Create a new location
    response_data, status_code = make_request(
        "post", 
        "/locations/", 
        data=TEST_LOCATION, 
        auth=True,
        expected_status=201
    )
    
    assert status_code == 201, f"Expected status 201, got {status_code}"
    assert "id" in response_data, "Location ID not found in response"
    assert "address" in response_data, "Address not found in response"
    assert "latitude" in response_data, "Latitude not found in response"
    assert "longitude" in response_data, "Longitude not found in response"
    assert "user_id" in response_data, "User ID not found in response"
    
    # Validate data
    assert response_data["address"] == TEST_LOCATION["address"]
    assert response_data["latitude"] == TEST_LOCATION["latitude"]
    assert response_data["longitude"] == TEST_LOCATION["longitude"]
    assert response_data["description"] == TEST_LOCATION["description"]
    assert response_data["tags"] == TEST_LOCATION["tags"]
    assert response_data["input_stream_url"] == TEST_LOCATION["input_stream_url"]
    assert response_data["output_stream_url"] == TEST_LOCATION["output_stream_url"]
    assert response_data["thumbnail"] == TEST_LOCATION["thumbnail"]
    assert is_valid_uuid(response_data["id"]), "Invalid location ID format"
    assert is_valid_uuid(response_data["user_id"]), "Invalid user ID format"
    
    # Store the location ID for future tests
    LOCATION_DATA["location_id"] = response_data["id"]
    
    print(f"Successfully created location with ID: {LOCATION_DATA['location_id']}")
    return response_data

def test_get_location():
    """Test getting a specific location by ID"""
    # First ensure we have a created location
    if not LOCATION_DATA["location_id"]:
        test_create_location()
    
    # Get the location
    response_data, status_code = make_request(
        "get", 
        f"/locations/{LOCATION_DATA['location_id']}"
    )
    
    assert status_code == 200, f"Expected status 200, got {status_code}"
    assert "id" in response_data, "Location ID not found in response"
    assert "address" in response_data, "Address not found in response"
    
    # Validate data
    assert response_data["id"] == LOCATION_DATA["location_id"]
    assert response_data["address"] == TEST_LOCATION["address"]
    assert response_data["latitude"] == TEST_LOCATION["latitude"]
    assert response_data["longitude"] == TEST_LOCATION["longitude"]
    
    print(f"Successfully retrieved location with ID: {LOCATION_DATA['location_id']}")
    return response_data

def test_get_all_locations():
    """Test getting all locations"""
    # First ensure we have a created location
    if not LOCATION_DATA["location_id"]:
        test_create_location()
    
    # Get all locations
    response_data, status_code = make_request(
        "get", 
        "/locations/"
    )
    
    assert status_code == 200, f"Expected status 200, got {status_code}"
    assert isinstance(response_data, list), "Expected a list of locations"
    assert len(response_data) > 0, "Expected at least one location"
    
    # Check if our test location is in the list
    location_found = False
    for location in response_data:
        if location["id"] == LOCATION_DATA["location_id"]:
            location_found = True
            break
    
    assert location_found, "Test location not found in the list of all locations"
    
    print(f"Successfully retrieved all locations (count: {len(response_data)})")
    return response_data

def test_get_my_locations():
    """Test getting locations for the current user"""
    # First ensure we have a logged-in user and created location
    if not AUTH_DATA["access_token"]:
        test_login()
    if not LOCATION_DATA["location_id"]:
        test_create_location()
    
    # Get my locations
    response_data, status_code = make_request(
        "get", 
        "/locations/me/", 
        auth=True
    )
    
    assert status_code == 200, f"Expected status 200, got {status_code}"
    assert isinstance(response_data, list), "Expected a list of locations"
    assert len(response_data) > 0, "Expected at least one location"
    
    # Check if our test location is in the list
    location_found = False
    for location in response_data:
        if location["id"] == LOCATION_DATA["location_id"]:
            location_found = True
            break
    
    assert location_found, "Test location not found in the list of my locations"
    
    print(f"Successfully retrieved my locations (count: {len(response_data)})")
    return response_data

def test_update_location():
    """Test updating a location"""
    # First ensure we have a created location
    if not LOCATION_DATA["location_id"]:
        test_create_location()
    
    # Update data
    update_data = {
        "address": "Updated Test Address",
        "description": "Updated description for testing"
    }
    
    # Update the location
    response_data, status_code = make_request(
        "put", 
        f"/locations/{LOCATION_DATA['location_id']}", 
        data=update_data, 
        auth=True
    )
    
    assert status_code == 200, f"Expected status 200, got {status_code}"
    assert "id" in response_data, "Location ID not found in response"
    assert "address" in response_data, "Address not found in response"
    
    # Validate data
    assert response_data["id"] == LOCATION_DATA["location_id"]
    assert response_data["address"] == update_data["address"]
    assert response_data["description"] == update_data["description"]
    assert response_data["latitude"] == TEST_LOCATION["latitude"]  # Unchanged
    assert response_data["longitude"] == TEST_LOCATION["longitude"]  # Unchanged
    
    print(f"Successfully updated location with ID: {LOCATION_DATA['location_id']}")
    return response_data

def test_create_second_location():
    """Test creating a second location for the same user"""
    # First ensure we have a logged-in user
    if not AUTH_DATA["access_token"]:
        test_login()
    
    # Create a second location
    response_data, status_code = make_request(
        "post", 
        "/locations/", 
        data=TEST_LOCATION_2, 
        auth=True,
        expected_status=201
    )
    
    assert status_code == 201, f"Expected status 201, got {status_code}"
    assert "id" in response_data, "Location ID not found in response"
    
    # Store the second location ID
    LOCATION_DATA["location_2_id"] = response_data["id"]
    
    print(f"Successfully created second location with ID: {LOCATION_DATA['location_2_id']}")
    return response_data

def test_delete_location():
    """Test deleting a location"""
    # First ensure we have a second location to delete
    # (we'll keep the first one for other tests)
    if not LOCATION_DATA["location_2_id"]:
        test_create_second_location()
    
    # Delete the second location
    response_data, status_code = make_request(
        "delete", 
        f"/locations/{LOCATION_DATA['location_2_id']}", 
        auth=True,
        expected_status=204
    )
    
    assert status_code == 204, f"Expected status 204, got {status_code}"
    
    # Verify the location is deleted by trying to get it
    response_data, status_code = make_request(
        "get", 
        f"/locations/{LOCATION_DATA['location_2_id']}",
        expected_status=404
    )
    
    assert status_code == 404, f"Expected status 404, got {status_code}"
    
    print(f"Successfully deleted location with ID: {LOCATION_DATA['location_2_id']}")
    
    # Clear the second location ID
    LOCATION_DATA["location_2_id"] = None

def run_location_tests():
    """Run all location tests in sequence"""
    # Start with a clean slate
    LOCATION_DATA["location_id"] = None
    LOCATION_DATA["location_2_id"] = None
    
    # Run the tests
    try:
        test_login()  # Make sure we're logged in
        test_create_location()
        test_get_location()
        test_get_all_locations()
        test_get_my_locations()
        test_update_location()
        test_create_second_location()
        test_delete_location()
        print("All location tests completed successfully!")
    except Exception as e:
        print(f"Error in location tests: {e}")
        import traceback
        print(traceback.format_exc())


if __name__ == "__main__":
    # Run all tests
    run_location_tests() 