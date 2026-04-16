import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.models.venue import Venue, Base


class TestVenueModel:
    """Test cases for the Venue model."""
    
    @pytest.fixture
    def engine(self):
        """Create an in-memory SQLite database for testing."""
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)
        return engine
    
    @pytest.fixture
    def session(self, engine):
        """Create a database session for testing."""
        Session = sessionmaker(bind=engine)
        session = Session()
        yield session
        session.close()
    
    def test_venue_creation_with_valid_data(self, session):
        """Test creating a venue with valid data."""
        venue_data = {
            'name': 'Madison Square Garden',
            'city': 'New York',
            'country': 'USA',
            'address': '4 Pennsylvania Plaza, New York, NY 10001',
            'capacity': 20000,
            'stage_size': '60ft x 40ft',
            'sound_system': 'Meyer Sound LEOPARD',
            'lighting_rig': 'Martin MAC Viper Performance',
            'contact_name': 'John Doe',
            'contact_email': 'john.doe@msg.com',
            'contact_phone': '+1-212-465-6741',
            'notes': 'Famous arena in Manhattan'
        }
        
        venue = Venue(**venue_data)
        session.add(venue)
        session.commit()
        
        assert venue.id is not None
        assert venue.name == 'Madison Square Garden'
        assert venue.city == 'New York'
        assert venue.country == 'USA'
        assert venue.capacity == 20000
        assert venue.contact_email == 'john.doe@msg.com'
        assert venue.created_at is not None
        assert venue.updated_at is not None
    
    def test_venue_creation_with_negative_capacity_raises_error(self):
        """Test that creating a venue with negative capacity raises ValueError."""
        venue_data = {
            'name': 'Test Venue',
            'city': 'Test City',
            'country': 'Test Country',
            'address': 'Test Address',
            'capacity': -100,  # Invalid negative capacity
            'stage_size': '30ft x 20ft',
            'sound_system': 'Basic Sound',
            'lighting_rig': 'Basic Lighting',
            'contact_name': 'Test Contact',
            'contact_email': 'test@example.com',
            'contact_phone': '+1-555-0123'
        }
        
        with pytest.raises(ValueError, match="Capacity must be a positive integer"):
            Venue(**venue_data)
    
    def test_venue_creation_with_zero_capacity_raises_error(self):
        """Test that creating a venue with zero capacity raises ValueError."""
        venue_data = {
            'name': 'Test Venue',
            'city': 'Test City',
            'country': 'Test Country',
            'address': 'Test Address',
            'capacity': 0,  # Invalid zero capacity
            'stage_size': '30ft x 20ft',
            'sound_system': 'Basic Sound',
            'lighting_rig': 'Basic Lighting',
            'contact_name': 'Test Contact',
            'contact_email': 'test@example.com',
            'contact_phone': '+1-555-0123'
        }
        
        with pytest.raises(ValueError, match="Capacity must be a positive integer"):
            Venue(**venue_data)
    
    def test_venue_creation_with_invalid_email_raises_error(self):
        """Test that creating a venue with invalid email raises ValueError."""
        venue_data = {
            'name': 'Test Venue',
            'city': 'Test City',
            'country': 'Test Country',
            'address': 'Test Address',
            'capacity': 1000,
            'stage_size': '30ft x 20ft',
            'sound_system': 'Basic Sound',
            'lighting_rig': 'Basic Lighting',
            'contact_name': 'Test Contact',
            'contact_email': 'invalid-email',  # Invalid email format
            'contact_phone': '+1-555-0123'
        }
        
        with pytest.raises(ValueError, match="Invalid email format"):
            Venue(**venue_data)
    
    def test_venue_creation_without_notes_is_allowed(self, session):
        """Test that creating a venue without notes is allowed."""
        venue_data = {
            'name': 'Test Venue',
            'city': 'Test City',
            'country': 'Test Country',
            'address': 'Test Address',
            'capacity': 1000,
            'stage_size': '30ft x 20ft',
            'sound_system': 'Basic Sound',
            'lighting_rig': 'Basic Lighting',
            'contact_name': 'Test Contact',
            'contact_email': 'test@example.com',
            'contact_phone': '+1-555-0123'
            # notes field is optional
        }
        
        venue = Venue(**venue_data)
        session.add(venue)
        session.commit()
        
        assert venue.id is not None
        assert venue.notes is None
    
    def test_valid_email_validation(self):
        """Test the email validation method with valid emails."""
        valid_emails = [
            'test@example.com',
            'user.name@domain.co.uk',
            'user+tag@example.org',
            'user123@test-domain.com'
        ]
        
        for email in valid_emails:
            assert Venue._is_valid_email(email), f"Email {email} should be valid"
    
    def test_invalid_email_validation(self):
        """Test the email validation method with invalid emails."""
        invalid_emails = [
            'invalid-email',
            '@example.com',
            'user@',
            'user@.com',
            'user..name@example.com',
            'user@example',
            ''
        ]
        
        for email in invalid_emails:
            assert not Venue._is_valid_email(email), f"Email {email} should be invalid"
    
    def test_venue_repr(self, session):
        """Test the string representation of a venue."""
        venue_data = {
            'name': 'Test Arena',
            'city': 'Test City',
            'country': 'Test Country',
            'address': 'Test Address',
            'capacity': 5000,
            'stage_size': '40ft x 30ft',
            'sound_system': 'Test Sound',
            'lighting_rig': 'Test Lighting',
            'contact_name': 'Test Contact',
            'contact_email': 'test@example.com',
            'contact_phone': '+1-555-0123'
        }
        
        venue = Venue(**venue_data)
        session.add(venue)
        session.commit()
        
        expected_repr = f"<Venue(id={venue.id}, name='Test Arena', city='Test City', capacity=5000)>"
        assert repr(venue) == expected_repr
