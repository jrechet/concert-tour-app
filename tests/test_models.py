import pytest
from datetime import date, time
from decimal import Decimal
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.database import Base
from src.models import Tour, Concert


@pytest.fixture
def db_session():
    """Create a test database session"""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()
    yield session
    session.close()


def test_tour_model(db_session):
    """Test Tour model creation and fields"""
    tour = Tour(
        name="Summer Stadium Tour 2024",
        band_name="The Rockers",
        start_date=date(2024, 6, 1),
        end_date=date(2024, 8, 31),
        status="planned"
    )
    
    db_session.add(tour)
    db_session.commit()
    db_session.refresh(tour)
    
    assert tour.id is not None
    assert tour.name == "Summer Stadium Tour 2024"
    assert tour.band_name == "The Rockers"
    assert tour.start_date == date(2024, 6, 1)
    assert tour.end_date == date(2024, 8, 31)
    assert tour.status == "planned"


def test_concert_model(db_session):
    """Test Concert model creation and fields"""
    # Create a tour first
    tour = Tour(
        name="Test Tour",
        band_name="Test Band",
        start_date=date(2024, 6, 1),
        end_date=date(2024, 6, 30),
        status="planned"
    )
    db_session.add(tour)
    db_session.commit()
    db_session.refresh(tour)
    
    # Create a concert
    concert = Concert(
        tour_id=tour.id,
        venue="Madison Square Garden",
        city="New York",
        country="USA",
        date=date(2024, 6, 15),
        time=time(20, 0),
        capacity=20000,
        ticket_price=Decimal("75.00")
    )
    
    db_session.add(concert)
    db_session.commit()
    db_session.refresh(concert)
    
    assert concert.id is not None
    assert concert.tour_id == tour.id
    assert concert.venue == "Madison Square Garden"
    assert concert.city == "New York"
    assert concert.country == "USA"
    assert concert.date == date(2024, 6, 15)
    assert concert.time == time(20, 0)
    assert concert.capacity == 20000
    assert concert.ticket_price == Decimal("75.00")


def test_tour_concert_relationship(db_session):
    """Test the relationship between Tour and Concert models"""
    # Create a tour
    tour = Tour(
        name="Relationship Test Tour",
        band_name="Test Band",
        start_date=date(2024, 6, 1),
        end_date=date(2024, 6, 30),
        status="planned"
    )
    db_session.add(tour)
    db_session.commit()
    db_session.refresh(tour)
    
    # Create concerts for the tour
    concert1 = Concert(
        tour_id=tour.id,
        venue="Venue 1",
        city="City 1",
        country="Country 1",
        date=date(2024, 6, 10),
        time=time(20, 0),
        capacity=10000,
        ticket_price=Decimal("50.00")
    )
    
    concert2 = Concert(
        tour_id=tour.id,
        venue="Venue 2",
        city="City 2",
        country="Country 2",
        date=date(2024, 6, 20),
        time=time(19, 30),
        capacity=15000,
        ticket_price=Decimal("60.00")
    )
    
    db_session.add_all([concert1, concert2])
    db_session.commit()
    
    # Test relationship from tour to concerts
    assert len(tour.concerts) == 2
    assert concert1 in tour.concerts
    assert concert2 in tour.concerts
    
    # Test relationship from concert to tour
    assert concert1.tour == tour
    assert concert2.tour == tour
