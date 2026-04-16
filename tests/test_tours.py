import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta
from main import app
from database import get_db
from models import Base

# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_tours.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


@pytest.fixture(scope="function")
def setup_database():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


def test_create_tour(setup_database):
    tour_data = {
        "name": "World Tour 2024",
        "description": "Amazing world tour",
        "start_date": "2024-06-01T10:00:00",
        "end_date": "2024-12-01T22:00:00",
        "status": "planning"
    }
    
    response = client.post("/api/v1/tours", json=tour_data)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == tour_data["name"]
    assert data["description"] == tour_data["description"]
    assert data["status"] == tour_data["status"]
    assert "id" in data
    assert "created_at" in data


def test_get_tours_empty(setup_database):
    response = client.get("/api/v1/tours")
    assert response.status_code == 200
    assert response.json() == []


def test_get_tours_with_pagination(setup_database):
    # Create multiple tours
    for i in range(5):
        tour_data = {
            "name": f"Tour {i}",
            "description": f"Description {i}",
            "start_date": "2024-06-01T10:00:00",
            "end_date": "2024-12-01T22:00:00",
            "status": "planning"
        }
        client.post("/api/v1/tours", json=tour_data)
    
    # Test pagination
    response = client.get("/api/v1/tours?limit=3&offset=0")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3
    
    response = client.get("/api/v1/tours?limit=3&offset=3")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2


def test_get_tour_by_id(setup_database):
    # Create a tour
    tour_data = {
        "name": "Test Tour",
        "description": "Test description",
        "start_date": "2024-06-01T10:00:00",
        "end_date": "2024-12-01T22:00:00",
        "status": "planning"
    }
    
    create_response = client.post("/api/v1/tours", json=tour_data)
    tour_id = create_response.json()["id"]
    
    # Get the tour by ID
    response = client.get(f"/api/v1/tours/{tour_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == tour_data["name"]
    assert data["id"] == tour_id


def test_get_tour_not_found(setup_database):
    response = client.get("/api/v1/tours/999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Tour not found"


def test_create_tour_invalid_data(setup_database):
    # Missing required fields
    tour_data = {
        "name": "",  # Empty name
        "start_date": "2024-06-01T10:00:00",
        "end_date": "2024-12-01T22:00:00"
    }
    
    response = client.post("/api/v1/tours", json=tour_data)
    assert response.status_code == 422  # Validation error
