"""Tests for dashboard statistics API endpoints."""
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


class TestDashboardStatsAPI:
    """Test dashboard statistics API endpoints."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    def test_concert_statistics_empty_state(self, client, clear_database):
        """Test concert statistics with no data."""
        response = client.get("/dashboard/stats/concerts")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["total_concerts"] == 0
        assert data["upcoming_concerts"] == 0
        assert data["past_concerts"] == 0
        assert data["monthly_breakdown"] == []

    def test_concert_statistics_with_data(self, client, sample_venues_db, clear_database):
        """Test concert statistics with actual data."""
        # Create venue
        venue_response = client.post("/venues/", json=sample_venues_db[0])
        assert venue_response.status_code == 201
        venue_id = venue_response.json()["id"]
        
        # Create concerts across different months
        concert_dates = [
            datetime.now() - timedelta(days=60),  # Past
            datetime.now() - timedelta(days=30),  # Past
            datetime.now() + timedelta(days=30),  # Future
            datetime.now() + timedelta(days=60),  # Future
        ]
        
        for i, date in enumerate(concert_dates):
            concert_data = {
                "title": f"Concert {i+1}",
                "artist": f"Artist {i+1}",
                "venue_id": venue_id,
                "date": date.isoformat(),
                "ticket_price": 50.0,
                "total_tickets": 100
            }
            
            concert_response = client.post("/concerts/", json=concert_data)
            assert concert_response.status_code == 201
        
        response = client.get("/dashboard/stats/concerts")
        assert response.status_code == 200
        
        data = response.json()
        assert data["total_concerts"] == 4
        assert data["upcoming_concerts"] == 2
        assert data["past_concerts"] == 2
        assert len(data["monthly_breakdown"]) > 0

    def test_revenue_statistics_empty_state(self, client, clear_database):
        """Test revenue statistics with no data."""
        response = client.get("/dashboard/stats/revenue")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["total_revenue"] == 0.0
        assert data["revenue_by_concert"] == []

    def test_revenue_statistics_with_tickets(self, client, sample_venues_db, sample_tickets_db, clear_database):
        """Test revenue statistics with ticket sales."""
        # Create venue
        venue_response = client.post("/venues/", json=sample_venues_db[0])
        assert venue_response.status_code == 201
        venue_id = venue_response.json()["id"]
        
        # Create concerts with different prices
        concert_data_list = [
            {
                "title": "Expensive Concert",
                "artist": "Premium Artist",
                "venue_id": venue_id,
                "date": (datetime.now() + timedelta(days=30)).isoformat(),
                "ticket_price": 150.0,
                "total_tickets": 100
            },
            {
                "title": "Budget Concert",
                "artist": "Local Artist",
                "venue_id": venue_id,
                "date": (datetime.now() + timedelta(days=60)).isoformat(),
                "ticket_price": 25.0,
                "total_tickets": 200
            }
        ]
        
        concert_ids = []
        for concert_data in concert_data_list:
            concert_response = client.post("/concerts/", json=concert_data)
            assert concert_response.status_code == 201
            concert_ids.append(concert_response.json()["id"])
        
        # Sell tickets for first concert (2 tickets)
        for i in range(2):
            ticket_data = {
                **sample_tickets_db[0],
                "concert_id": concert_ids[0],
                "customer_email": f"customer{i}@test.com"
            }
            ticket_response = client.post("/tickets/", json=ticket_data)
            assert ticket_response.status_code == 201
        
        # Sell tickets for second concert (3 tickets)
        for i in range(3):
            ticket_data = {
                **sample_tickets_db[0],
                "concert_id": concert_ids[1],
                "customer_email": f"budget{i}@test.com"
            }
            ticket_response = client.post("/tickets/", json=ticket_data)
            assert ticket_response.status_code == 201
        
        response = client.get("/dashboard/stats/revenue")
        assert response.status_code == 200
        
        data = response.json()
        expected_revenue = (150.0 * 2) + (25.0 * 3)  # 300 + 75 = 375
        assert abs(data["total_revenue"] - expected_revenue) < 0.01
        
        # Check revenue by concert
        assert len(data["revenue_by_concert"]) == 2
        
        # Find the expensive concert in results
        expensive_concert = next(
            (c for c in data["revenue_by_concert"] if c["ticket_price"] == 150.0),
            None
        )
        assert expensive_concert is not None
        assert expensive_concert["tickets_sold"] == 2
        assert expensive_concert["revenue"] == 300.0

    def test_venue_statistics_empty_state(self, client, clear_database):
        """Test venue statistics with no data."""
        response = client.get("/dashboard/stats/venues")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["total_venues"] == 0
        assert data["active_venues"] == 0
        assert data["venue_details"] == []

    def test_venue_statistics_with_data(self, client, sample_venues_db, clear_database):
        """Test venue statistics with venues and concerts."""
        # Create venues
        venue_ids = []
        for venue in sample_venues_db[:2]:  # Use first 2 venues
            venue_response = client.post("/venues/", json=venue)
            assert venue_response.status_code == 201
            venue_ids.append(venue_response.json()["id"])
        
        # Create concerts only for first venue
        for i in range(3):
            concert_data = {
                "title": f"Concert {i+1}",
                "artist": f"Artist {i+1}",
                "venue_id": venue_ids[0],
                "date": (datetime.now() + timedelta(days=30+i*10)).isoformat(),
                "ticket_price": 50.0,
                "total_tickets": 100
            }
            
            concert_response = client.post("/concerts/", json=concert_data)
            assert concert_response.status_code == 201
        
        response = client.get("/dashboard/stats/venues")
        assert response.status_code == 200
        
        data = response.json()
        assert data["total_venues"] == 2
        assert data["active_venues"] == 1  # Only first venue has concerts
        assert len(data["venue_details"]) == 2
        
        # Find venue with concerts
        active_venue = next(
            (v for v in data["venue_details"] if v["concerts_hosted"] > 0),
            None
        )
        assert active_venue is not None
        assert active_venue["concerts_hosted"] == 3

    def test_statistics_response_structure(self, client, clear_database):
        """Test that all statistics endpoints return correct structure."""
        endpoints = [
            "/dashboard/stats/concerts",
            "/dashboard/stats/revenue", 
            "/dashboard/stats/venues"
        ]
        
        for endpoint in endpoints:
            response = client.get(endpoint)
            assert response.status_code == 200
            
            data = response.json()
            assert isinstance(data, dict), f"Endpoint {endpoint} should return dict"
            
            # Check specific structures
            if "concerts" in endpoint:
                assert "total_concerts" in data
                assert "upcoming_concerts" in data
                assert "past_concerts" in data
                assert "monthly_breakdown" in data
            elif "revenue" in endpoint:
                assert "total_revenue" in data
                assert "revenue_by_concert" in data
            elif "venues" in endpoint:
                assert "total_venues" in data
                assert "active_venues" in data
                assert "venue_details" in data

    def test_statistics_error_handling(self, client):
        """Test error handling for statistics endpoints."""
        endpoints = [
            "/dashboard/stats/concerts",
            "/dashboard/stats/revenue",
            "/dashboard/stats/venues"
        ]
        
        for endpoint in endpoints:
            # Test invalid HTTP methods
            response = client.post(endpoint)
            assert response.status_code == 405
            
            # Test with query parameters (should be ignored)
            response = client.get(f"{endpoint}?invalid=param")
            assert response.status_code == 200

    def test_monthly_breakdown_format(self, client, sample_venues_db, clear_database):
        """Test that monthly breakdown has correct format."""
        # Create venue
        venue_response = client.post("/venues/", json=sample_venues_db[0])
        assert venue_response.status_code == 201
        venue_id = venue_response.json()["id"]
        
        # Create concert
        concert_data = {
            "title": "Test Concert",
            "artist": "Test Artist",
            "venue_id": venue_id,
            "date": datetime.now().isoformat(),
            "ticket_price": 50.0,
            "total_tickets": 100
        }
        
        concert_response = client.post("/concerts/", json=concert_data)
        assert concert_response.status_code == 201
        
        response = client.get("/dashboard/stats/concerts")
        assert response.status_code == 200
        
        data = response.json()
        if data["monthly_breakdown"]:
            month_data = data["monthly_breakdown"][0]
            assert "year" in month_data
            assert "month" in month_data
            assert "count" in month_data
            assert isinstance(month_data["year"], int)
            assert isinstance(month_data["month"], int)
            assert isinstance(month_data["count"], int)
            assert 1 <= month_data["month"] <= 12
