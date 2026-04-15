"""
Unit tests for Pydantic schemas.
"""

import pytest
from datetime import date, datetime, timedelta
from decimal import Decimal
from pydantic import ValidationError

from src.schemas.tour import TourCreate, TourUpdate, TourResponse
from src.schemas.concert import ConcertCreate, ConcertUpdate, ConcertResponse


class TestTourSchemas:
    """Test cases for Tour schemas."""
    
    def test_tour_create_valid(self):
        """Test valid tour creation schema."""
        tour_data = {
            "name": "World Tour 2024",
            "artist": "The Beatles",
            "start_date": "2024-06-01",
            "end_date": "2024-12-31",
            "description": "An amazing world tour"
        }
        tour = TourCreate(**tour_data)
        assert tour.name == "World Tour 2024"
        assert tour.artist == "The Beatles"
        assert tour.start_date == date(2024, 6, 1)
        assert tour.end_date == date(2024, 12, 31)
        assert tour.description == "An amazing world tour"
    
    def test_tour_create_without_description(self):
        """Test tour creation without optional description."""
        tour_data = {
            "name": "World Tour 2024",
            "artist": "The Beatles",
            "start_date": "2024-06-01",
            "end_date": "2024-12-31"
        }
        tour = TourCreate(**tour_data)
        assert tour.description is None
    
    def test_tour_create_end_date_before_start_date(self):
        """Test validation error when end_date is before start_date."""
        tour_data = {
            "name": "World Tour 2024",
            "artist": "The Beatles",
            "start_date": "2024-12-31",
            "end_date": "2024-06-01"
        }
        with pytest.raises(ValidationError) as exc_info:
            TourCreate(**tour_data)
        assert "end_date must be after or equal to start_date" in str(exc_info.value)
    
    def test_tour_create_empty_name(self):
        """Test validation error for empty name."""
        tour_data = {
            "name": "",
            "artist": "The Beatles",
            "start_date": "2024-06-01",
            "end_date": "2024-12-31"
        }
        with pytest.raises(ValidationError):
            TourCreate(**tour_data)
    
    def test_tour_update_partial(self):
        """Test partial tour update schema."""
        update_data = {
            "name": "Updated Tour Name"
        }
        tour_update = TourUpdate(**update_data)
        assert tour_update.name == "Updated Tour Name"
        assert tour_update.artist is None
    
    def test_tour_response(self):
        """Test tour response schema."""
        tour_data = {
            "id": 1,
            "name": "World Tour 2024",
            "artist": "The Beatles",
            "start_date": date(2024, 6, 1),
            "end_date": date(2024, 12, 31),
            "description": "An amazing world tour"
        }
        tour_response = TourResponse(**tour_data)
        assert tour_response.id == 1
        assert tour_response.name == "World Tour 2024"


class TestConcertSchemas:
    """Test cases for Concert schemas."""
    
    def test_concert_create_valid(self):
        """Test valid concert creation schema."""
        future_date = datetime.now() + timedelta(days=30)
        concert_data = {
            "tour_id": 1,
            "venue": "Madison Square Garden",
            "city": "New York",
            "country": "USA",
            "date_time": future_date,
            "ticket_price": "150.00",
            "capacity": 20000
        }
        concert = ConcertCreate(**concert_data)
        assert concert.tour_id == 1
        assert concert.venue == "Madison Square Garden"
        assert concert.ticket_price == Decimal("150.00")
        assert concert.capacity == 20000
    
    def test_concert_create_without_optional_fields(self):
        """Test concert creation without optional fields."""
        future_date = datetime.now() + timedelta(days=30)
        concert_data = {
            "tour_id": 1,
            "venue": "Madison Square Garden",
            "city": "New York",
            "country": "USA",
            "date_time": future_date
        }
        concert = ConcertCreate(**concert_data)
        assert concert.ticket_price is None
        assert concert.capacity is None
    
    def test_concert_create_past_date(self):
        """Test validation error for past concert date."""
        past_date = datetime.now() - timedelta(days=1)
        concert_data = {
            "tour_id": 1,
            "venue": "Madison Square Garden",
            "city": "New York",
            "country": "USA",
            "date_time": past_date
        }
        with pytest.raises(ValidationError) as exc_info:
            ConcertCreate(**concert_data)
        assert "Concert date must be in the future" in str(exc_info.value)
    
    def test_concert_create_negative_price(self):
        """Test validation error for negative ticket price."""
        future_date = datetime.now() + timedelta(days=30)
        concert_data = {
            "tour_id": 1,
            "venue": "Madison Square Garden",
            "city": "New York",
            "country": "USA",
            "date_time": future_date,
            "ticket_price": "-50.00"
        }
        with pytest.raises(ValidationError):
            ConcertCreate(**concert_data)
    
    def test_concert_create_invalid_tour_id(self):
        """Test validation error for invalid tour_id."""
        future_date = datetime.now() + timedelta(days=30)
        concert_data = {
            "tour_id": 0,
            "venue": "Madison Square Garden",
            "city": "New York",
            "country": "USA",
            "date_time": future_date
        }
        with pytest.raises(ValidationError):
            ConcertCreate(**concert_data)
    
    def test_concert_update_partial(self):
        """Test partial concert update schema."""
        update_data = {
            "venue": "Updated Venue",
            "ticket_price": "175.00"
        }
        concert_update = ConcertUpdate(**update_data)
        assert concert_update.venue == "Updated Venue"
        assert concert_update.ticket_price == Decimal("175.00")
        assert concert_update.city is None
    
    def test_concert_response(self):
        """Test concert response schema."""
        concert_data = {
            "id": 1,
            "tour_id": 1,
            "venue": "Madison Square Garden",
            "city": "New York",
            "country": "USA",
            "date_time": datetime(2024, 7, 15, 20, 0, 0),
            "ticket_price": Decimal("150.00"),
            "capacity": 20000
        }
        concert_response = ConcertResponse(**concert_data)
        assert concert_response.id == 1
        assert concert_response.tour_id == 1
        assert concert_response.venue == "Madison Square Garden"
