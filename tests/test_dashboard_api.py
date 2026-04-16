"""Tests for dashboard API endpoints."""

import pytest
from datetime import date, datetime
from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from src.main import app
from src.models import Tour, Concert, Venue, Ticket, TicketStatus
from tests.conftest import create_test_tour, create_test_venue, create_test_concert


client = TestClient(app)


class TestTourOverview:
    """Test tour overview endpoint."""
    
    def test_get_tour_overview_success(self, db: Session):
        """Test successful tour overview retrieval."""
        # Create test data
        tour = create_test_tour(db, name="Test Tour 2024", status="active")
        venue = create_test_venue(db, name="Test Venue", city="Test City")
        
        # Create concerts with different statuses
        concert1 = create_test_concert(
            db, 
            tour_id=tour.id, 
            venue_id=venue.id, 
            date=date(2024, 6, 15),
            status="completed"
        )
        concert2 = create_test_concert(
            db, 
            tour_id=tour.id, 
            venue_id=venue.id, 
            date=date(2024, 7, 20),
            status="scheduled"
        )
        
        response = client.get("/api/v1/dashboard/tour-overview")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["id"] == tour.id
        assert data["name"] == "Test Tour 2024"
        assert data["status"] == "active"
        assert data["total_concerts"] == 2
        assert data["completed_concerts"] == 1
        assert data["progress"] == 50.0
    
    def test_get_tour_overview_specific_tour(self, db: Session):
        """Test tour overview for specific tour ID."""
        tour = create_test_tour(db, name="Specific Tour", status="planning")
        
        response = client.get(f"/api/v1/dashboard/tour-overview?tour_id={tour.id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == tour.id
        assert data["name"] == "Specific Tour"
        assert data["status"] == "planning"
    
    def test_get_tour_overview_not_found(self, db: Session):
        """Test tour overview with non-existent tour ID."""
        response = client.get("/api/v1/dashboard/tour-overview?tour_id=99999")
        
        assert response.status_code == 404
        assert "Tour not found" in response.json()["detail"]
    
    def test_get_tour_overview_no_active_tour(self, db: Session):
        """Test tour overview when no active tour exists."""
        # Create only completed tour
        create_test_tour(db, name="Completed Tour", status="completed")
        
        response = client.get("/api/v1/dashboard/tour-overview")
        
        assert response.status_code == 404


class TestDashboardStatistics:
    """Test dashboard statistics endpoint."""
    
    def test_get_statistics_success(self, db: Session):
        """Test successful statistics retrieval."""
        # Create test data
        tour = create_test_tour(db, name="Stats Tour", status="active")
        
        venue1 = create_test_venue(db, name="Venue 1", city="City 1", country="Country 1", capacity=1000)
        venue2 = create_test_venue(db, name="Venue 2", city="City 2", country="Country 1", capacity=2000)
        venue3 = create_test_venue(db, name="Venue 3", city="City 3", country="Country 2", capacity=1500)
        
        concert1 = create_test_concert(db, tour_id=tour.id, venue_id=venue1.id)
        concert2 = create_test_concert(db, tour_id=tour.id, venue_id=venue2.id)
        concert3 = create_test_concert(db, tour_id=tour.id, venue_id=venue3.id)
        
        # Create tickets
        ticket1 = Ticket(
            concert_id=concert1.id,
            section="A",
            row="1",
            seat="1",
            price=Decimal("50.00"),
            status=TicketStatus.SOLD
        )
        ticket2 = Ticket(
            concert_id=concert2.id,
            section="B",
            row="2",
            seat="2",
            price=Decimal("75.00"),
            status=TicketStatus.SOLD
        )
        
        db.add_all([ticket1, ticket2])
        db.commit()
        
        response = client.get("/api/v1/dashboard/statistics")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["concerts"] == 3
        assert data["cities"] == 3  # 3 unique cities
        assert data["countries"] == 2  # 2 unique countries
        assert data["capacity"] == 4500  # Sum of venue capacities
        assert data["revenue"] == 125.0  # Sum of ticket prices
    
    def test_get_statistics_specific_tour(self, db: Session):
        """Test statistics for specific tour."""
        tour1 = create_test_tour(db, name="Tour 1", status="active")
        tour2 = create_test_tour(db, name="Tour 2", status="planning")
        
        venue = create_test_venue(db, capacity=1000)
        
        # Concerts for different tours
        create_test_concert(db, tour_id=tour1.id, venue_id=venue.id)
        create_test_concert(db, tour_id=tour2.id, venue_id=venue.id)
        
        response = client.get(f"/api/v1/dashboard/statistics?tour_id={tour2.id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["concerts"] == 1  # Only tour2 concerts
    
    def test_get_statistics_no_active_tour(self, db: Session):
        """Test statistics when no active tour exists."""
        create_test_tour(db, name="Completed Tour", status="completed")
        
        response = client.get("/api/v1/dashboard/statistics")
        
        assert response.status_code == 404


class TestCalendarData:
    """Test calendar data endpoint."""
    
    def test_get_calendar_data_success(self, db: Session):
        """Test successful calendar data retrieval."""
        tour = create_test_tour(db, name="Calendar Tour", status="active")
        venue = create_test_venue(db, name="Calendar Venue", city="Calendar City")
        
        # Create concerts in June 2024
        concert1 = create_test_concert(
            db,
            tour_id=tour.id,
            venue_id=venue.id,
            date=date(2024, 6, 15)
        )
        concert2 = create_test_concert(
            db,
            tour_id=tour.id,
            venue_id=venue.id,
            date=date(2024, 6, 20)
        )
        
        response = client.get("/api/v1/dashboard/calendar?year=2024&month=6")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["year"] == 2024
        assert data["month"] == 6
        assert data["month_name"] == "June"
        assert data["total_concerts"] == 2
        assert len(data["weeks"]) >= 5  # June 2024 spans 6 weeks
        
        # Check pagination
        assert data["pagination"]["prev"]["month"] == 5  # May
        assert data["pagination"]["prev"]["year"] == 2024
        assert data["pagination"]["next"]["month"] == 7  # July
        assert data["pagination"]["next"]["year"] == 2024
    
    def test_get_calendar_data_year_boundary(self, db: Session):
        """Test calendar pagination across year boundary."""
        # Test January (previous should be December of previous year)
        response = client.get("/api/v1/dashboard/calendar?year=2024&month=1")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["pagination"]["prev"]["month"] == 12
        assert data["pagination"]["prev"]["year"] == 2023
        
        # Test December (next should be January of next year)
        response = client.get("/api/v1/dashboard/calendar?year=2024&month=12")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["pagination"]["next"]["month"] == 1
        assert data["pagination"]["next"]["year"] == 2025
    
    def test_get_calendar_data_invalid_month(self, db: Session):
        """Test calendar with invalid month."""
        response = client.get("/api/v1/dashboard/calendar?year=2024&month=13")
        
        assert response.status_code == 400
        assert "Month must be between 1 and 12" in response.json()["detail"]
    
    def test_get_calendar_data_specific_tour(self, db: Session):
        """Test calendar for specific tour."""
        tour1 = create_test_tour(db, name="Tour 1", status="active")
        tour2 = create_test_tour(db, name="Tour 2", status="planning")
        
        venue = create_test_venue(db)
        
        # Concerts for different tours in same month
        create_test_concert(db, tour_id=tour1.id, venue_id=venue.id, date=date(2024, 6, 15))
        create_test_concert(db, tour_id=tour2.id, venue_id=venue.id, date=date(2024, 6, 20))
        
        response = client.get(f"/api/v1/dashboard/calendar?year=2024&month=6&tour_id={tour1.id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["total_concerts"] == 1  # Only tour1 concerts
    
    def test_get_calendar_data_empty_month(self, db: Session):
        """Test calendar with no concerts."""
        response = client.get("/api/v1/dashboard/calendar?year=2024&month=6")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["total_concerts"] == 0
        assert len(data["weeks"]) >= 5  # Still returns calendar structure
