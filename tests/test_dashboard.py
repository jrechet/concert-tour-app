import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime, timedelta
import json

from fastapi.testclient import TestClient
from src.main import app


@pytest.fixture
def client():
    """Test client fixture"""
    return TestClient(app)


@pytest.fixture
def sample_concerts():
    """Sample concert data for testing"""
    return [
        {
            "id": 1,
            "title": "Rock Concert",
            "artist": "The Rock Band",
            "date": datetime.now() + timedelta(days=30),
            "venue": "Main Arena",
            "ticket_price": 75.0,
            "tickets_available": 150,
            "total_tickets": 200,
            "status": "upcoming"
        },
        {
            "id": 2,
            "title": "Jazz Night",
            "artist": "Jazz Ensemble",
            "date": datetime.now() + timedelta(days=15),
            "venue": "Jazz Club",
            "ticket_price": 45.0,
            "tickets_available": 80,
            "total_tickets": 100,
            "status": "upcoming"
        }
    ]


@pytest.fixture
def sample_venues():
    """Sample venue data for testing"""
    return [
        {
            "id": 1,
            "name": "Main Arena",
            "capacity": 5000,
            "location": "Downtown",
            "concerts_count": 3
        },
        {
            "id": 2,
            "name": "Jazz Club",
            "capacity": 200,
            "location": "Arts District",
            "concerts_count": 1
        }
    ]


@pytest.fixture
def sample_dashboard_stats():
    """Sample dashboard statistics for testing"""
    return {
        "total_concerts": 25,
        "upcoming_concerts": 8,
        "total_venues": 5,
        "total_ticket_sales": 15000,
        "revenue": 750000.0,
        "average_attendance": 85.5
    }


class TestDashboardRoute:
    """Test dashboard HTML route"""

    @patch('src.routes.dashboard.get_dashboard_stats')
    def test_dashboard_route_success(self, mock_get_stats, client):
        """Test dashboard route returns correct template"""
        # Mock the database call
        mock_get_stats.return_value = {
            "total_concerts": 10,
            "upcoming_concerts": 5,
            "total_venues": 3,
            "total_ticket_sales": 1000,
            "revenue": 50000.0,
            "average_attendance": 80.0
        }
        
        response = client.get("/dashboard")
        
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        # Verify template context contains stats
        assert "dashboard.html" in str(response.content) or b"Dashboard" in response.content

    @patch('src.routes.dashboard.get_dashboard_stats')
    def test_dashboard_route_handles_database_error(self, mock_get_stats, client):
        """Test dashboard route handles database errors gracefully"""
        # Mock database error
        mock_get_stats.side_effect = Exception("Database connection failed")
        
        # Should still return 200 with error handling
        response = client.get("/dashboard")
        
        # The route should handle errors gracefully
        assert response.status_code in [200, 500]


