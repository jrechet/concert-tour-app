import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.main import app
from src.database import Base, get_db
from src.models import Venue

# Create in-memory SQLite database for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_database():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def sample_venue_data():
    return {
        "name": "Madison Square Garden",
        "city": "New York",
        "address": "4 Pennsylvania Plaza, New York, NY 10001",
        "capacity": 20000
    }


@pytest.fixture
def create_test_venue(sample_venue_data):
    response = client.post("/api/v1/venues/", json=sample_venue_data)
    return response.json()


class TestCreateVenue:
    def test_create_venue_success(self, sample_venue_data):
        response = client.post("/api/v1/venues/", json=sample_venue_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == sample_venue_data["name"]
        assert data["city"] == sample_venue_data["city"]
        assert data["address"] == sample_venue_data["address"]
        assert data["capacity"] == sample_venue_data["capacity"]
        assert "id" in data
        assert "created_at" in data
        assert "updated_at" in data

    def test_create_venue_invalid_data(self):
        invalid_data = {
            "name": "",  # Empty name
            "city": "New York",
            "address": "123 Main St",
            "capacity": 0  # Invalid capacity
        }
        response = client.post("/api/v1/venues/", json=invalid_data)
        assert response.status_code == 422

    def test_create_venue_missing_fields(self):
        incomplete_data = {
            "name": "Test Venue"
            # Missing required fields
        }
        response = client.post("/api/v1/venues/", json=incomplete_data)
        assert response.status_code == 422


class TestGetVenue:
    def test_get_venue_success(self, create_test_venue):
        venue_id = create_test_venue["id"]
        response = client.get(f"/api/v1/venues/{venue_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == venue_id
        assert data["name"] == create_test_venue["name"]

    def test_get_venue_not_found(self):
        response = client.get("/api/v1/venues/999")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]


class TestUpdateVenue:
    def test_update_venue_success(self, create_test_venue):
        venue_id = create_test_venue["id"]
        update_data = {
            "name": "Updated Venue Name",
            "capacity": 25000
        }
        
        response = client.put(f"/api/v1/venues/{venue_id}", json=update_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == update_data["name"]
        assert data["capacity"] == update_data["capacity"]
        assert data["city"] == create_test_venue["city"]  # Unchanged field

    def test_update_venue_not_found(self):
        update_data = {"name": "Updated Name"}
        response = client.put("/api/v1/venues/999", json=update_data)
        assert response.status_code == 404

    def test_update_venue_invalid_data(self, create_test_venue):
        venue_id = create_test_venue["id"]
        invalid_data = {"capacity": -1}
        
        response = client.put(f"/api/v1/venues/{venue_id}", json=invalid_data)
        assert response.status_code == 422


class TestDeleteVenue:
    def test_delete_venue_success(self, create_test_venue):
        venue_id = create_test_venue["id"]
        response = client.delete(f"/api/v1/venues/{venue_id}")
        
        assert response.status_code == 204
        
        # Verify venue is deleted
        get_response = client.get(f"/api/v1/venues/{venue_id}")
        assert get_response.status_code == 404

    def test_delete_venue_not_found(self):
        response = client.delete("/api/v1/venues/999")
        assert response.status_code == 404


class TestListVenues:
    def test_list_venues_empty(self):
        response = client.get("/api/v1/venues/")
        
        assert response.status_code == 200
        data = response.json()
        assert data["venues"] == []
        assert data["total"] == 0
        assert data["page"] == 1
        assert data["total_pages"] == 1

    def test_list_venues_with_data(self):
        # Create multiple venues
        venues_data = [
            {"name": "Venue 1", "city": "New York", "address": "Address 1", "capacity": 1000},
            {"name": "Venue 2", "city": "Boston", "address": "Address 2", "capacity": 2000},
            {"name": "Venue 3", "city": "New York", "address": "Address 3", "capacity": 3000},
        ]
        
        for venue_data in venues_data:
            client.post("/api/v1/venues/", json=venue_data)
        
        response = client.get("/api/v1/venues/")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["venues"]) == 3
        assert data["total"] == 3

    def test_list_venues_search_filter(self):
        # Create venues
        venues_data = [
            {"name": "Madison Square Garden", "city": "New York", "address": "Address 1", "capacity": 1000},
            {"name": "Boston Arena", "city": "Boston", "address": "Address 2", "capacity": 2000},
        ]
        
        for venue_data in venues_data:
            client.post("/api/v1/venues/", json=venue_data)
        
        # Search by venue name
        response = client.get("/api/v1/venues/?search=Madison")
        data = response.json()
        assert len(data["venues"]) == 1
        assert data["venues"][0]["name"] == "Madison Square Garden"
        
        # Search by city
        response = client.get("/api/v1/venues/?search=Boston")
        data = response.json()
        assert len(data["venues"]) == 1

    def test_list_venues_city_filter(self):
        # Create venues
        venues_data = [
            {"name": "Venue 1", "city": "New York", "address": "Address 1", "capacity": 1000},
            {"name": "Venue 2", "city": "Boston", "address": "Address 2", "capacity": 2000},
            {"name": "Venue 3", "city": "New York", "address": "Address 3", "capacity": 3000},
        ]
        
        for venue_data in venues_data:
            client.post("/api/v1/venues/", json=venue_data)
        
        response = client.get("/api/v1/venues/?city=New York")
        data = response.json()
        assert len(data["venues"]) == 2
        assert all(venue["city"] == "New York" for venue in data["venues"])

    def test_list_venues_min_capacity_filter(self):
        # Create venues
        venues_data = [
            {"name": "Venue 1", "city": "City 1", "address": "Address 1", "capacity": 1000},
            {"name": "Venue 2", "city": "City 2", "address": "Address 2", "capacity": 2000},
            {"name": "Venue 3", "city": "City 3", "address": "Address 3", "capacity": 3000},
        ]
        
        for venue_data in venues_data:
            client.post("/api/v1/venues/", json=venue_data)
        
        response = client.get("/api/v1/venues/?min_capacity=2500")
        data = response.json()
        assert len(data["venues"]) == 1
        assert data["venues"][0]["capacity"] >= 2500

    def test_list_venues_pagination(self):
        # Create 15 venues
        for i in range(15):
            venue_data = {
                "name": f"Venue {i+1}",
                "city": f"City {i+1}",
                "address": f"Address {i+1}",
                "capacity": 1000 + i * 100
            }
            client.post("/api/v1/venues/", json=venue_data)
        
        # Test pagination
        response = client.get("/api/v1/venues/?page=1&page_size=5")
        data = response.json()
        assert len(data["venues"]) == 5
        assert data["total"] == 15
        assert data["page"] == 1
        assert data["total_pages"] == 3
        
        # Test second page
        response = client.get("/api/v1/venues/?page=2&page_size=5")
        data = response.json()
        assert len(data["venues"]) == 5
        assert data["page"] == 2

    def test_list_venues_combined_filters(self):
        # Create venues
        venues_data = [
            {"name": "Big Arena", "city": "New York", "address": "Address 1", "capacity": 5000},
            {"name": "Small Venue", "city": "New York", "address": "Address 2", "capacity": 500},
            {"name": "Big Stadium", "city": "Boston", "address": "Address 3", "capacity": 10000},
        ]
        
        for venue_data in venues_data:
            client.post("/api/v1/venues/", json=venue_data)
        
        # Filter by city and min_capacity
        response = client.get("/api/v1/venues/?city=New York&min_capacity=1000")
        data = response.json()
        assert len(data["venues"]) == 1
        assert data["venues"][0]["name"] == "Big Arena"
