"""Tests for dashboard API endpoints."""
import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timedelta

from src.main import app
from tests.test_fixtures import (
    sample_venues_db,
    sample_concerts_db,
    sample_tickets_db,
    clear_database
)


class TestDashboardAPI:
    """Test dashboard API endpoints with various data scenarios."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    def test_dashboard_empty_state(self, client, clear_database):
        """Test dashboard with no concerts."""
        response = client.get("/dashboard/")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "total_concerts" in data
        assert "upcoming_concerts" in data
        assert "past_concerts" in data
        assert "total_revenue" in data
        assert "recent_concerts" in data
        
        # Verify empty state values
        assert data["total_concerts"] == 0
        assert data["upcoming_concerts"] == 0
        assert data["past_concerts"] == 0
        assert data["total_revenue"] == 0.0
        assert data["recent_concerts"] == []

    def test_dashboard_with_single_concert(self, client, sample_venues_db, clear_database):
        """Test dashboard with a single concert."""
        # Create venue first
        venue_response = client.post("/venues/", json=sample_venues_db[0])
        assert venue_response.status_code == 201
        venue_id = venue_response.json()["id"]
        
        # Create concert
        concert_data = {
            "title": "Solo Concert",
            "artist": "Test Artist",
            "venue_id": venue_id,
            "date": (datetime.now() + timedelta(days=30)).isoformat(),
            "ticket_price": 75.0,
            "total_tickets": 100
        }
        
        concert_response = client.post("/concerts/", json=concert_data)
        assert concert_response.status_code == 201
        
        response = client.get("/dashboard/")
        assert response.status_code == 200
        
        data = response.json()
        assert data["total_concerts"] == 1
        assert data["upcoming_concerts"] == 1
        assert data["past_concerts"] == 0
        assert data["total_revenue"] == 0.0  # No tickets sold yet
        assert len(data["recent_concerts"]) == 1

    def test_dashboard_with_multiple_concerts(self, client, sample_venues_db, sample_concerts_db, clear_database):
        """Test dashboard with multiple concerts."""
        # Create venues
        venue_ids = []
        for venue in sample_venues_db:
            venue_response = client.post("/venues/", json=venue)
            assert venue_response.status_code == 201
            venue_ids.append(venue_response.json()["id"])
        
        # Create concerts with mixed past and future dates
        concerts_created = []
        for i, concert in enumerate(sample_concerts_db[:3]):  # Use first 3 concerts
            concert_data = {
                **concert,
                "venue_id": venue_ids[i % len(venue_ids)],
                # Mix of past and future dates
                "date": (datetime.now() + timedelta(days=(-30 if i == 0 else 30 + i*10))).isoformat()
            }
            concert_response = client.post("/concerts/", json=concert_data)
            assert concert_response.status_code == 201
            concerts_created.append(concert_response.json())
        
        response = client.get("/dashboard/")
        assert response.status_code == 200
        
        data = response.json()
        assert data["total_concerts"] == 3
        assert data["upcoming_concerts"] == 2  # 2 future concerts
        assert data["past_concerts"] == 1     # 1 past concert
        assert len(data["recent_concerts"]) <= 5  # Should be limited

    def test_dashboard_with_tickets_sold(self, client, sample_venues_db, sample_tickets_db, clear_database):
        """Test dashboard revenue calculation with ticket sales."""
        # Create venue
        venue_response = client.post("/venues/", json=sample_venues_db[0])
        assert venue_response.status_code == 201
        venue_id = venue_response.json()["id"]
        
        # Create concert
        concert_data = {
            "title": "Revenue Test Concert",
            "artist": "Test Artist",
            "venue_id": venue_id,
            "date": (datetime.now() + timedelta(days=30)).isoformat(),
            "ticket_price": 100.0,
            "total_tickets": 100
        }
        
        concert_response = client.post("/concerts/", json=concert_data)
        assert concert_response.status_code == 201
        concert_id = concert_response.json()["id"]
        
        # Sell some tickets
        for i in range(3):  # Sell 3 tickets
            ticket_data = {
                **sample_tickets_db[0],
                "concert_id": concert_id,
                "customer_email": f"customer{i}@test.com"
            }
            ticket_response = client.post("/tickets/", json=ticket_data)
            assert ticket_response.status_code == 201
        
        response = client.get("/dashboard/")
        assert response.status_code == 200
        
        data = response.json()
        assert data["total_revenue"] == 300.0  # 3 tickets * $100

    def test_dashboard_future_only_concerts(self, client, sample_venues_db, clear_database):
        """Test dashboard with only future concerts."""
        # Create venue
        venue_response = client.post("/venues/", json=sample_venues_db[0])
        assert venue_response.status_code == 201
        venue_id = venue_response.json()["id"]
        
        # Create multiple future concerts
        future_dates = [
            datetime.now() + timedelta(days=10),
            datetime.now() + timedelta(days=30),
            datetime.now() + timedelta(days=60)
        ]
        
        for i, date in enumerate(future_dates):
            concert_data = {
                "title": f"Future Concert {i+1}",
                "artist": f"Artist {i+1}",
                "venue_id": venue_id,
                "date": date.isoformat(),
                "ticket_price": 50.0 + i*10,
                "total_tickets": 100
            }
            
            concert_response = client.post("/concerts/", json=concert_data)
            assert concert_response.status_code == 201
        
        response = client.get("/dashboard/")
        assert response.status_code == 200
        
        data = response.json()
        assert data["total_concerts"] == 3
        assert data["upcoming_concerts"] == 3
        assert data["past_concerts"] == 0

    def test_dashboard_past_only_concerts(self, client, sample_venues_db, clear_database):
        """Test dashboard with only past concerts."""
        # Create venue
        venue_response = client.post("/venues/", json=sample_venues_db[0])
        assert venue_response.status_code == 201
        venue_id = venue_response.json()["id"]
        
        # Create multiple past concerts
        past_dates = [
            datetime.now() - timedelta(days=60),
            datetime.now() - timedelta(days=30),
            datetime.now() - timedelta(days=10)
        ]
        
        for i, date in enumerate(past_dates):
            concert_data = {
                "title": f"Past Concert {i+1}",
                "artist": f"Artist {i+1}",
                "venue_id": venue_id,
                "date": date.isoformat(),
                "ticket_price": 50.0 + i*10,
                "total_tickets": 100
            }
            
            concert_response = client.post("/concerts/", json=concert_data)
            assert concert_response.status_code == 201
        
        response = client.get("/dashboard/")
        assert response.status_code == 200
        
        data = response.json()
        assert data["total_concerts"] == 3
        assert data["upcoming_concerts"] == 0
        assert data["past_concerts"] == 3

    def test_dashboard_response_structure(self, client, clear_database):
        """Test that dashboard response has correct JSON structure."""
        response = client.get("/dashboard/")
        assert response.status_code == 200
        
        data = response.json()
        
        # Check required fields exist
        required_fields = [
            "total_concerts",
            "upcoming_concerts", 
            "past_concerts",
            "total_revenue",
            "recent_concerts"
        ]
        
        for field in required_fields:
            assert field in data, f"Missing required field: {field}"
        
        # Check data types
        assert isinstance(data["total_concerts"], int)
        assert isinstance(data["upcoming_concerts"], int)
        assert isinstance(data["past_concerts"], int)
        assert isinstance(data["total_revenue"], (int, float))
        assert isinstance(data["recent_concerts"], list)
        
        # If there are recent concerts, check their structure
        if data["recent_concerts"]:
            concert = data["recent_concerts"][0]
            concert_fields = ["id", "title", "artist", "date", "venue_name"]
            for field in concert_fields:
                assert field in concert, f"Missing concert field: {field}"

    def test_dashboard_error_handling(self, client):
        """Test dashboard API error handling."""
        # Test with invalid HTTP method
        response = client.post("/dashboard/")
        assert response.status_code == 405  # Method Not Allowed
        
        # Test dashboard with query parameters (should ignore them)
        response = client.get("/dashboard/?invalid=param")
        assert response.status_code == 200

    def test_dashboard_recent_concerts_limit(self, client, sample_venues_db, clear_database):
        """Test that recent concerts list is properly limited."""
        # Create venue
        venue_response = client.post("/venues/", json=sample_venues_db[0])
        assert venue_response.status_code == 201
        venue_id = venue_response.json()["id"]
        
        # Create more than 5 concerts to test limit
        for i in range(8):
            concert_data = {
                "title": f"Concert {i+1}",
                "artist": f"Artist {i+1}",
                "venue_id": venue_id,
                "date": (datetime.now() + timedelta(days=i+1)).isoformat(),
                "ticket_price": 50.0,
                "total_tickets": 100
            }
            
            concert_response = client.post("/concerts/", json=concert_data)
            assert concert_response.status_code == 201
        
        response = client.get("/dashboard/")
        assert response.status_code == 200
        
        data = response.json()
        # Should limit to 5 recent concerts
        assert len(data["recent_concerts"]) <= 5

    def test_dashboard_with_mixed_revenue_scenarios(self, client, sample_venues_db, sample_tickets_db, clear_database):
        """Test dashboard revenue with multiple concerts and varying ticket sales."""
        # Create venue
        venue_response = client.post("/venues/", json=sample_venues_db[0])
        assert venue_response.status_code == 201
        venue_id = venue_response.json()["id"]
        
        # Create concerts with different prices
        concert_prices = [50.0, 75.0, 100.0]
        concert_ids = []
        
        for i, price in enumerate(concert_prices):
            concert_data = {
                "title": f"Concert {i+1}",
                "artist": f"Artist {i+1}",
                "venue_id": venue_id,
                "date": (datetime.now() + timedelta(days=10+i)).isoformat(),
                "ticket_price": price,
                "total_tickets": 100
            }
            
            concert_response = client.post("/concerts/", json=concert_data)
            assert concert_response.status_code == 201
            concert_ids.append(concert_response.json()["id"])
        
        # Sell different numbers of tickets for each concert
        tickets_sold = [2, 3, 1]  # Different quantities
        expected_revenue = 0
        
        for concert_id, price, quantity in zip(concert_ids, concert_prices, tickets_sold):
            expected_revenue += price * quantity
            
            for j in range(quantity):
                ticket_data = {
                    **sample_tickets_db[0],
                    "concert_id": concert_id,
                    "customer_email": f"customer{concert_id}_{j}@test.com"
                }
                ticket_response = client.post("/tickets/", json=ticket_data)
                assert ticket_response.status_code == 201
        
        response = client.get("/dashboard/")
        assert response.status_code == 200
        
        data = response.json()
        assert data["total_concerts"] == 3
        assert abs(data["total_revenue"] - expected_revenue) < 0.01  # Allow for floating point precision