class TestDashboardStatsAPI:
    """Test dashboard stats API endpoint"""

    @patch('src.routes.dashboard.get_dashboard_stats')
    def test_dashboard_stats_success(self, mock_get_stats, client, sample_dashboard_stats):
        """Test successful dashboard stats retrieval"""
        mock_get_stats.return_value = sample_dashboard_stats
        
        response = client.get("/api/dashboard/stats")
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/json"
        
        data = response.json()
        assert data["total_concerts"] == 25
        assert data["upcoming_concerts"] == 8
        assert data["total_venues"] == 5
        assert data["total_ticket_sales"] == 15000
        assert data["revenue"] == 750000.0
        assert data["average_attendance"] == 85.5

    @patch('src.routes.dashboard.get_dashboard_stats')
    def test_dashboard_stats_empty_data(self, mock_get_stats, client):
        """Test dashboard stats with empty/null data"""
        mock_get_stats.return_value = {
            "total_concerts": 0,
            "upcoming_concerts": 0,
            "total_venues": 0,
            "total_ticket_sales": 0,
            "revenue": 0.0,
            "average_attendance": 0.0
        }
        
        response = client.get("/api/dashboard/stats")
        
        assert response.status_code == 200
        data = response.json()
        assert all(value == 0 or value == 0.0 for value in data.values())

    @patch('src.routes.dashboard.get_dashboard_stats')
    def test_dashboard_stats_database_error(self, mock_get_stats, client):
        """Test dashboard stats API handles database errors"""
        mock_get_stats.side_effect = Exception("Database error")
        
        response = client.get("/api/dashboard/stats")
        
        # Should return 500 for API errors
        assert response.status_code == 500
        assert "error" in response.json()

    @patch('src.routes.dashboard.get_dashboard_stats')
    def test_dashboard_stats_response_structure(self, mock_get_stats, client, sample_dashboard_stats):
        """Test dashboard stats response has correct structure"""
        mock_get_stats.return_value = sample_dashboard_stats
        
        response = client.get("/api/dashboard/stats")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify all required fields are present
        required_fields = [
            "total_concerts", "upcoming_concerts", "total_venues",
            "total_ticket_sales", "revenue", "average_attendance"
        ]
        
        for field in required_fields:
            assert field in data
            assert isinstance(data[field], (int, float))


class TestDashboardConcertsAPI:
    """Test dashboard concerts API endpoint"""

    @patch('src.routes.dashboard.get_recent_concerts')
    def test_dashboard_concerts_success(self, mock_get_concerts, client, sample_concerts):
        """Test successful dashboard concerts retrieval"""
        mock_get_concerts.return_value = sample_concerts
        
        response = client.get("/api/dashboard/concerts")
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/json"
        
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 2
        
        # Verify first concert structure
        concert = data[0]
        assert concert["id"] == 1
        assert concert["title"] == "Rock Concert"
        assert concert["artist"] == "The Rock Band"
        assert concert["venue"] == "Main Arena"
        assert concert["ticket_price"] == 75.0
        assert concert["tickets_available"] == 150
        assert concert["total_tickets"] == 200
        assert concert["status"] == "upcoming"

    @patch('src.routes.dashboard.get_recent_concerts')
    def test_dashboard_concerts_empty_list(self, mock_get_concerts, client):
        """Test dashboard concerts with empty results"""
        mock_get_concerts.return_value = []
        
        response = client.get("/api/dashboard/concerts")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0

    @patch('src.routes.dashboard.get_recent_concerts')
    def test_dashboard_concerts_database_error(self, mock_get_concerts, client):
        """Test dashboard concerts API handles database errors"""
        mock_get_concerts.side_effect = Exception("Database connection failed")
        
        response = client.get("/api/dashboard/concerts")
        
        assert response.status_code == 500
        assert "error" in response.json()

    @patch('src.routes.dashboard.get_recent_concerts')
    def test_dashboard_concerts_response_structure(self, mock_get_concerts, client, sample_concerts):
        """Test dashboard concerts response structure"""
        mock_get_concerts.return_value = sample_concerts
        
        response = client.get("/api/dashboard/concerts")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify each concert has required fields
        required_fields = [
            "id", "title", "artist", "date", "venue",
            "ticket_price", "tickets_available", "total_tickets", "status"
        ]
        
        for concert in data:
            for field in required_fields:
                assert field in concert


