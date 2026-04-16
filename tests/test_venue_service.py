"""Tests for venue service layer."""

import pytest
from unittest.mock import Mock, patch
from sqlalchemy.exc import SQLAlchemyError

from src.services.venue_service import (
    create_venue,
    get_venue_by_id,
    update_venue,
    delete_venue,
    list_venues,
    VenueServiceError
)
from src.models import Venue


@pytest.fixture
def sample_venue_data():
    """Sample venue data for testing."""
    return {
        "name": "Test Arena",
        "city": "Test City",
        "country": "Test Country",
        "capacity": 10000,
        "address": "123 Test St"
    }


@pytest.fixture
def sample_venue():
    """Sample venue object for testing."""
    venue = Mock(spec=Venue)
    venue.id = 1
    venue.name = "Test Arena"
    venue.city = "Test City"
    venue.country = "Test Country"
    venue.capacity = 10000
    venue.address = "123 Test St"
    return venue


class TestCreateVenue:
    """Tests for create_venue function."""
    
    @patch('src.services.venue_service.get_db')
    def test_create_venue_success(self, mock_get_db, sample_venue_data, sample_venue):
        """Test successful venue creation."""
        # Setup mock
        mock_db = Mock()
        mock_get_db.return_value = iter([mock_db])
        
        # Mock venue creation
        with patch('src.services.venue_service.Venue') as mock_venue_class:
            mock_venue_class.return_value = sample_venue
            
            result = create_venue(sample_venue_data)
            
            # Verify calls
            mock_venue_class.assert_called_once_with(**sample_venue_data)
            mock_db.add.assert_called_once_with(sample_venue)
            mock_db.commit.assert_called_once()
            mock_db.refresh.assert_called_once_with(sample_venue)
            mock_db.close.assert_called_once()
            
            assert result == sample_venue
    
    @patch('src.services.venue_service.get_db')
    def test_create_venue_database_error(self, mock_get_db, sample_venue_data):
        """Test venue creation with database error."""
        # Setup mock
        mock_db = Mock()
        mock_get_db.return_value = iter([mock_db])
        mock_db.commit.side_effect = SQLAlchemyError("Database error")
        
        with patch('src.services.venue_service.Venue'):
            with pytest.raises(VenueServiceError, match="Failed to create venue"):
                create_venue(sample_venue_data)
            
            mock_db.rollback.assert_called_once()
            mock_db.close.assert_called_once()


class TestGetVenueById:
    """Tests for get_venue_by_id function."""
    
    @patch('src.services.venue_service.get_db')
    def test_get_venue_by_id_success(self, mock_get_db, sample_venue):
        """Test successful venue retrieval."""
        # Setup mock
        mock_db = Mock()
        mock_get_db.return_value = iter([mock_db])
        mock_db.query.return_value.filter.return_value.first.return_value = sample_venue
        
        result = get_venue_by_id(1)
        
        # Verify calls
        mock_db.query.assert_called_once_with(Venue)
        mock_db.close.assert_called_once()
        
        assert result == sample_venue
    
    @patch('src.services.venue_service.get_db')
    def test_get_venue_by_id_not_found(self, mock_get_db):
        """Test venue retrieval when not found."""
        # Setup mock
        mock_db = Mock()
        mock_get_db.return_value = iter([mock_db])
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        result = get_venue_by_id(999)
        
        assert result is None
        mock_db.close.assert_called_once()
    
    @patch('src.services.venue_service.get_db')
    def test_get_venue_by_id_database_error(self, mock_get_db):
        """Test venue retrieval with database error."""
        # Setup mock
        mock_db = Mock()
        mock_get_db.return_value = iter([mock_db])
        mock_db.query.side_effect = SQLAlchemyError("Database error")
        
        with pytest.raises(VenueServiceError, match="Failed to get venue"):
            get_venue_by_id(1)
        
        mock_db.close.assert_called_once()


class TestUpdateVenue:
    """Tests for update_venue function."""
    
    @patch('src.services.venue_service.get_db')
    def test_update_venue_success(self, mock_get_db, sample_venue):
        """Test successful venue update."""
        # Setup mock
        mock_db = Mock()
        mock_get_db.return_value = iter([mock_db])
        mock_db.query.return_value.filter.return_value.first.return_value = sample_venue
        
        update_data = {"name": "Updated Arena", "capacity": 15000}
        
        result = update_venue(1, update_data)
        
        # Verify calls
        mock_db.query.assert_called_once_with(Venue)
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once_with(sample_venue)
        mock_db.close.assert_called_once()
        
        assert result == sample_venue
    
    @patch('src.services.venue_service.get_db')
    def test_update_venue_not_found(self, mock_get_db):
        """Test venue update when not found."""
        # Setup mock
        mock_db = Mock()
        mock_get_db.return_value = iter([mock_db])
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        result = update_venue(999, {"name": "Updated"})
        
        assert result is None
        mock_db.close.assert_called_once()
    
    @patch('src.services.venue_service.get_db')
    def test_update_venue_database_error(self, mock_get_db, sample_venue):
        """Test venue update with database error."""
        # Setup mock
        mock_db = Mock()
        mock_get_db.return_value = iter([mock_db])
        mock_db.query.return_value.filter.return_value.first.return_value = sample_venue
        mock_db.commit.side_effect = SQLAlchemyError("Database error")
        
        with pytest.raises(VenueServiceError, match="Failed to update venue"):
            update_venue(1, {"name": "Updated"})
        
        mock_db.rollback.assert_called_once()
        mock_db.close.assert_called_once()


