import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta
from main import app
from database import get_db
from models import Base

# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_concerts.db"
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


@pytest.fixture
def create_tour(setup_database):
    tour_data = {
        "name": "Test Tour",
        "description": "Test description",
        "start_date": "2024-06-01T10:00:00",
        "end_date": "2024-12-01T22:00:00",
        "status": "planning"
    }
    response = client.post("/api/v1/tours", json=tour_data)
    return response.json()["id"]


def test_create_concert(create_tour):
    tour_id = create_tour
    concert_data = {
        "tour_id": tour_id,
        "venue_name": "Madison Square Garden",
        "venue_address": "4 Pennsylvania Plaza",
        "venue_city": "New York",
        "venue_country": "USA",
        "venue_capacity": 20000,
        "concert_date": "2024-07-15T20:00:00",
        "ticket_price": 75.00,
        "status": "scheduled"
    }
    
    response = client.post("/api/v1/concerts", json=concert_data)
    assert response.status_code == 201
    data = response.json()
    assert data["venue_name"] == concert_data["venue_name"]
    assert data["tour_id"] == tour_id
    assert data["venue_capacity"] == concert_data["venue_capacity"]
    assert data["ticket_price"] == concert_data["ticket_price"]
    assert "id" in data


def test_create_concert_invalid_tour(setup_database):
    concert_data = {
        "tour_id": 999,  # Non-existent tour
        "venue_name": "Test Venue",
        "venue_address": "Test Address",
        "venue_city": "Test City",
        "venue_country": "Test Country",
        "venue_capacity": 1000,
        "concert_date": "2024-07-15T20:00:00",
        "ticket_price": 50.00,
        "status": "scheduled"
    }
    
    response = client.post("/api/v1/concerts", json=concert_data)
    assert response.status_code == 400
    assert response.json()["detail"] == "Tour not found"


def test_get_concerts_empty(setup_database):
    response = client.get("/api/v1/concerts")
    assert response.status_code == 200
    assert response.json() == []


def test_get_concerts_with_pagination(create_tour):
    tour_id = create_tour
    
    # Create multiple concerts
    for i in range(5):
        concert_data = {
            "tour_id": tour_id,
            "venue_name": f"Venue {i}",
            "venue_address": f"Address {i}",
            "venue_city": f"City {i}",
            "venue_country": "USA",
            "venue_capacity": 1000 + i,
            "concert_date": "2024-07-15T20:00:00",
            "ticket_price": 50.00 + i,
            "status": "scheduled"
        }
        client.post("/api/v1/concerts", json=concert_data)
    
    # Test pagination
    response = client.get("/api/v1/concerts?limit=3&offset=0")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3
    
    response = client.get("/api/v1/concerts?limit=3&offset=3")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2


def test_get_concert_by_id(create_tour):
    tour_id = create_tour
    concert_data = {
        "tour_id": tour_id,
        "venue_name": "Test Venue",
        "venue_address": "Test Address",
        "venue_city": "Test City",
        "venue_country": "Test Country",
        "venue_capacity": 5000,
        "concert_date": "2024-07-15T20:00:00",
        "ticket_price": 60.00,
        "status": "scheduled"
    }
    
    create_response = client.post("/api/v1/concerts", json=concert_data)
    concert_id = create_response.json()["id"]
    
    # Get the concert by ID
    response = client.get(f"/api/v1/concerts/{concert_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["venue_name"] == concert_data["venue_name"]
    assert data["id"] == concert_id
    assert data["tour_id"] == tour_id


def test_get_concert_not_found(setup_database):
    response = client.get("/api/v1/concerts/999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Concert not found"


def test_create_concert_invalid_data(create_tour):
    tour_id = create_tour
    
    # Invalid venue capacity (negative)
    concert_data = {
        "tour_id": tour_id,
        "venue_name": "Test Venue",
        "venue_address": "Test Address",
        "venue_city": "Test City",
        "venue_country": "Test Country",
        "venue_capacity": -100,  # Invalid
        "concert_date": "2024-07-15T20:00:00",
        "ticket_price": 60.00,
        "status": "scheduled"
    }
    
    response = client.post("/api/v1/concerts", json=concert_data)
    assert response.status_code == 422  # Validation error
