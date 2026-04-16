import pytest
from datetime import date, timedelta
from decimal import Decimal
from sqlalchemy.orm import Session
from src.services.dashboard_service import DashboardService
from src.models.venue import Venue
from src.models.concert import Concert


@pytest.fixture
def dashboard_service(db_session: Session):
    return DashboardService(db_session)


@pytest.fixture
def sample_venues(db_session: Session):
    venues = [
        Venue(
            name="Madison Square Garden",
            city="New York",
            country="USA",
            capacity=20000,
            address="4 Pennsylvania Plaza, New York, NY 10001"
        ),
        Venue(
            name="O2 Arena",
            city="London",
            country="UK",
            capacity=20000,
            address="Peninsula Square, London SE10 0DX"
        ),
        Venue(
            name="Bercy Arena",
            city="Paris",
            country="France", 
            capacity=15000,
            address="8 Boulevard de Bercy, 75012 Paris"
        )
    ]
    
    for venue in venues:
        db_session.add(venue)
    db_session.commit()
    
    for venue in venues:
        db_session.refresh(venue)
    
    return venues


@pytest.fixture
def sample_concerts(db_session: Session, sample_venues):
    today = date.today()
    concerts = [
        Concert(
            date=today - timedelta(days=30),  # Past concert
            venue_id=sample_venues[0].id,
            ticket_price=Decimal("100.00")
        ),
        Concert(
            date=today + timedelta(days=30),  # Future concert
            venue_id=sample_venues[1].id,
            ticket_price=Decimal("85.00")
        ),
        Concert(
            date=today + timedelta(days=60),  # Future concert
            venue_id=sample_venues[2].id,
            ticket_price=Decimal("75.00")
        )
    ]
    
    for concert in concerts:
        db_session.add(concert)
    db_session.commit()
    
    for concert in concerts:
        db_session.refresh(concert)
    
    return concerts


def test_get_tour_overview_with_concerts(dashboard_service, sample_concerts):
    overview = dashboard_service.get_tour_overview()
    
    assert overview.tour_name == "World Tour 2024"
    assert overview.start_date is not None
    assert overview.end_date is not None
    assert overview.progress_percentage >= 0
    assert overview.progress_percentage <= 100
    

def test_get_tour_overview_empty_database(dashboard_service):
    overview = dashboard_service.get_tour_overview()
    
    assert overview.tour_name == "Concert Tour"
    assert overview.start_date is None
    assert overview.end_date is None
    assert overview.progress_percentage == 0.0


def test_get_dashboard_stats_with_concerts(dashboard_service, sample_concerts, sample_venues):
    stats = dashboard_service.get_dashboard_stats()
    
    assert stats.total_concerts == 3
    assert stats.unique_cities == 3
    assert stats.unique_countries == 3
    assert stats.total_capacity == 55000  # 20000 + 20000 + 15000
    
    # Revenue: (100 * 20000) + (85 * 20000) + (75 * 15000) = 4,825,000
    expected_revenue = (100 * 20000) + (85 * 20000) + (75 * 15000)
    assert stats.revenue_estimate == float(expected_revenue)


def test_get_dashboard_stats_empty_database(dashboard_service):
    stats = dashboard_service.get_dashboard_stats()
    
    assert stats.total_concerts == 0
    assert stats.unique_cities == 0
    assert stats.unique_countries == 0
    assert stats.total_capacity == 0
    assert stats.revenue_estimate == 0.0


def test_get_upcoming_concerts_with_pagination(dashboard_service, sample_concerts):
    # Get first page with limit 1
    result = dashboard_service.get_upcoming_concerts(limit=1, offset=0)
    
    assert len(result.concerts) == 1
    assert result.total == 2  # Two future concerts
    assert result.limit == 1
    assert result.offset == 0
    assert result.has_next is True
    
    # Verify the concert is in the future
    assert result.concerts[0].date >= date.today()


def test_get_upcoming_concerts_second_page(dashboard_service, sample_concerts):
    # Get second page
    result = dashboard_service.get_upcoming_concerts(limit=1, offset=1)
    
    assert len(result.concerts) == 1
    assert result.total == 2
    assert result.limit == 1
    assert result.offset == 1
    assert result.has_next is False


def test_get_upcoming_concerts_no_future_concerts(dashboard_service, db_session, sample_venues):
    # Add only past concerts
    past_concert = Concert(
        date=date.today() - timedelta(days=30),
        venue_id=sample_venues[0].id,
        ticket_price=Decimal("100.00")
    )
    db_session.add(past_concert)
    db_session.commit()
    
    result = dashboard_service.get_upcoming_concerts()
    
    assert len(result.concerts) == 0
    assert result.total == 0
    assert result.has_next is False


def test_upcoming_concerts_response_format(dashboard_service, sample_concerts, sample_venues):
    result = dashboard_service.get_upcoming_concerts()
    
    if result.concerts:
        concert = result.concerts[0]
        assert hasattr(concert, 'id')
        assert hasattr(concert, 'date')
        assert hasattr(concert, 'venue_name')
        assert hasattr(concert, 'city')
        assert hasattr(concert, 'country')
        assert hasattr(concert, 'ticket_price')
        
        # Verify the venue information is correctly joined
        assert concert.venue_name in ["O2 Arena", "Bercy Arena"]  # Future concerts only
        assert concert.city in ["London", "Paris"]
        assert concert.country in ["UK", "France"]
