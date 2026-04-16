"""Tests for Pydantic schemas."""

import pytest
from datetime import datetime, timezone
from pydantic import ValidationError
from schemas import (
    TourCreate, TourUpdate, TourResponse, TourStatus,
    ConcertCreate, ConcertUpdate, ConcertResponse
)


class TestTourSchemas:
    """Tests for Tour schemas."""

    def test_tour_create_valid(self):
        """Test valid TourCreate schema."""
        tour_data = {
            "name": "Summer Tour 2024",
            "description": "A great summer tour",
            "start_date": "2024-06-01T10:00:00Z",
            "end_date": "2024-08-31T22:00:00Z",
            "status": "planning"
        }
        tour = TourCreate(**tour_data)
        assert tour.name == "Summer Tour 2024"
        assert tour.status == TourStatus.planning
        assert isinstance(tour.start_date, datetime)

    def test_tour_create_minimal_valid(self):
        """Test TourCreate with minimal required fields."""
        tour_data = {
            "name": "Minimal Tour",
            "start_date": "2024-06-01T10:00:00Z"
        }
        tour = TourCreate(**tour_data)
        assert tour.name == "Minimal Tour"
        assert tour.description is None
        assert tour.end_date is None
        assert tour.status == TourStatus.planning

    def test_tour_create_missing_name(self):
        """Test TourCreate fails with missing name."""
        tour_data = {
            "start_date": "2024-06-01T10:00:00Z"
        }
        with pytest.raises(ValidationError) as exc_info:
            TourCreate(**tour_data)
        assert "name" in str(exc_info.value)

    def test_tour_create_empty_name(self):
        """Test TourCreate fails with empty name."""
        tour_data = {
            "name": "",
            "start_date": "2024-06-01T10:00:00Z"
        }
        with pytest.raises(ValidationError) as exc_info:
            TourCreate(**tour_data)
        assert "at least 1 character" in str(exc_info.value)

    def test_tour_create_name_too_long(self):
        """Test TourCreate fails with name too long."""
        tour_data = {
            "name": "x" * 101,
            "start_date": "2024-06-01T10:00:00Z"
        }
        with pytest.raises(ValidationError) as exc_info:
            TourCreate(**tour_data)
        assert "at most 100 characters" in str(exc_info.value)

    def test_tour_create_missing_start_date(self):
        """Test TourCreate fails with missing start_date."""
        tour_data = {
            "name": "Tour without start date"
        }
        with pytest.raises(ValidationError) as exc_info:
            TourCreate(**tour_data)
        assert "start_date" in str(exc_info.value)

    def test_tour_create_invalid_status(self):
        """Test TourCreate fails with invalid status."""
        tour_data = {
            "name": "Tour",
            "start_date": "2024-06-01T10:00:00Z",
            "status": "invalid_status"
        }
        with pytest.raises(ValidationError) as exc_info:
            TourCreate(**tour_data)
        assert "status" in str(exc_info.value)

    def test_tour_update_partial(self):
        """Test TourUpdate with partial data."""
        update_data = {
            "name": "Updated Tour Name",
            "status": "active"
        }
        tour_update = TourUpdate(**update_data)
        assert tour_update.name == "Updated Tour Name"
        assert tour_update.status == TourStatus.active
        assert tour_update.description is None
        assert tour_update.start_date is None
        assert tour_update.end_date is None

    def test_tour_response_with_concerts(self):
        """Test TourResponse serialization with concerts."""
        # Mock data that would come from SQLAlchemy model
        tour_data = {
            "id": 1,
            "name": "Tour Response Test",
            "description": "Test description",
            "start_date": datetime(2024, 6, 1, 10, 0, 0, tzinfo=timezone.utc),
            "end_date": datetime(2024, 8, 31, 22, 0, 0, tzinfo=timezone.utc),
            "status": "planning",
            "concerts": [
                {
                    "id": 1,
                    "venue": "Test Venue",
                    "city": "Test City",
                    "country": "Test Country",
                    "date": datetime(2024, 6, 15, 20, 0, 0, tzinfo=timezone.utc),
                    "ticket_price": 50.0,
                    "available_tickets": 1000,
                    "tour_id": 1
                }
            ]
        }
        tour_response = TourResponse(**tour_data)
        assert tour_response.id == 1
        assert tour_response.name == "Tour Response Test"
        assert len(tour_response.concerts) == 1
        assert tour_response.concerts[0].venue == "Test Venue"


