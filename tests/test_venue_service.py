"""
Unit tests for venue service functionality.
"""
import pytest
from unittest.mock import Mock, patch
from datetime import datetime

from src.services.venue_service import VenueService
from src.models import Venue
from src.exceptions import VenueNotFoundError, ValidationError


class TestVenueService:
    """Test cases for VenueService."""

    @pytest.fixture
    def mock_db(self):
        """Mock database session."""
        return Mock()

    @pytest.fixture
    def venue_service(self, mock_db):
        """Create venue service with mocked dependencies."""
        return VenueService(mock_db)

    @pytest.fixture
    def sample_venue_data(self):
        """Sample venue data for testing."""
        return {
            "name": "Madison Square Garden",
            "city": "New York",
            "state": "NY",
            "country": "USA",
            "address": "4 Pennsylvania Plaza",
            "capacity": 20000,
            "venue_type": "arena",
            "contact_email": "booking@msg.com",
            "contact_phone": "+1-212-465-6741"
        }

    @pytest.fixture
    def sample_venue(self, sample_venue_data):
        """Sample venue instance for testing."""
        venue = Venue(**sample_venue_data)
        venue.id = 1
        venue.created_at = datetime.utcnow()
        venue.updated_at = datetime.utcnow()
        return venue

    def test_create_venue_success(self, venue_service, mock_db, sample_venue_data):
        """Test successful venue creation."""
        # Mock the database operations
        mock_db.add = Mock()
        mock_db.commit = Mock()
        mock_db.refresh = Mock()
        
        # Mock the created venue
        created_venue = Venue(**sample_venue_data)
        created_venue.id = 1
        mock_db.refresh.side_effect = lambda x: setattr(x, 'id', 1)

        result = venue_service.create_venue(sample_venue_data)

        assert result.name == sample_venue_data["name"]
        assert result.city == sample_venue_data["city"]
        assert result.capacity == sample_venue_data["capacity"]
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

    def test_create_venue_invalid_data(self, venue_service, sample_venue_data):
        """Test venue creation with invalid data."""
        # Test with missing required field
        invalid_data = sample_venue_data.copy()
        del invalid_data["name"]
        
        with pytest.raises(ValidationError):
            venue_service.create_venue(invalid_data)

    def test_create_venue_invalid_capacity(self, venue_service, sample_venue_data):
        """Test venue creation with invalid capacity."""
        invalid_data = sample_venue_data.copy()
        invalid_data["capacity"] = -100
        
        with pytest.raises(ValidationError):
            venue_service.create_venue(invalid_data)

    def test_create_venue_invalid_email(self, venue_service, sample_venue_data):
        """Test venue creation with invalid email."""
        invalid_data = sample_venue_data.copy()
        invalid_data["contact_email"] = "invalid-email"
        
        with pytest.raises(ValidationError):
            venue_service.create_venue(invalid_data)

    def test_get_venue_by_id_success(self, venue_service, mock_db, sample_venue):
        """Test successful venue retrieval by ID."""
        mock_db.query().filter().first.return_value = sample_venue
        
        result = venue_service.get_venue_by_id(1)
        
        assert result == sample_venue
        mock_db.query.assert_called_with(Venue)

    def test_get_venue_by_id_not_found(self, venue_service, mock_db):
        """Test venue retrieval with non-existent ID."""
        mock_db.query().filter().first.return_value = None
        
        with pytest.raises(VenueNotFoundError):
            venue_service.get_venue_by_id(999)

    def test_get_venue_by_id_invalid_id(self, venue_service):
        """Test venue retrieval with invalid ID."""
        with pytest.raises(ValidationError):
            venue_service.get_venue_by_id("invalid")
        
        with pytest.raises(ValidationError):
            venue_service.get_venue_by_id(-1)

    def test_update_venue_success(self, venue_service, mock_db, sample_venue):
        """Test successful venue update."""
        mock_db.query().filter().first.return_value = sample_venue
        mock_db.commit = Mock()
        
        update_data = {"name": "Updated Venue Name", "capacity": 25000}
        result = venue_service.update_venue(1, update_data)
        
        assert result.name == "Updated Venue Name"
        assert result.capacity == 25000
        mock_db.commit.assert_called_once()

    def test_update_venue_not_found(self, venue_service, mock_db):
        """Test updating non-existent venue."""
        mock_db.query().filter().first.return_value = None
        
        with pytest.raises(VenueNotFoundError):
            venue_service.update_venue(999, {"name": "New Name"})

    def test_update_venue_invalid_data(self, venue_service, mock_db, sample_venue):
        """Test venue update with invalid data."""
        mock_db.query().filter().first.return_value = sample_venue
        
        with pytest.raises(ValidationError):
            venue_service.update_venue(1, {"capacity": -100})

    def test_delete_venue_success(self, venue_service, mock_db, sample_venue):
        """Test successful venue deletion."""
        mock_db.query().filter().first.return_value = sample_venue
        mock_db.delete = Mock()
        mock_db.commit = Mock()
        
        venue_service.delete_venue(1)
        
        mock_db.delete.assert_called_once_with(sample_venue)
        mock_db.commit.assert_called_once()

    def test_delete_venue_not_found(self, venue_service, mock_db):
        """Test deleting non-existent venue."""
        mock_db.query().filter().first.return_value = None
        
        with pytest.raises(VenueNotFoundError):
            venue_service.delete_venue(999)

    def test_search_venues_by_name(self, venue_service, mock_db, sample_venue):
        """Test venue search by name."""
        mock_db.query().filter().all.return_value = [sample_venue]
        
        results = venue_service.search_venues(name="Madison")
        
        assert len(results) == 1
        assert results[0] == sample_venue

    def test_search_venues_by_city(self, venue_service, mock_db, sample_venue):
        """Test venue search by city."""
        mock_db.query().filter().all.return_value = [sample_venue]
        
        results = venue_service.search_venues(city="New York")
        
        assert len(results) == 1
        assert results[0] == sample_venue

    def test_search_venues_by_capacity_range(self, venue_service, mock_db, sample_venue):
        """Test venue search by capacity range."""
        mock_db.query().filter().all.return_value = [sample_venue]
        
        results = venue_service.search_venues(min_capacity=15000, max_capacity=25000)
        
        assert len(results) == 1
        assert results[0] == sample_venue

    def test_search_venues_no_results(self, venue_service, mock_db):
        """Test venue search with no results."""
        mock_db.query().filter().all.return_value = []
        
        results = venue_service.search_venues(name="Nonexistent")
        
        assert len(results) == 0

    def test_search_venues_multiple_filters(self, venue_service, mock_db, sample_venue):
        """Test venue search with multiple filters."""
        mock_db.query().filter().all.return_value = [sample_venue]
        
        results = venue_service.search_venues(
            city="New York",
            venue_type="arena",
            min_capacity=10000
        )
        
        assert len(results) == 1
        assert results[0] == sample_venue

    def test_list_venues_with_pagination(self, venue_service, mock_db, sample_venue):
        """Test venue listing with pagination."""
        mock_query = Mock()
        mock_query.offset().limit().all.return_value = [sample_venue]
        mock_db.query.return_value = mock_query
        
        results = venue_service.list_venues(page=1, per_page=10)
        
        assert len(results) == 1
        mock_query.offset.assert_called_with(0)
        mock_query.offset().limit.assert_called_with(10)

    def test_list_venues_invalid_pagination(self, venue_service):
        """Test venue listing with invalid pagination parameters."""
        with pytest.raises(ValidationError):
            venue_service.list_venues(page=0, per_page=10)
        
        with pytest.raises(ValidationError):
            venue_service.list_venues(page=1, per_page=0)

    def test_get_venues_by_location(self, venue_service, mock_db, sample_venue):
        """Test getting venues by location."""
        mock_db.query().filter().all.return_value = [sample_venue]
        
        results = venue_service.get_venues_by_location("New York", "NY")
        
        assert len(results) == 1
        assert results[0] == sample_venue

    def test_get_venues_by_type(self, venue_service, mock_db, sample_venue):
        """Test getting venues by type."""
        mock_db.query().filter().all.return_value = [sample_venue]
        
        results = venue_service.get_venues_by_type("arena")
        
        assert len(results) == 1
        assert results[0] == sample_venue

    @patch('src.services.venue_service.datetime')
    def test_venue_timestamps(self, mock_datetime, venue_service, mock_db, sample_venue_data):
        """Test that venue timestamps are set correctly."""
        now = datetime(2023, 1, 1, 12, 0, 0)
        mock_datetime.utcnow.return_value = now
        
        mock_db.add = Mock()
        mock_db.commit = Mock()
        mock_db.refresh = Mock()
        
        venue_service.create_venue(sample_venue_data)
        
        # Verify that created_at and updated_at are set
        call_args = mock_db.add.call_args[0][0]
        assert hasattr(call_args, 'created_at')
        assert hasattr(call_args, 'updated_at')

    def test_validate_venue_data_success(self, venue_service, sample_venue_data):
        """Test successful venue data validation."""
        # This should not raise an exception
        venue_service._validate_venue_data(sample_venue_data)

    def test_validate_venue_data_missing_required(self, venue_service):
        """Test venue data validation with missing required fields."""
        with pytest.raises(ValidationError):
            venue_service._validate_venue_data({})

    def test_validate_venue_data_invalid_types(self, venue_service, sample_venue_data):
        """Test venue data validation with invalid data types."""
        invalid_data = sample_venue_data.copy()
        invalid_data["capacity"] = "not_a_number"
        
        with pytest.raises(ValidationError):
            venue_service._validate_venue_data(invalid_data)

    def test_venue_capacity_boundary_conditions(self, venue_service, sample_venue_data):
        """Test venue capacity boundary conditions."""
        # Test minimum capacity
        data = sample_venue_data.copy()
        data["capacity"] = 1
        venue_service._validate_venue_data(data)  # Should not raise
        
        # Test zero capacity
        data["capacity"] = 0
        with pytest.raises(ValidationError):
            venue_service._validate_venue_data(data)
        
        # Test very large capacity
        data["capacity"] = 1000000
        venue_service._validate_venue_data(data)  # Should not raise

    def test_venue_name_length_validation(self, venue_service, sample_venue_data):
        """Test venue name length validation."""
        # Test empty name
        data = sample_venue_data.copy()
        data["name"] = ""
        with pytest.raises(ValidationError):
            venue_service._validate_venue_data(data)
        
        # Test very long name
        data["name"] = "x" * 1000
        with pytest.raises(ValidationError):
            venue_service._validate_venue_data(data)
