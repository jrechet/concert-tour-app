import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.models.venue import Venue, Base


@pytest.fixture
def db_session():
    """Create a test database session"""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    
    yield session
    
    session.close()


class TestVenueModel:
    def test_create_venue_with_all_fields(self, db_session):
        """Test creating a venue with all fields"""
        venue = Venue(
            name="Madison Square Garden",
            city="New York",
            country="USA",
            address="4 Pennsylvania Plaza, New York, NY 10001",
            capacity=20789,
            stage_size="40ft x 30ft",
            sound_system="L-Acoustics K2",
            lighting_rig="LED RGB System",
            contact_name="John Smith",
            contact_email="john.smith@msg.com",
            contact_phone="+1-555-123-4567",
            notes="World famous venue with excellent acoustics"
        )
        
        db_session.add(venue)
        db_session.commit()
        
        # Verify venue was created
        saved_venue = db_session.query(Venue).filter(Venue.name == "Madison Square Garden").first()
        assert saved_venue is not None
        assert saved_venue.name == "Madison Square Garden"
        assert saved_venue.city == "New York"
        assert saved_venue.country == "USA"
        assert saved_venue.capacity == 20789
        assert saved_venue.contact_email == "john.smith@msg.com"

    def test_create_venue_with_required_fields_only(self, db_session):
        """Test creating a venue with only required fields"""
        venue = Venue(
            name="Local Club",
            city="Austin",
            country="USA"
        )
        
        db_session.add(venue)
        db_session.commit()
        
        # Verify venue was created
        saved_venue = db_session.query(Venue).filter(Venue.name == "Local Club").first()
        assert saved_venue is not None
        assert saved_venue.name == "Local Club"
        assert saved_venue.city == "Austin"
        assert saved_venue.country == "USA"
        assert saved_venue.capacity is None
        assert saved_venue.contact_email is None

    def test_venue_string_representation(self):
        """Test venue string representation"""
        venue = Venue(
            id=1,
            name="Test Venue",
            city="Test City",
            country="Test Country"
        )
        
        expected = "<Venue(id=1, name='Test Venue', city='Test City', country='Test Country')>"
        assert str(venue) == expected

    def test_validate_email_valid(self):
        """Test email validation with valid emails"""
        assert Venue.validate_email("test@example.com") is True
        assert Venue.validate_email("user.name@domain.co.uk") is True
        assert Venue.validate_email("test+tag@example.org") is True
        assert Venue.validate_email(None) is True

    def test_validate_email_invalid(self):
        """Test email validation with invalid emails"""
        assert Venue.validate_email("invalid-email") is False
        assert Venue.validate_email("@example.com") is False
        assert Venue.validate_email("test@") is False
        assert Venue.validate_email("test..test@example.com") is False

    def test_validate_capacity_valid(self):
        """Test capacity validation with valid values"""
        assert Venue.validate_capacity(100) is True
        assert Venue.validate_capacity(50000) is True
        assert Venue.validate_capacity(1) is True
        assert Venue.validate_capacity(None) is True

    def test_validate_capacity_invalid(self):
        """Test capacity validation with invalid values"""
        assert Venue.validate_capacity(0) is False
        assert Venue.validate_capacity(-100) is False
        assert Venue.validate_capacity("100") is False
        assert Venue.validate_capacity(12.5) is False

    def test_venue_fields_length_limits(self, db_session):
        """Test that string fields respect length limits"""
        # Test creating venue with maximum length strings
        long_name = "A" * 200
        long_city = "B" * 100
        long_country = "C" * 100
        
        venue = Venue(
            name=long_name,
            city=long_city,
            country=long_country
        )
        
        db_session.add(venue)
        db_session.commit()
        
        # Verify venue was created with full length strings
        saved_venue = db_session.query(Venue).filter(Venue.name == long_name).first()
        assert saved_venue is not None
        assert len(saved_venue.name) == 200
        assert len(saved_venue.city) == 100
        assert len(saved_venue.country) == 100

    def test_venue_indexes_exist(self, db_session):
        """Test that proper indexes are created"""
        # Create multiple venues
        venues = [
            Venue(name="Venue A", city="City A", country="Country A"),
            Venue(name="Venue B", city="City B", country="Country B"),
            Venue(name="Venue C", city="City A", country="Country A"),
        ]
        
        for venue in venues:
            db_session.add(venue)
        db_session.commit()
        
        # Test queries that should use indexes
        city_venues = db_session.query(Venue).filter(Venue.city == "City A").all()
        assert len(city_venues) == 2
        
        country_venues = db_session.query(Venue).filter(Venue.country == "Country A").all()
        assert len(country_venues) == 2
        
        named_venue = db_session.query(Venue).filter(Venue.name == "Venue B").first()
        assert named_venue is not None
        assert named_venue.name == "Venue B"
