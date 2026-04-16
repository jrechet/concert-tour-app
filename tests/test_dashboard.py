"""
Test fixtures and mock data for dashboard functionality testing.
"""
import pytest
from datetime import datetime, timedelta
from typing import List, Dict, Any
from unittest.mock import MagicMock

import pytest_asyncio
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from src.models import Base, Tour, Concert, Venue, TourStatus
from src.database import get_db


# Database fixtures
@pytest.fixture
def test_engine():
    """Create in-memory SQLite engine for testing."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    return engine


@pytest.fixture
def test_session(test_engine):
    """Create test database session with cleanup."""
    TestingSessionLocal = sessionmaker(
        autocommit=False, autoflush=False, bind=test_engine
    )
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def override_get_db(test_session):
    """Override dependency for database session."""
    def _override_get_db():
        try:
            yield test_session
        finally:
            test_session.close()
    return _override_get_db


# Helper functions for generating realistic test data
def create_venue_data(
    name: str = "Test Venue",
    city: str = "Test City",
    capacity: int = 5000,
    **kwargs
) -> Dict[str, Any]:
    """Generate realistic venue data."""
    return {
        "name": name,
        "city": city,
        "capacity": capacity,
        "address": kwargs.get("address", f"123 {name} St"),
        "state": kwargs.get("state", "CA"),
        "country": kwargs.get("country", "USA"),
        **kwargs
    }


def create_concert_data(
    venue_id: int,
    date: datetime,
    ticket_price: float = 75.0,
    **kwargs
) -> Dict[str, Any]:
    """Generate realistic concert data."""
    return {
        "venue_id": venue_id,
        "date": date,
        "ticket_price": ticket_price,
        "tickets_sold": kwargs.get("tickets_sold", 0),
        "total_tickets": kwargs.get("total_tickets", 5000),
        **kwargs
    }


def create_tour_data(
    name: str = "Test Tour",
    status: TourStatus = TourStatus.ACTIVE,
    **kwargs
) -> Dict[str, Any]:
    """Generate realistic tour data."""
    return {
        "name": name,
        "status": status,
        "start_date": kwargs.get("start_date", datetime.now()),
        "end_date": kwargs.get("end_date", datetime.now() + timedelta(days=30)),
        "description": kwargs.get("description", f"Description for {name}"),
        **kwargs
    }


# Mock data fixtures for various scenarios
@pytest.fixture
def sample_venues(test_session) -> List[Venue]:
    """Create sample venues for testing."""
    venues_data = [
        create_venue_data("Madison Square Garden", "New York", 20000, state="NY"),
        create_venue_data("The Forum", "Los Angeles", 17500),
        create_venue_data("United Center", "Chicago", 23500, state="IL"),
        create_venue_data("TD Garden", "Boston", 19580, state="MA"),
        create_venue_data("Staples Center", "Los Angeles", 21000),
        create_venue_data("Oracle Arena", "Oakland", 19596),
        create_venue_data("Barclays Center", "Brooklyn", 19000, state="NY"),
        create_venue_data("American Airlines Center", "Dallas", 20000, state="TX"),
        create_venue_data("Wells Fargo Center", "Philadelphia", 21600, state="PA"),
        create_venue_data("Pepsi Center", "Denver", 20000, state="CO"),
    ]
    
    venues = []
    for venue_data in venues_data:
        venue = Venue(**venue_data)
        test_session.add(venue)
        venues.append(venue)
    
    test_session.commit()
    return venues


@pytest.fixture
def comprehensive_tour_data(test_session, sample_venues) -> Tour:
    """Create tour with 10+ concerts across different time periods."""
    # Create tour
    tour_data = create_tour_data(
        "World Tour 2024",
        TourStatus.ACTIVE,
        start_date=datetime.now() - timedelta(days=30),
        end_date=datetime.now() + timedelta(days=60)
    )
    tour = Tour(**tour_data)
    test_session.add(tour)
    test_session.flush()  # Get the tour ID
    
    # Create concerts with varied dates and scenarios
    base_date = datetime.now()
    concert_scenarios = [
        # Past concerts (completed)
        (base_date - timedelta(days=30), 4500, 5000),  # Sold out past show
        (base_date - timedelta(days=25), 3200, 4000),  # Good sales
        (base_date - timedelta(days=20), 1800, 3500),  # Moderate sales
        (base_date - timedelta(days=15), 5000, 5000),  # Another sold out
        (base_date - timedelta(days=10), 2900, 4200),  # Past show
        
        # Recent/current concerts
        (base_date - timedelta(days=2), 4100, 4500),   # Recent show
        (base_date + timedelta(days=1), 3800, 5500),   # Tomorrow
        
        # Future concerts
        (base_date + timedelta(days=7), 2100, 6000),   # Next week
        (base_date + timedelta(days=14), 1500, 4800),  # Future booking
        (base_date + timedelta(days=21), 800, 3900),   # Early booking
        (base_date + timedelta(days=35), 300, 5200),   # Far future
        (base_date + timedelta(days=45), 150, 4600),   # Very far future
    ]
    
    concerts = []
    for i, (date, sold, total) in enumerate(concert_scenarios):
        venue = sample_venues[i % len(sample_venues)]
        concert_data = create_concert_data(
            venue_id=venue.id,
            date=date,
            ticket_price=float(65 + (i * 5)),  # Varying prices
            tickets_sold=sold,
            total_tickets=total
        )
        concert = Concert(tour_id=tour.id, **concert_data)
        test_session.add(concert)
        concerts.append(concert)
    
    test_session.commit()
    tour.concerts = concerts
    return tour


@pytest.fixture
def empty_tour_data(test_session) -> Tour:
    """Create tour with zero concerts for edge case testing."""
    tour_data = create_tour_data(
        "Empty Tour",
        TourStatus.PLANNING,
        start_date=datetime.now() + timedelta(days=30),
        end_date=datetime.now() + timedelta(days=90)
    )
    tour = Tour(**tour_data)
    test_session.add(tour)
    test_session.commit()
    return tour


@pytest.fixture
def future_only_tour_data(test_session, sample_venues) -> Tour:
    """Create tour with future-only concerts."""
    tour_data = create_tour_data(
        "Future Tour",
        TourStatus.ACTIVE,
        start_date=datetime.now() + timedelta(days=10),
        end_date=datetime.now() + timedelta(days=70)
    )
    tour = Tour(**tour_data)
    test_session.add(tour)
    test_session.flush()
    
    # All concerts in the future
    future_dates = [
        datetime.now() + timedelta(days=15),
        datetime.now() + timedelta(days=22),
        datetime.now() + timedelta(days=30),
        datetime.now() + timedelta(days=40),
        datetime.now() + timedelta(days=50),
    ]
    
    concerts = []
    for i, date in enumerate(future_dates):
        venue = sample_venues[i % len(sample_venues)]
        concert_data = create_concert_data(
            venue_id=venue.id,
            date=date,
            ticket_price=80.0,
            tickets_sold=500 + (i * 200),
            total_tickets=5000
        )
        concert = Concert(tour_id=tour.id, **concert_data)
        test_session.add(concert)
        concerts.append(concert)
    
    test_session.commit()
    tour.concerts = concerts
    return tour


@pytest.fixture
def past_only_tour_data(test_session, sample_venues) -> Tour:
    """Create tour with past-only concerts (completed tour)."""
    tour_data = create_tour_data(
        "Past Tour",
        TourStatus.COMPLETED,
        start_date=datetime.now() - timedelta(days=90),
        end_date=datetime.now() - timedelta(days=10)
    )
    tour = Tour(**tour_data)
    test_session.add(tour)
    test_session.flush()
    
    # All concerts in the past
    past_dates = [
        datetime.now() - timedelta(days=80),
        datetime.now() - timedelta(days=70),
        datetime.now() - timedelta(days=60),
        datetime.now() - timedelta(days=45),
        datetime.now() - timedelta(days=30),
        datetime.now() - timedelta(days=20),
    ]
    
    concerts = []
    for i, date in enumerate(past_dates):
        venue = sample_venues[i % len(sample_venues)]
        concert_data = create_concert_data(
            venue_id=venue.id,
            date=date,
            ticket_price=70.0 + (i * 2),
            tickets_sold=3000 + (i * 300),
            total_tickets=4500
        )
        concert = Concert(tour_id=tour.id, **concert_data)
        test_session.add(concert)
        concerts.append(concert)
    
    test_session.commit()
    tour.concerts = concerts
    return tour


@pytest.fixture
def mixed_timeframe_tours(test_session, sample_venues) -> Dict[str, Tour]:
    """Create multiple tours with mixed timeframes for comprehensive testing."""
    tours = {}
    
    # Planning tour (future start date)
    planning_tour_data = create_tour_data(
        "Planning Tour",
        TourStatus.PLANNING,
        start_date=datetime.now() + timedelta(days=60),
        end_date=datetime.now() + timedelta(days=120)
    )
    planning_tour = Tour(**planning_tour_data)
    test_session.add(planning_tour)
    test_session.flush()
    
    # Add a few planned concerts
    for i in range(3):
        venue = sample_venues[i]
        concert_data = create_concert_data(
            venue_id=venue.id,
            date=datetime.now() + timedelta(days=65 + (i * 10)),
            ticket_price=85.0,
            tickets_sold=0,  # No sales yet
            total_tickets=4000
        )
        concert = Concert(tour_id=planning_tour.id, **concert_data)
        test_session.add(concert)
    
    tours['planning'] = planning_tour
    
    # Cancelled tour
    cancelled_tour_data = create_tour_data(
        "Cancelled Tour",
        TourStatus.CANCELLED,
        start_date=datetime.now() - timedelta(days=20),
        end_date=datetime.now() + timedelta(days=40)
    )
    cancelled_tour = Tour(**cancelled_tour_data)
    test_session.add(cancelled_tour)
    test_session.flush()
    
    # Add some concerts to cancelled tour
    for i in range(2):
        venue = sample_venues[i + 3]
        concert_data = create_concert_data(
            venue_id=venue.id,
            date=datetime.now() + timedelta(days=10 + (i * 15)),
            ticket_price=75.0,
            tickets_sold=1000,  # Some tickets sold before cancellation
            total_tickets=3500
        )
        concert = Concert(tour_id=cancelled_tour.id, **concert_data)
        test_session.add(concert)
    
    tours['cancelled'] = cancelled_tour
    
    test_session.commit()
    return tours


@pytest.fixture
def high_capacity_venues(test_session) -> List[Venue]:
    """Create venues with very high capacity for stress testing."""
    venues_data = [
        create_venue_data("MetLife Stadium", "East Rutherford", 82500, state="NJ"),
        create_venue_data("Rose Bowl", "Pasadena", 88565),
        create_venue_data("Michigan Stadium", "Ann Arbor", 107601, state="MI"),
        create_venue_data("AT&T Stadium", "Arlington", 105000, state="TX"),
    ]
    
    venues = []
    for venue_data in venues_data:
        venue = Venue(**venue_data)
        test_session.add(venue)
        venues.append(venue)
    
    test_session.commit()
    return venues


@pytest.fixture
def varied_pricing_tour(test_session, sample_venues) -> Tour:
    """Create tour with varied ticket pricing scenarios."""
    tour_data = create_tour_data(
        "Premium Pricing Tour",
        TourStatus.ACTIVE,
        start_date=datetime.now() - timedelta(days=10),
        end_date=datetime.now() + timedelta(days=50)
    )
    tour = Tour(**tour_data)
    test_session.add(tour)
    test_session.flush()
    
    # Different pricing tiers and sales scenarios
    pricing_scenarios = [
        (datetime.now() - timedelta(days=5), 150.0, 2800, 3000),   # Premium sold out
        (datetime.now() + timedelta(days=5), 45.0, 8500, 10000),   # Budget show
        (datetime.now() + timedelta(days=12), 200.0, 1200, 2500),  # VIP pricing
        (datetime.now() + timedelta(days=20), 85.0, 4200, 6000),   # Standard pricing
        (datetime.now() + timedelta(days=30), 300.0, 800, 1500),   # Ultra premium
    ]
    
    concerts = []
    for i, (date, price, sold, total) in enumerate(pricing_scenarios):
        venue = sample_venues[i % len(sample_venues)]
        concert_data = create_concert_data(
            venue_id=venue.id,
            date=date,
            ticket_price=price,
            tickets_sold=sold,
            total_tickets=total
        )
        concert = Concert(tour_id=tour.id, **concert_data)
        test_session.add(concert)
        concerts.append(concert)
    
    test_session.commit()
    tour.concerts = concerts
    return tour


# Mock objects for external dependencies
@pytest.fixture
def mock_cache():
    """Mock cache for testing dashboard caching functionality."""
    cache = MagicMock()
    cache.get.return_value = None
    cache.set.return_value = True
    cache.delete.return_value = True
    return cache


@pytest.fixture
def mock_analytics_client():
    """Mock analytics client for dashboard metrics."""
    client = MagicMock()
    client.track_dashboard_view.return_value = True
    client.get_user_engagement.return_value = {"views": 150, "time_spent": 300}
    return client


# Cleanup fixtures
@pytest.fixture(autouse=True)
def cleanup_database(test_session):
    """Automatically clean up database after each test."""
    yield
    # Clean up in reverse order of dependencies
    test_session.query(Concert).delete()
    test_session.query(Tour).delete()
    test_session.query(Venue).delete()
    test_session.commit()


# Async fixtures for async testing
@pytest_asyncio.fixture
async def async_test_session(test_engine):
    """Async database session for async tests."""
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
    async_session = async_sessionmaker(test_engine, class_=AsyncSession)
    
    async with async_session() as session:
        yield session


# Performance testing fixtures
@pytest.fixture
def large_dataset_tour(test_session, sample_venues) -> Tour:
    """Create tour with large number of concerts for performance testing."""
    tour_data = create_tour_data(
        "Large Dataset Tour",
        TourStatus.ACTIVE,
        start_date=datetime.now() - timedelta(days=180),
        end_date=datetime.now() + timedelta(days=180)
    )
    tour = Tour(**tour_data)
    test_session.add(tour)
    test_session.flush()
    
    # Create 100+ concerts for performance testing
    concerts = []
    base_date = datetime.now() - timedelta(days=150)
    
    for i in range(150):
        date = base_date + timedelta(days=i * 2)
        venue = sample_venues[i % len(sample_venues)]
        
        concert_data = create_concert_data(
            venue_id=venue.id,
            date=date,
            ticket_price=50.0 + (i % 10) * 5,
            tickets_sold=1000 + (i * 20) % 4000,
            total_tickets=3000 + (i % 5) * 1000
        )
        concert = Concert(tour_id=tour.id, **concert_data)
        test_session.add(concert)
        concerts.append(concert)
    
    test_session.commit()
    tour.concerts = concerts
    return tour
