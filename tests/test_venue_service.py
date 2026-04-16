import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.models import Base, Venue
from src.services import venue_service


@pytest.fixture
def db_session():
    """Create a test database session."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    yield session
    session.close()


@pytest.fixture
def sample_venue_data():
    """Sample venue data for testing."""
    return {
        "name": "Madison Square Garden",
        "city": "New York",
        "country": "USA",
        "capacity": 20000,
        "address": "4 Pennsylvania Plaza"
    }


@pytest.fixture
def sample_venues(db_session):
    """Create sample venues for testing."""
    venues_data = [
        {
            "name": "Madison Square Garden",
            "city": "New York",
            "country": "USA",
            "capacity": 20000,
            "address": "4 Pennsylvania Plaza"
        },
        {
            "name": "Wembley Stadium",
            "city": "London",
            "country": "UK",
            "capacity": 90000,
            "address": "Wembley, London"
        },
        {
            "name": "Central Park",
            "city": "New York",
            "country": "USA",
            "capacity": 50000,
            "address": "Central Park, NYC"
        }
    ]
    
    venues = []
    for venue_data in venues_data:
        venue = venue_service.create_venue(db_session, venue_data)
        venues.append(venue)
    
    return venues


class TestCreateVenue:
    def test_create_venue_success(self, db_session, sample_venue_data):
        venue = venue_service.create_venue(db_session, sample_venue_data)
        
        assert venue.id is not None
        assert venue.name == sample_venue_data["name"]
        assert venue.city == sample_venue_data["city"]
        assert venue.country == sample_venue_data["country"]
        assert venue.capacity == sample_venue_data["capacity"]
        assert venue.address == sample_venue_data["address"]


class TestGetVenue:
    def test_get_venue_exists(self, db_session, sample_venues):
        venue = sample_venues[0]
        retrieved_venue = venue_service.get_venue(db_session, venue.id)
        
        assert retrieved_venue is not None
        assert retrieved_venue.id == venue.id
        assert retrieved_venue.name == venue.name
    
    def test_get_venue_not_exists(self, db_session):
        venue = venue_service.get_venue(db_session, 999)
        assert venue is None


class TestGetVenues:
    def test_get_all_venues(self, db_session, sample_venues):
        venues = venue_service.get_venues(db_session)
        assert len(venues) == 3
    
    def test_get_venues_with_pagination(self, db_session, sample_venues):
        # Test limit
        venues = venue_service.get_venues(db_session, limit=2)
        assert len(venues) == 2
        
        # Test offset
        venues = venue_service.get_venues(db_session, limit=2, offset=1)
        assert len(venues) == 2
    
    def test_search_venues_by_name(self, db_session, sample_venues):
        venues = venue_service.get_venues(db_session, search_query="garden")
        assert len(venues) == 1
        assert "Garden" in venues[0].name
        
        # Test case insensitive search
        venues = venue_service.get_venues(db_session, search_query="GARDEN")
        assert len(venues) == 1
    
    def test_filter_venues_by_city(self, db_session, sample_venues):
        venues = venue_service.get_venues(db_session, city_filter="New York")
        assert len(venues) == 2
        for venue in venues:
            assert venue.city == "New York"
        
        # Test partial city match
        venues = venue_service.get_venues(db_session, city_filter="York")
        assert len(venues) == 2
    
    def test_filter_venues_by_country(self, db_session, sample_venues):
        venues = venue_service.get_venues(db_session, country_filter="USA")
        assert len(venues) == 2
        for venue in venues:
            assert venue.country == "USA"
    
    def test_combined_filters(self, db_session, sample_venues):
        venues = venue_service.get_venues(
            db_session,
            city_filter="New York",
            search_query="park"
        )
        assert len(venues) == 1
        assert "Park" in venues[0].name
        assert venues[0].city == "New York"


class TestUpdateVenue:
    def test_update_venue_success(self, db_session, sample_venues):
        venue = sample_venues[0]
        update_data = {"name": "Updated Garden", "capacity": 25000}
        
        updated_venue = venue_service.update_venue(db_session, venue.id, update_data)
        
        assert updated_venue is not None
        assert updated_venue.name == "Updated Garden"
        assert updated_venue.capacity == 25000
        assert updated_venue.city == venue.city  # Unchanged field
    
    def test_update_venue_not_exists(self, db_session):
        update_data = {"name": "Non-existent Venue"}
        updated_venue = venue_service.update_venue(db_session, 999, update_data)
        assert updated_venue is None
    
    def test_update_venue_partial_data(self, db_session, sample_venues):
        venue = sample_venues[0]
        original_name = venue.name
        update_data = {"capacity": 15000}
        
        updated_venue = venue_service.update_venue(db_session, venue.id, update_data)
        
        assert updated_venue.capacity == 15000
        assert updated_venue.name == original_name  # Unchanged


class TestDeleteVenue:
    def test_delete_venue_success(self, db_session, sample_venues):
        venue = sample_venues[0]
        venue_id = venue.id
        
        result = venue_service.delete_venue(db_session, venue_id)
        assert result is True
        
        # Verify venue is deleted
        deleted_venue = venue_service.get_venue(db_session, venue_id)
        assert deleted_venue is None
    
    def test_delete_venue_not_exists(self, db_session):
        result = venue_service.delete_venue(db_session, 999)
        assert result is False
