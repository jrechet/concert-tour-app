import pytest
from datetime import date


def test_create_tour(client, sample_tour_data):
    """Test creating a new tour."""
    response = client.post("/api/v1/tours/", json=sample_tour_data)
    
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == sample_tour_data["name"]
    assert data["artist"] == sample_tour_data["artist"]
    assert data["start_date"] == sample_tour_data["start_date"]
    assert data["end_date"] == sample_tour_data["end_date"]
    assert data["description"] == sample_tour_data["description"]
    assert "id" in data


def test_create_tour_invalid_data(client):
    """Test creating a tour with invalid data."""
    invalid_data = {
        "name": "",  # Empty name
        "artist": "Test Artist",
        "start_date": "invalid-date",  # Invalid date format
        "end_date": "2024-12-31"
    }
    
    response = client.post("/api/v1/tours/", json=invalid_data)
    assert response.status_code == 422


def test_get_tours(client, created_tour):
    """Test getting all tours."""
    response = client.get("/api/v1/tours/")
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["id"] == created_tour["id"]


def test_get_tour_by_id(client, created_tour):
    """Test getting a specific tour by ID."""
    tour_id = created_tour["id"]
    response = client.get(f"/api/v1/tours/{tour_id}")
    
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == tour_id
    assert data["name"] == created_tour["name"]


def test_get_tour_not_found(client):
    """Test getting a tour that doesn't exist."""
    response = client.get("/api/v1/tours/999")
    
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_update_tour(client, created_tour):
    """Test updating an existing tour."""
    tour_id = created_tour["id"]
    update_data = {
        "name": "Updated Tour Name",
        "description": "Updated description"
    }
    
    response = client.put(f"/api/v1/tours/{tour_id}", json=update_data)
    
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == update_data["name"]
    assert data["description"] == update_data["description"]
    assert data["artist"] == created_tour["artist"]  # Unchanged


def test_update_tour_not_found(client):
    """Test updating a tour that doesn't exist."""
    update_data = {"name": "Updated Name"}
    response = client.put("/api/v1/tours/999", json=update_data)
    
    assert response.status_code == 404


def test_delete_tour(client, created_tour):
    """Test deleting a tour."""
    tour_id = created_tour["id"]
    response = client.delete(f"/api/v1/tours/{tour_id}")
    
    assert response.status_code == 204
    
    # Verify tour is deleted
    get_response = client.get(f"/api/v1/tours/{tour_id}")
    assert get_response.status_code == 404


def test_delete_tour_not_found(client):
    """Test deleting a tour that doesn't exist."""
    response = client.delete("/api/v1/tours/999")
    
    assert response.status_code == 404


def test_tour_date_validation(client):
    """Test that end_date must be after start_date."""
    invalid_data = {
        "name": "Test Tour",
        "artist": "Test Artist",
        "start_date": "2024-12-31",
        "end_date": "2024-01-01",  # End date before start date
        "description": "Test description"
    }
    
    response = client.post("/api/v1/tours/", json=invalid_data)
    assert response.status_code == 422
