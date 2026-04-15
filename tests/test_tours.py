"""Tests for tour CRUD endpoints."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import date

from src.main import app
from src.database import get_db
from src.models import Base

# Create test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create tables
Base.metadata.create_all(bind=engine)


def override_get_db():
    """Override database dependency for testing."""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


@pytest.fixture(autouse=True)
def clean_database():
    """Clean database before each test."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


def test_create_tour():
    """Test creating a new tour."""
    tour_data = {
        "name": "World Tour 2024",
        "artist": "Test Artist",
        "description": "Amazing world tour",
        "start_date": "2024-06-01",
        "end_date": "2024-12-01",
        "status": "planned"
    }
    
    response = client.post("/api/v1/tours/", json=tour_data)
    
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == tour_data["name"]
    assert data["artist"] == tour_data["artist"]
    assert data["id"] is not None


def test_get_tours_empty():
    """Test retrieving tours when none exist."""
    response = client.get("/api/v1/tours/")
    
    assert response.status_code == 200
    assert response.json() == []


def test_get_tours_with_pagination():
    """Test retrieving tours with pagination."""
    # Create multiple tours
    for i in range(5):
        tour_data = {
            "name": f"Tour {i}",
            "artist": f"Artist {i}",
            "description": f"Description {i}",
            "start_date": "2024-06-01",
            "end_date": "2024-12-01",
            "status": "planned"
        }
        client.post("/api/v1/tours/", json=tour_data)
    
    # Test pagination
    response = client.get("/api/v1/tours/?skip=2&limit=2")
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2


def test_get_tour_by_id():
    """Test retrieving a specific tour by ID."""
    # Create a tour first
    tour_data = {
        "name": "Specific Tour",
        "artist": "Specific Artist",
        "description": "Specific description",
        "start_date": "2024-06-01",
        "end_date": "2024-12-01",
        "status": "planned"
    }
    
    create_response = client.post("/api/v1/tours/", json=tour_data)
    tour_id = create_response.json()["id"]
    
    # Retrieve the tour
    response = client.get(f"/api/v1/tours/{tour_id}")
    
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == tour_data["name"]
    assert data["id"] == tour_id


def test_get_tour_not_found():
    """Test retrieving a non-existent tour returns 404."""
    response = client.get("/api/v1/tours/999")
    
    assert response.status_code == 404
    assert response.json()["detail"] == "Tour not found"


def test_update_tour():
    """Test updating an existing tour."""
    # Create a tour first
    tour_data = {
        "name": "Original Tour",
        "artist": "Original Artist",
        "description": "Original description",
        "start_date": "2024-06-01",
        "end_date": "2024-12-01",
        "status": "planned"
    }
    
    create_response = client.post("/api/v1/tours/", json=tour_data)
    tour_id = create_response.json()["id"]
    
    # Update the tour
    update_data = {
        "name": "Updated Tour",
        "status": "active"
    }
    
    response = client.put(f"/api/v1/tours/{tour_id}", json=update_data)
    
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Tour"
    assert data["status"] == "active"
    assert data["artist"] == "Original Artist"  # Unchanged field


def test_update_tour_not_found():
    """Test updating a non-existent tour returns 404."""
    update_data = {"name": "Updated Tour"}
    
    response = client.put("/api/v1/tours/999", json=update_data)
    
    assert response.status_code == 404
    assert response.json()["detail"] == "Tour not found"


def test_delete_tour():
    """Test deleting a tour."""
    # Create a tour first
    tour_data = {
        "name": "Tour to Delete",
        "artist": "Artist",
        "description": "Description",
        "start_date": "2024-06-01",
        "end_date": "2024-12-01",
        "status": "planned"
    }
    
    create_response = client.post("/api/v1/tours/", json=tour_data)
    tour_id = create_response.json()["id"]
    
    # Delete the tour
    response = client.delete(f"/api/v1/tours/{tour_id}")
    
    assert response.status_code == 204
    
    # Verify the tour is deleted
    get_response = client.get(f"/api/v1/tours/{tour_id}")
    assert get_response.status_code == 404


def test_delete_tour_not_found():
    """Test deleting a non-existent tour returns 404."""
    response = client.delete("/api/v1/tours/999")
    
    assert response.status_code == 404
    assert response.json()["detail"] == "Tour not found"


def test_create_tour_validation_error():
    """Test creating a tour with invalid data."""
    invalid_tour_data = {
        "name": "",  # Empty name should fail validation
        "artist": "Artist",
        "start_date": "invalid-date",  # Invalid date format
        "status": "invalid_status"  # Invalid status
    }
    
    response = client.post("/api/v1/tours/", json=invalid_tour_data)
    
    assert response.status_code == 422  # Validation error