class TestConcertSchemas:
    """Tests for Concert schemas."""

    def test_concert_create_valid(self):
        """Test valid ConcertCreate schema."""
        concert_data = {
            "venue": "Madison Square Garden",
            "city": "New York",
            "country": "USA",
            "date": "2024-06-15T20:00:00Z",
            "ticket_price": 75.0,
            "available_tickets": 20000,
            "tour_id": 1
        }
        concert = ConcertCreate(**concert_data)
        assert concert.venue == "Madison Square Garden"
        assert concert.city == "New York"
        assert concert.country == "USA"
        assert concert.ticket_price == 75.0
        assert concert.available_tickets == 20000
        assert concert.tour_id == 1
        assert isinstance(concert.date, datetime)

    def test_concert_create_missing_required_fields(self):
        """Test ConcertCreate fails with missing required fields."""
        concert_data = {
            "venue": "Madison Square Garden",
            # Missing other required fields
        }
        with pytest.raises(ValidationError) as exc_info:
            ConcertCreate(**concert_data)
        errors = str(exc_info.value)
        assert "city" in errors
        assert "country" in errors
        assert "date" in errors
        assert "ticket_price" in errors
        assert "available_tickets" in errors
        assert "tour_id" in errors

    def test_concert_create_empty_venue(self):
        """Test ConcertCreate fails with empty venue."""
        concert_data = {
            "venue": "",
            "city": "New York",
            "country": "USA",
            "date": "2024-06-15T20:00:00Z",
            "ticket_price": 75.0,
            "available_tickets": 20000,
            "tour_id": 1
        }
        with pytest.raises(ValidationError) as exc_info:
            ConcertCreate(**concert_data)
        assert "at least 1 character" in str(exc_info.value)

    def test_concert_create_negative_ticket_price(self):
        """Test ConcertCreate fails with negative ticket price."""
        concert_data = {
            "venue": "Madison Square Garden",
            "city": "New York",
            "country": "USA",
            "date": "2024-06-15T20:00:00Z",
            "ticket_price": -10.0,
            "available_tickets": 20000,
            "tour_id": 1
        }
        with pytest.raises(ValidationError) as exc_info:
            ConcertCreate(**concert_data)
        assert "greater than 0" in str(exc_info.value)

    def test_concert_create_negative_available_tickets(self):
        """Test ConcertCreate fails with negative available tickets."""
        concert_data = {
            "venue": "Madison Square Garden",
            "city": "New York",
            "country": "USA",
            "date": "2024-06-15T20:00:00Z",
            "ticket_price": 75.0,
            "available_tickets": -100,
            "tour_id": 1
        }
        with pytest.raises(ValidationError) as exc_info:
            ConcertCreate(**concert_data)
        assert "greater than or equal to 0" in str(exc_info.value)

    def test_concert_create_zero_tour_id(self):
        """Test ConcertCreate fails with zero tour_id."""
        concert_data = {
            "venue": "Madison Square Garden",
            "city": "New York",
            "country": "USA",
            "date": "2024-06-15T20:00:00Z",
            "ticket_price": 75.0,
            "available_tickets": 20000,
            "tour_id": 0
        }
        with pytest.raises(ValidationError) as exc_info:
            ConcertCreate(**concert_data)
        assert "greater than 0" in str(exc_info.value)

    def test_concert_update_partial(self):
        """Test ConcertUpdate with partial data."""
        update_data = {
            "venue": "Updated Venue",
            "ticket_price": 80.0
        }
        concert_update = ConcertUpdate(**update_data)
        assert concert_update.venue == "Updated Venue"
        assert concert_update.ticket_price == 80.0
        assert concert_update.city is None
        assert concert_update.country is None
        assert concert_update.date is None
        assert concert_update.available_tickets is None

    def test_concert_response_serialization(self):
        """Test ConcertResponse serialization."""
        concert_data = {
            "id": 1,
            "venue": "Madison Square Garden",
            "city": "New York",
            "country": "USA",
            "date": datetime(2024, 6, 15, 20, 0, 0, tzinfo=timezone.utc),
            "ticket_price": 75.0,
            "available_tickets": 20000,
            "tour_id": 1
        }
        concert_response = ConcertResponse(**concert_data)
        assert concert_response.id == 1
        assert concert_response.venue == "Madison Square Garden"
        assert concert_response.city == "New York"
        assert concert_response.country == "USA"
        assert concert_response.ticket_price == 75.0
        assert concert_response.available_tickets == 20000
        assert concert_response.tour_id == 1


class TestSchemaValidation:
    """Tests for schema validation edge cases."""

    def test_iso_date_format_parsing(self):
        """Test that schemas correctly parse ISO date formats."""
        # Test various ISO format variations
        date_formats = [
            "2024-06-15T20:00:00Z",
            "2024-06-15T20:00:00+00:00",
            "2024-06-15T20:00:00.000Z",
            "2024-06-15 20:00:00"
        ]
        
        for date_str in date_formats:
            tour_data = {
                "name": "Date Test Tour",
                "start_date": date_str
            }
            tour = TourCreate(**tour_data)
            assert isinstance(tour.start_date, datetime)

    def test_schema_imports_without_errors(self):
        """Test that all schemas can be imported without errors."""
        # This test will pass if the file imports successfully
        from schemas import (
            TourCreate, TourUpdate, TourResponse, TourStatus,
            ConcertCreate, ConcertUpdate, ConcertResponse
        )
        assert TourCreate is not None
        assert TourUpdate is not None
        assert TourResponse is not None
        assert TourStatus is not None
        assert ConcertCreate is not None
        assert ConcertUpdate is not None
        assert ConcertResponse is not None
