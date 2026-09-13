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


client = TestClient(app)


@pytest.fixture(autouse=True)
def clean_database():
    """Clean database before each test.

    Scopes the `get_db` override to this module's tests only: setting it at
    import time would leak into every other test file sharing the same
    `app` singleton (dependency_overrides is a plain mutable dict), since
    pytest imports all test modules during collection before any test runs.
    Restoring the prior override on teardown keeps that leakage from
    outliving this module's tests.
    """
    previous_override = app.dependency_overrides.get(get_db)
    app.dependency_overrides[get_db] = override_get_db
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    if previous_override is None:
        app.dependency_overrides.pop(get_db, None)
    else:
        app.dependency_overrides[get_db] = previous_override


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
    assert data["name"] == "World Tour 2024"
    assert data["artist"] == "Test Artist"
    assert "id" in data


def test_get_tours_empty():
    """Test getting tours when none exist."""
    response = client.get("/api/v1/tours/")
    assert response.status_code == 200
    assert response.json() == []


def test_get_tours_with_pagination():
    """Test getting tours with pagination."""
    for i in range(5):
        tour_data = {
            "name": f"Tour {i}",
            "artist": f"Artist {i}",
            "start_date": "2024-01-01",
            "end_date": "2024-12-31",
            "status": "planned"
        }
        client.post("/api/v1/tours/", json=tour_data)

    response = client.get("/api/v1/tours/?skip=2&limit=2")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2


def test_get_tour_by_id():
    """Test getting a specific tour by ID."""
    tour_data = {
        "name": "Test Tour",
        "artist": "Test Artist",
        "start_date": "2024-01-01",
        "end_date": "2024-12-31",
        "status": "planned"
    }
    create_response = client.post("/api/v1/tours/", json=tour_data)
    tour_id = create_response.json()["id"]

    response = client.get(f"/api/v1/tours/{tour_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == tour_id
    assert data["name"] == "Test Tour"


def test_get_tour_not_found():
    """Test getting a tour that doesn't exist."""
    response = client.get("/api/v1/tours/999")
    assert response.status_code == 404


def test_update_tour():
    """Test updating a tour."""
    tour_data = {
        "name": "Original Tour",
        "artist": "Original Artist",
        "start_date": "2024-01-01",
        "end_date": "2024-12-31",
        "status": "planned"
    }
    create_response = client.post("/api/v1/tours/", json=tour_data)
    tour_id = create_response.json()["id"]

    update_data = {
        "name": "Updated Tour",
        "status": "active"
    }
    response = client.put(f"/api/v1/tours/{tour_id}", json=update_data)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Tour"
    assert data["status"] == "active"
    assert data["artist"] == "Original Artist"


def test_update_tour_not_found():
    """Test updating a tour that doesn't exist."""
    update_data = {"name": "Updated Tour"}
    response = client.put("/api/v1/tours/999", json=update_data)
    assert response.status_code == 404


def test_delete_tour():
    """Test deleting a tour."""
    tour_data = {
        "name": "Tour to Delete",
        "artist": "Test Artist",
        "start_date": "2024-01-01",
        "end_date": "2024-12-31",
        "status": "planned"
    }
    create_response = client.post("/api/v1/tours/", json=tour_data)
    tour_id = create_response.json()["id"]

    response = client.delete(f"/api/v1/tours/{tour_id}")
    assert response.status_code == 204

    get_response = client.get(f"/api/v1/tours/{tour_id}")
    assert get_response.status_code == 404


def test_delete_tour_not_found():
    """Test deleting a tour that doesn't exist."""
    response = client.delete("/api/v1/tours/999")
    assert response.status_code == 404


def test_create_tour_validation_error():
    """Test creating a tour with invalid data."""
    invalid_tour_data = {
        "name": "",
        "artist": "Test Artist",
        "start_date": "2024-12-01",
        "end_date": "2024-06-01",
        "status": "planned"
    }
    response = client.post("/api/v1/tours/", json=invalid_tour_data)
    assert response.status_code == 422
