"""Comprehensive tests for venue REST API endpoints."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.main import app
from src.database import get_db
from src.models import Base, Venue

# Create in-memory SQLite database for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create tables
Base.metadata.create_all(bind=engine)


def override_get_db():
    """Override database dependency for testing."""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


@pytest.fixture
def db_session():
    """Create a fresh database session for each test."""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def sample_venues(db_session):
    """Create sample venues for testing."""
    venues = [
        Venue(
            name="Madison Square Garden",
            address="4 Pennsylvania Plaza",
            city="New York",
            country="USA",
            capacity=20000
        ),
        Venue(
            name="Wembley Stadium",
            address="Wembley",
            city="London",
            country="UK",
            capacity=90000
        ),
        Venue(
            name="Hollywood Bowl",
            address="2301 N Highland Ave",
            city="Los Angeles",
            country="USA",
            capacity=17500
        ),
        Venue(
            name="Sydney Opera House",
            address="Bennelong Point",
            city="Sydney",
            country="Australia",
            capacity=5679
        )
    ]
    
    for venue in venues:
        db_session.add(venue)
    db_session.commit()
    
    for venue in venues:
        db_session.refresh(venue)
    
    return venues


class TestListVenues:
    """Test GET /api/v1/venues endpoint."""

    def test_list_venues_empty(self):
        """Test listing venues when database is empty."""
        response = client.get("/api/v1/venues")
        assert response.status_code == 200
        assert response.json() == []

    def test_list_venues_default_pagination(self, sample_venues):
        """Test listing venues with default pagination."""
        response = client.get("/api/v1/venues")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 4
        assert data[0]["name"] == "Madison Square Garden"

    def test_list_venues_custom_pagination(self, sample_venues):
        """Test listing venues with custom pagination."""
        response = client.get("/api/v1/venues?limit=2&offset=1")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["name"] == "Wembley Stadium"

    def test_list_venues_pagination_validation(self):
        """Test pagination parameter validation."""
        # Test invalid limit
        response = client.get("/api/v1/venues?limit=0")
        assert response.status_code == 422

        response = client.get("/api/v1/venues?limit=1001")
        assert response.status_code == 422

        # Test invalid offset
        response = client.get("/api/v1/venues?offset=-1")
        assert response.status_code == 422

    def test_filter_by_city(self, sample_venues):
        """Test filtering venues by city."""
        response = client.get("/api/v1/venues?city=New York")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "Madison Square Garden"

        # Test case insensitive search
        response = client.get("/api/v1/venues?city=new york")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1

    def test_filter_by_country(self, sample_venues):
        """Test filtering venues by country."""
        response = client.get("/api/v1/venues?country=USA")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        venue_names = [venue["name"] for venue in data]
        assert "Madison Square Garden" in venue_names
        assert "Hollywood Bowl" in venue_names

    def test_search_by_name(self, sample_venues):
        """Test searching venues by name."""
        response = client.get("/api/v1/venues?search=Garden")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "Madison Square Garden"

        # Test partial match
        response = client.get("/api/v1/venues?search=Bowl")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "Hollywood Bowl"

    def test_combined_filters(self, sample_venues):
        """Test combining multiple filters."""
        response = client.get("/api/v1/venues?country=USA&city=Los Angeles")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "Hollywood Bowl"

        # Test filters with no results
        response = client.get("/api/v1/venues?country=USA&city=London")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 0


class TestGetVenue:
    """Test GET /api/v1/venues/{id} endpoint."""

    def test_get_venue_success(self, sample_venues):
        """Test getting a venue by ID."""
        venue_id = sample_venues[0].id
        response = client.get(f"/api/v1/venues/{venue_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == venue_id
        assert data["name"] == "Madison Square Garden"
        assert "created_at" in data
        assert "updated_at" in data

    def test_get_venue_not_found(self):
        """Test getting a non-existent venue."""
        response = client.get("/api/v1/venues/999")
        assert response.status_code == 404
        assert response.json()["detail"] == "Venue not found"

    def test_get_venue_invalid_id(self):
        """Test getting a venue with invalid ID format."""
        response = client.get("/api/v1/venues/invalid")
        assert response.status_code == 422


class TestCreateVenue:
    """Test POST /api/v1/venues endpoint."""

    def test_create_venue_success(self):
        """Test creating a venue successfully."""
        venue_data = {
            "name": "Test Venue",
            "address": "123 Test St",
            "city": "Test City",
            "country": "Test Country",
            "capacity": 5000
        }
        response = client.post("/api/v1/venues", json=venue_data)
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == venue_data["name"]
        assert data["address"] == venue_data["address"]
        assert data["city"] == venue_data["city"]
        assert data["country"] == venue_data["country"]
        assert data["capacity"] == venue_data["capacity"]
        assert "id" in data
        assert "created_at" in data
        assert "updated_at" in data

    def test_create_venue_missing_required_fields(self):
        """Test creating a venue with missing required fields."""
        venue_data = {
            "name": "Test Venue",
            "address": "123 Test St"
            # Missing city, country, capacity
        }
        response = client.post("/api/v1/venues", json=venue_data)
        assert response.status_code == 422

    def test_create_venue_invalid_data(self):
        """Test creating a venue with invalid data."""
        # Test negative capacity
        venue_data = {
            "name": "Test Venue",
            "address": "123 Test St",
            "city": "Test City",
            "country": "Test Country",
            "capacity": -100
        }
        response = client.post("/api/v1/venues", json=venue_data)
        assert response.status_code == 422

        # Test zero capacity
        venue_data["capacity"] = 0
        response = client.post("/api/v1/venues", json=venue_data)
        assert response.status_code == 422

        # Test empty string fields
        venue_data.update({
            "name": "",
            "capacity": 1000
        })
        response = client.post("/api/v1/venues", json=venue_data)
        assert response.status_code == 422

    def test_create_venue_field_length_validation(self):
        """Test field length validation."""
        # Test name too long (over 255 chars)
        venue_data = {
            "name": "x" * 256,
            "address": "123 Test St",
            "city": "Test City",
            "country": "Test Country",
            "capacity": 5000
        }
        response = client.post("/api/v1/venues", json=venue_data)
        assert response.status_code == 422


class TestUpdateVenue:
    """Test PUT /api/v1/venues/{id} endpoint."""

    def test_update_venue_success(self, sample_venues):
        """Test updating a venue successfully."""
        venue_id = sample_venues[0].id
        update_data = {
            "name": "Updated Garden",
            "capacity": 25000
        }
        response = client.put(f"/api/v1/venues/{venue_id}", json=update_data)
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == venue_id
        assert data["name"] == "Updated Garden"
        assert data["capacity"] == 25000
        # Other fields should remain unchanged
        assert data["address"] == "4 Pennsylvania Plaza"
        assert data["city"] == "New York"

    def test_update_venue_all_fields(self, sample_venues):
        """Test updating all venue fields."""
        venue_id = sample_venues[0].id
        update_data = {
            "name": "Completely New Venue",
            "address": "999 New Address",
            "city": "New City",
            "country": "New Country",
            "capacity": 30000
        }
        response = client.put(f"/api/v1/venues/{venue_id}", json=update_data)
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == update_data["name"]
        assert data["address"] == update_data["address"]
        assert data["city"] == update_data["city"]
        assert data["country"] == update_data["country"]
        assert data["capacity"] == update_data["capacity"]

    def test_update_venue_not_found(self):
        """Test updating a non-existent venue."""
        update_data = {"name": "Updated Name"}
        response = client.put("/api/v1/venues/999", json=update_data)
        assert response.status_code == 404
        assert response.json()["detail"] == "Venue not found"

    def test_update_venue_invalid_data(self, sample_venues):
        """Test updating a venue with invalid data."""
        venue_id = sample_venues[0].id
        
        # Test negative capacity
        update_data = {"capacity": -100}
        response = client.put(f"/api/v1/venues/{venue_id}", json=update_data)
        assert response.status_code == 422

        # Test empty string
        update_data = {"name": ""}
        response = client.put(f"/api/v1/venues/{venue_id}", json=update_data)
        assert response.status_code == 422

    def test_update_venue_empty_request(self, sample_venues):
        """Test updating a venue with empty request body."""
        venue_id = sample_venues[0].id
        response = client.put(f"/api/v1/venues/{venue_id}", json={})
        assert response.status_code == 200
        # Venue should remain unchanged
        data = response.json()
        assert data["name"] == "Madison Square Garden"


class TestDeleteVenue:
    """Test DELETE /api/v1/venues/{id} endpoint."""

    def test_delete_venue_success(self, sample_venues):
        """Test deleting a venue successfully."""
        venue_id = sample_venues[0].id
        response = client.delete(f"/api/v1/venues/{venue_id}")
        assert response.status_code == 204
        assert response.content == b""

        # Verify venue is deleted
        response = client.get(f"/api/v1/venues/{venue_id}")
        assert response.status_code == 404

    def test_delete_venue_not_found(self):
        """Test deleting a non-existent venue."""
        response = client.delete("/api/v1/venues/999")
        assert response.status_code == 404
        assert response.json()["detail"] == "Venue not found"

    def test_delete_venue_invalid_id(self):
        """Test deleting a venue with invalid ID format."""
        response = client.delete("/api/v1/venues/invalid")
        assert response.status_code == 422


class TestVenueEndpointsIntegration:
    """Integration tests for venue endpoints."""

    def test_crud_workflow(self):
        """Test complete CRUD workflow."""
        # Create venue
        venue_data = {
            "name": "Integration Test Venue",
            "address": "123 Integration St",
            "city": "Test City",
            "country": "Test Country",
            "capacity": 8000
        }
        create_response = client.post("/api/v1/venues", json=venue_data)
        assert create_response.status_code == 201
        created_venue = create_response.json()
        venue_id = created_venue["id"]

        # Read venue
        get_response = client.get(f"/api/v1/venues/{venue_id}")
        assert get_response.status_code == 200
        assert get_response.json()["name"] == venue_data["name"]

        # Update venue
        update_data = {"name": "Updated Integration Venue", "capacity": 10000}
        update_response = client.put(f"/api/v1/venues/{venue_id}", json=update_data)
        assert update_response.status_code == 200
        updated_venue = update_response.json()
        assert updated_venue["name"] == "Updated Integration Venue"
        assert updated_venue["capacity"] == 10000

        # Delete venue
        delete_response = client.delete(f"/api/v1/venues/{venue_id}")
        assert delete_response.status_code == 204

        # Verify deletion
        get_response = client.get(f"/api/v1/venues/{venue_id}")
        assert get_response.status_code == 404

    def test_list_after_operations(self):
        """Test listing venues after various operations."""
        # Create multiple venues
        venues_data = [
            {"name": "Venue A", "address": "Address A", "city": "City A", "country": "Country A", "capacity": 1000},
            {"name": "Venue B", "address": "Address B", "city": "City B", "country": "Country B", "capacity": 2000},
            {"name": "Venue C", "address": "Address C", "city": "City C", "country": "Country C", "capacity": 3000},
        ]
        
        created_venues = []
        for venue_data in venues_data:
            response = client.post("/api/v1/venues", json=venue_data)
            assert response.status_code == 201
            created_venues.append(response.json())

        # List all venues
        list_response = client.get("/api/v1/venues")
        assert list_response.status_code == 200
        venues_list = list_response.json()
        assert len(venues_list) >= 3

        # Test search functionality
        search_response = client.get("/api/v1/venues?search=Venue A")
        assert search_response.status_code == 200
        search_results = search_response.json()
        assert len(search_results) == 1
        assert search_results[0]["name"] == "Venue A"

        # Clean up
        for venue in created_venues:
            client.delete(f"/api/v1/venues/{venue['id']}")
