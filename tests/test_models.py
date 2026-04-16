import pytest
from datetime import date, time
from decimal import Decimal
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError

from models import Base, Tour, Concert, TourStatus


@pytest.fixture
def db_session():
    """Create a test database session."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


@pytest.fixture
def sample_tour(db_session):
    """Create a sample tour for testing."""
    tour = Tour(
        name="World Tour 2024",
        band_name="Test Band",
        start_date=date(2024, 1, 1),
        end_date=date(2024, 12, 31),
        status=TourStatus.PLANNING
    )
    db_session.add(tour)
    db_session.commit()
    return tour


class TestTourModel:
    def test_create_tour(self, db_session):
        """Test creating a tour with valid data."""
        tour = Tour(
            name="Summer Tour",
            band_name="Rock Band",
            start_date=date(2024, 6, 1),
            end_date=date(2024, 8, 31),
            status=TourStatus.ACTIVE
        )
        db_session.add(tour)
        db_session.commit()

        assert tour.id is not None
        assert tour.name == "Summer Tour"
        assert tour.band_name == "Rock Band"
        assert tour.status == TourStatus.ACTIVE

    def test_tour_default_status(self, db_session):
        """Test that tour status defaults to PLANNING."""
        tour = Tour(
            name="Default Status Tour",
            band_name="Test Band",
            start_date=date(2024, 1, 1),
            end_date=date(2024, 12, 31)
        )
        db_session.add(tour)
        db_session.commit()

        assert tour.status == TourStatus.PLANNING

    def test_tour_date_order_constraint(self, db_session):
        """Test that end_date must be after start_date."""
        tour = Tour(
            name="Invalid Date Tour",
            band_name="Test Band",
            start_date=date(2024, 12, 31),
            end_date=date(2024, 1, 1),  # End before start
            status=TourStatus.PLANNING
        )
        db_session.add(tour)
        
        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_tour_repr(self, sample_tour):
        """Test tour string representation."""
        expected = f"<Tour(id={sample_tour.id}, name='World Tour 2024', band='Test Band', status='planning')>"
        assert repr(sample_tour) == expected


class TestConcertModel:
    def test_create_concert(self, db_session, sample_tour):
        """Test creating a concert with valid data."""
        concert = Concert(
            tour_id=sample_tour.id,
            venue="Madison Square Garden",
            city="New York",
            country="USA",
            date=date(2024, 6, 15),
            time=time(20, 0),
            capacity=20000,
            ticket_price=Decimal("99.99")
        )
        db_session.add(concert)
        db_session.commit()

        assert concert.id is not None
        assert concert.tour_id == sample_tour.id
        assert concert.venue == "Madison Square Garden"
        assert concert.capacity == 20000
        assert concert.ticket_price == Decimal("99.99")

    def test_concert_capacity_constraint(self, db_session, sample_tour):
        """Test that capacity cannot be negative."""
        concert = Concert(
            tour_id=sample_tour.id,
            venue="Test Venue",
            city="Test City",
            country="Test Country",
            date=date(2024, 6, 15),
            time=time(20, 0),
            capacity=-100,  # Negative capacity
            ticket_price=Decimal("50.00")
        )
        db_session.add(concert)
        
        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_concert_ticket_price_constraint(self, db_session, sample_tour):
        """Test that ticket price must be positive."""
        concert = Concert(
            tour_id=sample_tour.id,
            venue="Test Venue",
            city="Test City",
            country="Test Country",
            date=date(2024, 6, 15),
            time=time(20, 0),
            capacity=1000,
            ticket_price=Decimal("0.00")  # Zero price
        )
        db_session.add(concert)
        
        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_concert_foreign_key_constraint(self, db_session):
        """Test that concert must reference a valid tour."""
        concert = Concert(
            tour_id=999,  # Non-existent tour
            venue="Test Venue",
            city="Test City",
            country="Test Country",
            date=date(2024, 6, 15),
            time=time(20, 0),
            capacity=1000,
            ticket_price=Decimal("50.00")
        )
        db_session.add(concert)
        
        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_concert_repr(self, db_session, sample_tour):
        """Test concert string representation."""
        concert = Concert(
            tour_id=sample_tour.id,
            venue="Test Venue",
            city="Test City",
            country="Test Country",
            date=date(2024, 6, 15),
            time=time(20, 0),
            capacity=1000,
            ticket_price=Decimal("50.00")
        )
        db_session.add(concert)
        db_session.commit()

        expected = f"<Concert(id={concert.id}, venue='Test Venue', city='Test City', date=2024-06-15)>"
        assert repr(concert) == expected


class TestRelationships:
    def test_tour_concerts_relationship(self, db_session, sample_tour):
        """Test the one-to-many relationship between Tour and Concert."""
        # Create concerts for the tour
        concert1 = Concert(
            tour_id=sample_tour.id,
            venue="Venue 1",
            city="City 1",
            country="Country 1",
            date=date(2024, 6, 15),
            time=time(20, 0),
            capacity=1000,
            ticket_price=Decimal("50.00")
        )
        concert2 = Concert(
            tour_id=sample_tour.id,
            venue="Venue 2",
            city="City 2",
            country="Country 2",
            date=date(2024, 7, 15),
            time=time(19, 30),
            capacity=1500,
            ticket_price=Decimal("75.00")
        )
        db_session.add_all([concert1, concert2])
        db_session.commit()

        # Refresh the tour to load the relationship
        db_session.refresh(sample_tour)

        assert len(sample_tour.concerts) == 2
        assert concert1 in sample_tour.concerts
        assert concert2 in sample_tour.concerts

    def test_concert_tour_relationship(self, db_session, sample_tour):
        """Test the many-to-one relationship from Concert to Tour."""
        concert = Concert(
            tour_id=sample_tour.id,
            venue="Test Venue",
            city="Test City",
            country="Test Country",
            date=date(2024, 6, 15),
            time=time(20, 0),
            capacity=1000,
            ticket_price=Decimal("50.00")
        )
        db_session.add(concert)
        db_session.commit()

        # Refresh the concert to load the relationship
        db_session.refresh(concert)

        assert concert.tour == sample_tour
        assert concert.tour.name == "World Tour 2024"

    def test_cascade_delete(self, db_session, sample_tour):
        """Test that deleting a tour cascades to delete its concerts."""
        # Create a concert for the tour
        concert = Concert(
            tour_id=sample_tour.id,
            venue="Test Venue",
            city="Test City",
            country="Test Country",
            date=date(2024, 6, 15),
            time=time(20, 0),
            capacity=1000,
            ticket_price=Decimal("50.00")
        )
        db_session.add(concert)
        db_session.commit()

        concert_id = concert.id

        # Delete the tour
        db_session.delete(sample_tour)
        db_session.commit()

        # Concert should be deleted too
        deleted_concert = db_session.get(Concert, concert_id)
        assert deleted_concert is None
