"""Tests for venue schemas."""

import pytest
from datetime import datetime
from pydantic import ValidationError
from src.schemas.venue import VenueCreate, VenueUpdate, VenueResponse, VenueListResponse


class TestVenueCreate:
    """Tests for VenueCreate schema."""
    
    def test_valid_venue_create(self):
        """Test creating a valid venue."""
        venue_data = {
            "name": "Test Venue",
            "address": "123 Test St",
            "city": "Test City",
            "state": "NY",
            "zip_code": "12345",
            "capacity": 1000,
            "phone_number": "+1-555-0123",
            "email": "test@venue.com",
            "website": "https://testvenue.com"
        }
        venue = VenueCreate(**venue_data)
        assert venue.name == "Test Venue"
        assert venue.capacity == 1000
        assert venue.email == "test@venue.com"
    
    def test_venue_create_required_fields(self):
        """Test that required fields are validated."""
        with pytest.raises(ValidationError):
            VenueCreate()
    
    def test_venue_create_invalid_capacity(self):
        """Test validation of negative capacity."""
        venue_data = {
            "name": "Test Venue",
            "address": "123 Test St",
            "city": "Test City", 
            "state": "NY",
            "zip_code": "12345",
            "capacity": -100
        }
        with pytest.raises(ValidationError) as exc_info:
            VenueCreate(**venue_data)
        assert "Venue capacity must be positive" in str(exc_info.value)
    
    def test_venue_create_zero_capacity(self):
        """Test validation of zero capacity."""
        venue_data = {
            "name": "Test Venue",
            "address": "123 Test St", 
            "city": "Test City",
            "state": "NY",
            "zip_code": "12345",
            "capacity": 0
        }
        with pytest.raises(ValidationError) as exc_info:
            VenueCreate(**venue_data)
        assert "Venue capacity must be positive" in str(exc_info.value)
    
    def test_venue_create_invalid_email(self):
        """Test validation of invalid email."""
        venue_data = {
            "name": "Test Venue",
            "address": "123 Test St",
            "city": "Test City",
            "state": "NY", 
            "zip_code": "12345",
            "capacity": 1000,
            "email": "invalid-email"
        }
        with pytest.raises(ValidationError):
            VenueCreate(**venue_data)
    
    def test_venue_create_invalid_zip_code(self):
        """Test validation of invalid zip code."""
        venue_data = {
            "name": "Test Venue",
            "address": "123 Test St",
            "city": "Test City",
            "state": "NY",
            "zip_code": "ABCDE",
            "capacity": 1000
        }
        with pytest.raises(ValidationError) as exc_info:
            VenueCreate(**venue_data)
        assert "Zip code must contain only digits and hyphens" in str(exc_info.value)
    
    def test_venue_create_valid_zip_with_hyphen(self):
        """Test validation of zip code with hyphen."""
        venue_data = {
            "name": "Test Venue", 
            "address": "123 Test St",
            "city": "Test City",
            "state": "NY",
            "zip_code": "12345-6789",
            "capacity": 1000
        }
        venue = VenueCreate(**venue_data)
        assert venue.zip_code == "12345-6789"
    
    def test_venue_create_optional_fields(self):
        """Test that optional fields can be None."""
        venue_data = {
            "name": "Test Venue",
            "address": "123 Test St",
            "city": "Test City",
            "state": "NY",
            "zip_code": "12345",
            "capacity": 1000
        }
        venue = VenueCreate(**venue_data)
        assert venue.phone_number is None
        assert venue.email is None
        assert venue.website is None


