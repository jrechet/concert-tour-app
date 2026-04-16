import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.main import app
from src.database import get_db
from src.models import Base, Tour, Venue, Concert
from datetime import date, time


# Create test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="function")
def test_db():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    
    # Create test data
    tour = Tour(
        name="World Tour 2024",
        start_date=date(2024, 1, 1),
        end_date=date(2024, 12, 31),
        is_active=True
    )
    db.add(tour)
    db.commit()
    
    venue1 = Venue(
        name="Madison Square Garden",
        city="New York",
        country="USA",
        capacity=20000
    )
    venue2 = Venue(
        name="Wembley Stadium",
        city="London",
        country="UK",
        capacity=90000
    )
    db.add_all([venue1, venue2])
    db.commit()
    
    concert1 = Concert(
        tour_id=tour.id,
        venue_id=venue1.id,
        date=date(2024, 6, 15),
        time=time(20, 0)
    )
    concert2 = Concert(
        tour_id=tour.id,
        venue_id=venue2.id,
        date=date(2024, 7, 20),
        time=time(19, 30)
    )
    db.add_all([concert1, concert2])
    db.commit()
    
    yield db
    
    db.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client():
    return TestClient(app)


def test_get_current_tour(client, test_db):
    """Test getting current tour overview."""
    response = client.get("/api/v1/tours/current")
    
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "World Tour 2024"
    assert data["start_date"] == "2024-01-01"
    assert data["end_date"] == "2024-12-31"
    assert "progress_percentage" in data


def test_get_current_tour_not_found(client):
    """Test getting current tour when none exists."""
    Base.metadata.create_all(bind=engine)
    response = client.get("/api/v1/tours/current")
    
    assert response.status_code == 404
    assert response.json()["detail"] == "No active tour found"


def test_get_tour_concerts(client, test_db):
    """Test getting upcoming concerts for a tour."""
    response = client.get("/api/v1/tours/1/concerts")
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    
    # Check first concert
    concert = data[0]
    assert concert["venue_name"] == "Madison Square Garden"
    assert concert["city"] == "New York"
    assert concert["country"] == "USA"
    assert concert["capacity"] == 20000
    assert concert["date"] == "2024-06-15"


def test_get_tour_concerts_invalid_tour(client, test_db):
    """Test getting concerts for non-existent tour."""
    response = client.get("/api/v1/tours/999/concerts")
    
    assert response.status_code == 404
    assert response.json()["detail"] == "Tour not found"


def test_get_tour_stats(client, test_db):
    """Test getting tour statistics."""
    response = client.get("/api/v1/tours/1/stats")
    
    assert response.status_code == 200
    data = response.json()
    assert data["total_concerts"] == 2
    assert data["unique_cities"] == 2
    assert data["unique_countries"] == 2
    assert data["total_capacity"] == 110000  # 20000 + 90000
    assert data["revenue_estimate"] == 8800000.0  # 110000 * 100 * 0.8


def test_get_tour_stats_invalid_tour(client, test_db):
    """Test getting stats for non-existent tour."""
    response = client.get("/api/v1/tours/999/stats")
    
    assert response.status_code == 404
    assert response.json()["detail"] == "Tour not found"


def test_response_format_current_tour(client, test_db):
    """Test that current tour endpoint returns proper JSON format."""
    response = client.get("/api/v1/tours/current")
    
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/json"
    
    data = response.json()
    required_fields = ["id", "name", "start_date", "end_date", "progress_percentage"]
    for field in required_fields:
        assert field in data


def test_response_format_concerts(client, test_db):
    """Test that concerts endpoint returns proper JSON format."""
    response = client.get("/api/v1/tours/1/concerts")
    
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/json"
    
    data = response.json()
    assert isinstance(data, list)
    if data:  # If there are concerts
        concert = data[0]
        required_fields = ["id", "date", "venue_name", "city", "country", "capacity"]
        for field in required_fields:
            assert field in concert


def test_response_format_stats(client, test_db):
    """Test that stats endpoint returns proper JSON format."""
    response = client.get("/api/v1/tours/1/stats")
    
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/json"
    
    data = response.json()
    required_fields = ["total_concerts", "unique_cities", "unique_countries", "total_capacity", "revenue_estimate"]
    for field in required_fields:
        assert field in data