class TestDashboardVenuesAPI:
    """Test dashboard venues API endpoint"""

    @patch('src.routes.dashboard.get_venue_summary')
    def test_dashboard_venues_success(self, mock_get_venues, client, sample_venues):
        """Test successful dashboard venues retrieval"""
        mock_get_venues.return_value = sample_venues
        
        response = client.get("/api/dashboard/venues")
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/json"
        
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 2
        
        # Verify first venue structure
        venue = data[0]
        assert venue["id"] == 1
        assert venue["name"] == "Main Arena"
        assert venue["capacity"] == 5000
        assert venue["location"] == "Downtown"
        assert venue["concerts_count"] == 3

    @patch('src.routes.dashboard.get_venue_summary')
    def test_dashboard_venues_empty_list(self, mock_get_venues, client):
        """Test dashboard venues with empty results"""
        mock_get_venues.return_value = []
        
        response = client.get("/api/dashboard/venues")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0

    @patch('src.routes.dashboard.get_venue_summary')
    def test_dashboard_venues_database_error(self, mock_get_venues, client):
        """Test dashboard venues API handles database errors"""
        mock_get_venues.side_effect = Exception("Database error")
        
        response = client.get("/api/dashboard/venues")
        
        assert response.status_code == 500
        assert "error" in response.json()

    @patch('src.routes.dashboard.get_venue_summary')
    def test_dashboard_venues_response_structure(self, mock_get_venues, client, sample_venues):
        """Test dashboard venues response structure"""
        mock_get_venues.return_value = sample_venues
        
        response = client.get("/api/dashboard/venues")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify each venue has required fields
        required_fields = ["id", "name", "capacity", "location", "concerts_count"]
        
        for venue in data:
            for field in required_fields:
                assert field in venue
                
    @patch('src.routes.dashboard.get_venue_summary')
    def test_dashboard_venues_data_types(self, mock_get_venues, client, sample_venues):
        """Test dashboard venues data types are correct"""
        mock_get_venues.return_value = sample_venues
        
        response = client.get("/api/dashboard/venues")
        
        assert response.status_code == 200
        data = response.json()
        
        for venue in data:
            assert isinstance(venue["id"], int)
            assert isinstance(venue["name"], str)
            assert isinstance(venue["capacity"], int)
            assert isinstance(venue["location"], str)
            assert isinstance(venue["concerts_count"], int)


class TestDashboardIntegration:
    """Integration tests for dashboard functionality"""

    @patch('src.routes.dashboard.get_dashboard_stats')
    @patch('src.routes.dashboard.get_recent_concerts')
    @patch('src.routes.dashboard.get_venue_summary')
    def test_all_dashboard_endpoints_work_together(self, mock_venues, mock_concerts, mock_stats, client):
        """Test that all dashboard endpoints work correctly together"""
        # Set up mocks
        mock_stats.return_value = {"total_concerts": 5, "upcoming_concerts": 3, "total_venues": 2, "total_ticket_sales": 100, "revenue": 5000.0, "average_attendance": 90.0}
        mock_concerts.return_value = [{"id": 1, "title": "Test Concert", "artist": "Test Artist", "date": datetime.now(), "venue": "Test Venue", "ticket_price": 50.0, "tickets_available": 100, "total_tickets": 150, "status": "upcoming"}]
        mock_venues.return_value = [{"id": 1, "name": "Test Venue", "capacity": 1000, "location": "Test City", "concerts_count": 2}]
        
        # Test main dashboard
        dashboard_response = client.get("/dashboard")
        assert dashboard_response.status_code == 200
        
        # Test all API endpoints
        stats_response = client.get("/api/dashboard/stats")
        assert stats_response.status_code == 200
        
        concerts_response = client.get("/api/dashboard/concerts")
        assert concerts_response.status_code == 200
        
        venues_response = client.get("/api/dashboard/venues")
        assert venues_response.status_code == 200
        
        # Verify data consistency
        assert len(concerts_response.json()) == 1
        assert len(venues_response.json()) == 1
        assert stats_response.json()["total_venues"] == 2

    def test_dashboard_endpoints_without_mocks_fail_gracefully(self, client):
        """Test that endpoints fail gracefully when database is unavailable"""
        # These should either return 500 or handle errors gracefully
        # depending on implementation
        
        stats_response = client.get("/api/dashboard/stats")
        assert stats_response.status_code in [200, 500]
        
        concerts_response = client.get("/api/dashboard/concerts")
        assert concerts_response.status_code in [200, 500]
        
        venues_response = client.get("/api/dashboard/venues")
        assert venues_response.status_code in [200, 500]