class TestVenueUpdate:
    """Tests for VenueUpdate schema."""
    
    def test_venue_update_all_fields_optional(self):
        """Test that all fields are optional in update schema."""
        venue = VenueUpdate()
        assert venue.name is None
        assert venue.capacity is None
    
    def test_venue_update_partial(self):
        """Test partial update with some fields."""
        venue_data = {
            "name": "Updated Name",
            "capacity": 2000
        }
        venue = VenueUpdate(**venue_data)
        assert venue.name == "Updated Name"
        assert venue.capacity == 2000
        assert venue.address is None
    
    def test_venue_update_invalid_capacity(self):
        """Test validation of negative capacity in update."""
        with pytest.raises(ValidationError) as exc_info:
            VenueUpdate(capacity=-100)
        assert "Venue capacity must be positive" in str(exc_info.value)
    
    def test_venue_update_invalid_zip_code(self):
        """Test validation of invalid zip code in update."""
        with pytest.raises(ValidationError) as exc_info:
            VenueUpdate(zip_code="INVALID")
        assert "Zip code must contain only digits and hyphens" in str(exc_info.value)
    
    def test_venue_update_valid_email(self):
        """Test updating with valid email."""
        venue = VenueUpdate(email="updated@venue.com")
        assert venue.email == "updated@venue.com"


class TestVenueResponse:
    """Tests for VenueResponse schema."""
    
    def test_venue_response_from_dict(self):
        """Test creating response from dict."""
        venue_data = {
            "id": 1,
            "name": "Test Venue",
            "address": "123 Test St",
            "city": "Test City",
            "state": "NY",
            "zip_code": "12345",
            "capacity": 1000,
            "phone_number": "+1-555-0123",
            "email": "test@venue.com",
            "website": "https://testvenue.com",
            "created_at": datetime(2024, 1, 1),
            "updated_at": datetime(2024, 1, 1)
        }
        venue = VenueResponse(**venue_data)
        assert venue.id == 1
        assert venue.name == "Test Venue"
        assert isinstance(venue.created_at, datetime)


class TestVenueListResponse:
    """Tests for VenueListResponse schema."""
    
    def test_venue_list_response(self):
        """Test venue list response schema."""
        venue_data = {
            "id": 1,
            "name": "Test Venue",
            "address": "123 Test St", 
            "city": "Test City",
            "state": "NY",
            "zip_code": "12345",
            "capacity": 1000,
            "phone_number": None,
            "email": None,
            "website": None,
            "created_at": datetime(2024, 1, 1),
            "updated_at": datetime(2024, 1, 1)
        }
        venue_response = VenueResponse(**venue_data)
        
        list_data = {
            "venues": [venue_response],
            "total": 1,
            "page": 1,
            "per_page": 10,
            "pages": 1
        }
        venue_list = VenueListResponse(**list_data)
        assert len(venue_list.venues) == 1
        assert venue_list.total == 1
        assert venue_list.page == 1
    
    def test_venue_list_response_empty(self):
        """Test empty venue list response."""
        list_data = {
            "venues": [],
            "total": 0,
            "page": 1,
            "per_page": 10,
            "pages": 0
        }
        venue_list = VenueListResponse(**list_data)
        assert len(venue_list.venues) == 0
        assert venue_list.total == 0


class TestVenueSchemaImports:
    """Tests for venue schema imports."""
    
    def test_can_import_schemas(self):
        """Test that venue schemas can be imported."""
        from src.schemas import (
            VenueCreate, 
            VenueUpdate, 
            VenueResponse, 
            VenueListResponse
        )
        
        # Test instantiation works
        venue_create_data = {
            "name": "Test Venue",
            "address": "123 Test St",
            "city": "Test City", 
            "state": "NY",
            "zip_code": "12345",
            "capacity": 1000
        }
        venue_create = VenueCreate(**venue_create_data)
        assert venue_create.name == "Test Venue"
        
        venue_update = VenueUpdate(name="Updated Name")
        assert venue_update.name == "Updated Name"
        
        venue_response_data = {
            **venue_create_data,
            "id": 1,
            "phone_number": None,
            "email": None,
            "website": None,
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        }
        venue_response = VenueResponse(**venue_response_data)
        assert venue_response.id == 1
        
        venue_list = VenueListResponse(
            venues=[venue_response],
            total=1,
            page=1, 
            per_page=10,
            pages=1
        )
        assert len(venue_list.venues) == 1
