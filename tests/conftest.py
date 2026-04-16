import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.database import Base, get_db
from src.models.models import Tour, Concert, Venue, TourStatus, ConcertStatus
from datetime import datetime, timedelta
from decimal import Decimal

# Use in-memory SQLite for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture
def db_session():
    """Create a fresh database session for each test"""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def sample_venue(db_session):
    """Create a sample venue for testing"""
    venue = Venue(
        name="Madison Square Garden",
        city="New York",
        country="USA",
        capacity=20000
    )
    db_session.add(venue)
    db_session.commit()
    db_session.refresh(venue)
    return venue


@pytest.fixture
def sample_tour(db_session):
    """Create a sample tour for testing"""
    tour = Tour(
        name="World Tour 2024",
        start_date=datetime.now() + timedelta(days=30),
        end_date=datetime.now() + timedelta(days=180),
        status=TourStatus.PLANNING
    )
    db_session.add(tour)
    db_session.commit()
    db_session.refresh(tour)
    return tour


@pytest.fixture
def sample_concert(db_session, sample_tour, sample_venue):
    """Create a sample concert for testing"""
    concert = Concert(
        tour_id=sample_tour.id,
        venue_id=sample_venue.id,
        date=datetime.now() + timedelta(days=45),
        capacity=sample_venue.capacity,
        ticket_price=Decimal("75.00"),
        status=ConcertStatus.SCHEDULED
    )
    db_session.add(concert)
    db_session.commit()
    db_session.refresh(concert)
    return concert
