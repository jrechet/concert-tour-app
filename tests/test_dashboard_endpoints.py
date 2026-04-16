import pytest
from datetime import date, timedelta
from decimal import Decimal
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from src.models.venue import Venue
from src.models.concert import Concert


@pytest.fixture
def sample_data(db_session: Session):
    # Create venues
    venues = [
        Venue(
            name="Madison Square Garden",
            city="New York", 
            country="USA",
            capacity=20000,
            address="4 Pennsylvania Plaza, New York, NY 10001"
        ),
        Venue(
            name="O2 Arena",
            city="London",
            country="UK", 
            capacity=15000,
            address="Peninsula Square, London SE10 0DX"
        )
    ]
    
    for venue in venues:
        db_session.add(venue)
    db_session.commit()
    
    for venue in venues:
        db_session.refresh(venue)
    
    # Create concerts
    today = date.today()
    concerts = [
        Concert(
            date=today - timedelta(days=30),  # Past
            venue_id=venues[0].id,
            ticket_price=Decimal("100.00")
        ),
        Concert(
            date=today + timedelta(days=30),  # Future
            venue_id=venues[1].id,
            ticket_price=Decimal("85.00")
        )
    ]
    
    for concert in concerts:
        db_session.add(concert)
    db_session.commit()
    
    return venues, concerts


def test_get_tour_overview(client: TestClient, sample_data):
    response = client.get("/api/v1/dashboard/tour-overview")
    
    assert response.status_code == 200
    data = response.json()
    
    assert "tour_name" in data
    assert "start_date" in data
    assert "end_date" in data
    assert "progress_percentage" in data
    
    assert isinstance(data["progress_percentage"], (int, float))
    assert 0 <= data["progress_percentage"] <= 100


def test_get_tour_overview_empty_database(client: TestClient):
    response = client.get("/api/v1/dashboard/tour-overview")
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["tour_name"] == "Concert Tour"
    assert data["start_date"] is None
    assert data["end_date"] is None
    assert data["progress_percentage"] == 0.0


def test_get_dashboard_stats(client: TestClient, sample_data):
    response = client.get("/api/v1/dashboard/stats")
    
    assert response.status_code == 200
    data = response.json()
    
    assert "total_concerts" in data
    assert "unique_cities" in data
    assert "unique_countries" in data
    assert "total_capacity" in data
    assert "revenue_estimate" in data
    
    assert data["total_concerts"] == 2
    assert data["unique_cities"] == 2
    assert data["unique_countries"] == 2
    assert data["total_capacity"] == 35000  # 20000 + 15000
    
    # Revenue: (100 * 20000) + (85 * 15000) = 3,275,000
    expected_revenue = (100 * 20000) + (85 * 15000)
    assert data["revenue_estimate"] == expected_revenue


def test_get_dashboard_stats_empty_database(client: TestClient):
    response = client.get("/api/v1/dashboard/stats")
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["total_concerts"] == 0
    assert data["unique_cities"] == 0
    assert data["unique_countries"] == 0
    assert data["total_capacity"] == 0
    assert data["revenue_estimate"] == 0.0


def test_get_upcoming_concerts(client: TestClient, sample_data):
    response = client.get("/api/v1/dashboard/upcoming-concerts")
    
    assert response.status_code == 200
    data = response.json()
    
    assert "concerts" in data
    assert "total" in data
    assert "limit" in data
    assert "offset" in data
    assert "has_next" in data
    
    assert data["total"] == 1  # Only one future concert
    assert len(data["concerts"]) == 1
    assert data["limit"] == 10
    assert data["offset"] == 0
    assert data["has_next"] is False


def test_get_upcoming_concerts_with_pagination(client: TestClient, sample_data):
    response = client.get("/api/v1/dashboard/upcoming-concerts?limit=1&offset=0")
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["limit"] == 1
    assert data["offset"] == 0
    assert len(data["concerts"]) <= 1


def test_get_upcoming_concerts_pagination_validation(client: TestClient):
    # Test invalid limit
    response = client.get("/api/v1/dashboard/upcoming-concerts?limit=0")
    assert response.status_code == 422
    
    # Test invalid limit too high
    response = client.get("/api/v1/dashboard/upcoming-concerts?limit=101")
    assert response.status_code == 422
    
    # Test invalid offset
    response = client.get("/api/v1/dashboard/upcoming-concerts?offset=-1")
    assert response.status_code == 422


def test_upcoming_concerts_response_format(client: TestClient, sample_data):
    response = client.get("/api/v1/dashboard/upcoming-concerts")
    
    assert response.status_code == 200
    data = response.json()
    
    if data["concerts"]:
        concert = data["concerts"][0]
        required_fields = ["id", "date", "venue_name", "city", "country", "ticket_price"]
        
        for field in required_fields:
            assert field in concert
        
        # Verify data types
        assert isinstance(concert["id"], int)
        assert isinstance(concert["venue_name"], str)
        assert isinstance(concert["city"], str)
        assert isinstance(concert["country"], str)
        assert isinstance(concert["ticket_price"], str)  # Decimal serialized as string


def test_upcoming_concerts_empty_database(client: TestClient):
    response = client.get("/api/v1/dashboard/upcoming-concerts")
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["concerts"] == []
    assert data["total"] == 0
    assert data["has_next"] is False


def test_all_dashboard_endpoints_accessible(client: TestClient):
    """Test that all dashboard endpoints are accessible and return 200."""
    endpoints = [
        "/api/v1/dashboard/tour-overview",
        "/api/v1/dashboard/stats", 
        "/api/v1/dashboard/upcoming-concerts"
    ]
    
    for endpoint in endpoints:
        response = client.get(endpoint)
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/json"