class TestDeleteVenue:
    """Tests for delete_venue function."""
    
    @patch('src.services.venue_service.get_db')
    def test_delete_venue_success(self, mock_get_db, sample_venue):
        """Test successful venue deletion."""
        # Setup mock
        mock_db = Mock()
        mock_get_db.return_value = iter([mock_db])
        mock_db.query.return_value.filter.return_value.first.return_value = sample_venue
        
        result = delete_venue(1)
        
        # Verify calls
        mock_db.query.assert_called_once_with(Venue)
        mock_db.delete.assert_called_once_with(sample_venue)
        mock_db.commit.assert_called_once()
        mock_db.close.assert_called_once()
        
        assert result is True
    
    @patch('src.services.venue_service.get_db')
    def test_delete_venue_not_found(self, mock_get_db):
        """Test venue deletion when not found."""
        # Setup mock
        mock_db = Mock()
        mock_get_db.return_value = iter([mock_db])
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        result = delete_venue(999)
        
        assert result is False
        mock_db.close.assert_called_once()
    
    @patch('src.services.venue_service.get_db')
    def test_delete_venue_database_error(self, mock_get_db, sample_venue):
        """Test venue deletion with database error."""
        # Setup mock
        mock_db = Mock()
        mock_get_db.return_value = iter([mock_db])
        mock_db.query.return_value.filter.return_value.first.return_value = sample_venue
        mock_db.commit.side_effect = SQLAlchemyError("Database error")
        
        with pytest.raises(VenueServiceError, match="Failed to delete venue"):
            delete_venue(1)
        
        mock_db.rollback.assert_called_once()
        mock_db.close.assert_called_once()


class TestListVenues:
    """Tests for list_venues function."""
    
    @patch('src.services.venue_service.get_db')
    def test_list_venues_no_filters(self, mock_get_db):
        """Test listing all venues without filters."""
        # Setup mock
        mock_db = Mock()
        mock_get_db.return_value = iter([mock_db])
        expected_venues = [Mock(spec=Venue), Mock(spec=Venue)]
        mock_db.query.return_value.order_by.return_value.all.return_value = expected_venues
        
        result = list_venues()
        
        # Verify calls
        mock_db.query.assert_called_once_with(Venue)
        mock_db.close.assert_called_once()
        
        assert result == expected_venues
    
    @patch('src.services.venue_service.get_db')
    def test_list_venues_with_search_term(self, mock_get_db):
        """Test listing venues with search term."""
        # Setup mock
        mock_db = Mock()
        mock_get_db.return_value = iter([mock_db])
        expected_venues = [Mock(spec=Venue)]
        
        # Setup query chain
        mock_query = mock_db.query.return_value
        mock_filtered = mock_query.filter.return_value
        mock_filtered.order_by.return_value.all.return_value = expected_venues
        
        result = list_venues(search_term="arena")
        
        # Verify filter was called
        mock_query.filter.assert_called_once()
        mock_db.close.assert_called_once()
        
        assert result == expected_venues
    
    @patch('src.services.venue_service.get_db')
    def test_list_venues_with_city_filter(self, mock_get_db):
        """Test listing venues with city filter."""
        # Setup mock
        mock_db = Mock()
        mock_get_db.return_value = iter([mock_db])
        expected_venues = [Mock(spec=Venue)]
        
        # Setup query chain
        mock_query = mock_db.query.return_value
        mock_filtered = mock_query.filter.return_value
        mock_filtered.order_by.return_value.all.return_value = expected_venues
        
        result = list_venues(city_filter="New York")
        
        # Verify filter was called
        mock_query.filter.assert_called_once()
        mock_db.close.assert_called_once()
        
        assert result == expected_venues
    
    @patch('src.services.venue_service.get_db')
    def test_list_venues_with_min_capacity(self, mock_get_db):
        """Test listing venues with minimum capacity filter."""
        # Setup mock
        mock_db = Mock()
        mock_get_db.return_value = iter([mock_db])
        expected_venues = [Mock(spec=Venue)]
        
        # Setup query chain
        mock_query = mock_db.query.return_value
        mock_filtered = mock_query.filter.return_value
        mock_filtered.order_by.return_value.all.return_value = expected_venues
        
        result = list_venues(min_capacity=5000)
        
        # Verify filter was called
        mock_query.filter.assert_called_once()
        mock_db.close.assert_called_once()
        
        assert result == expected_venues
    
    @patch('src.services.venue_service.get_db')
    def test_list_venues_with_all_filters(self, mock_get_db):
        """Test listing venues with all filters applied."""
        # Setup mock
        mock_db = Mock()
        mock_get_db.return_value = iter([mock_db])
        expected_venues = [Mock(spec=Venue)]
        
        # Setup query chain - multiple filter calls
        mock_query = mock_db.query.return_value
        mock_filtered1 = mock_query.filter.return_value
        mock_filtered2 = mock_filtered1.filter.return_value
        mock_filtered3 = mock_filtered2.filter.return_value
        mock_filtered3.order_by.return_value.all.return_value = expected_venues
        
        result = list_venues(
            search_term="arena",
            city_filter="New York",
            min_capacity=5000
        )
        
        # Verify multiple filters were called
        assert mock_query.filter.call_count == 3
        mock_db.close.assert_called_once()
        
        assert result == expected_venues
    
    @patch('src.services.venue_service.get_db')
    def test_list_venues_database_error(self, mock_get_db):
        """Test listing venues with database error."""
        # Setup mock
        mock_db = Mock()
        mock_get_db.return_value = iter([mock_db])
        mock_db.query.side_effect = SQLAlchemyError("Database error")
        
        with pytest.raises(VenueServiceError, match="Failed to list venues"):
            list_venues()
        
        mock_db.close.assert_called_once()
