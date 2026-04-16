import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database import get_db, Base
from app.models import Concert, Venue

# Create test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_dashboard.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


@pytest.fixture
def db_session():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def sample_venue(db_session):
    venue = Venue(
        name="Madison Square Garden",
        city="New York",
        state="NY",
        capacity=20000
    )
    db_session.add(venue)
    db_session.commit()
    db_session.refresh(venue)
    return venue


@pytest.fixture
def sample_concert(db_session, sample_venue):
    concert = Concert(
        date=datetime.now() + timedelta(days=7),
        venue_id=sample_venue.id,
        notes="Opening night"
    )
    db_session.add(concert)
    db_session.commit()
    db_session.refresh(concert)
    return concert


class TestDashboard:
    def test_dashboard_page_loads(self):
        """Test that the main dashboard page loads"""
        response = client.get("/")
        assert response.status_code == 200
        assert "Concert Tour Dashboard" in response.text
        assert "hx-get" in response.text  # Check HTMX attributes are present

    def test_dashboard_stats_endpoint(self, sample_concert):
        """Test dashboard stats endpoint returns proper stats"""
        response = client.get("/api/dashboard/stats")
        assert response.status_code == 200
        
        # Check that response contains stat cards
        assert "Total Concerts" in response.text
        assert "Upcoming Shows" in response.text
        assert "Venues" in response.text
        assert "Total Capacity" in response.text
        
        # Check for stat values
        assert "stat-value" in response.text

    def test_calendar_view_endpoint(self, sample_concert):
        """Test calendar view endpoint returns calendar HTML"""
        response = client.get("/api/dashboard/calendar")
        assert response.status_code == 200
        
        # Check calendar structure
        assert "calendar-grid" in response.text
        assert "calendar-header-day" in response.text
        assert "calendar-day" in response.text
        
        # Check for days of week
        assert "Sun" in response.text
        assert "Mon" in response.text

    def test_calendar_navigation(self, sample_concert):
        """Test calendar navigation with offset"""
        # Test previous month
        response = client.get("/api/dashboard/calendar?offset=-1")
        assert response.status_code == 200
        
        # Test next month
        response = client.get("/api/dashboard/calendar?offset=1")
        assert response.status_code == 200

    def test_concert_details_with_valid_date(self, sample_concert):
        """Test concert details endpoint with valid date"""
        concert_date = sample_concert.date.strftime('%Y-%m-%d')
        response = client.get(f"/api/dashboard/concert-details?date={concert_date}")
        assert response.status_code == 200
        
        # Check concert details are shown
        assert "Madison Square Garden" in response.text
        assert "New York, NY" in response.text
        assert "20,000" in response.text

    def test_concert_details_with_no_concerts(self):
        """Test concert details endpoint with date that has no concerts"""
        future_date = (datetime.now() + timedelta(days=365)).strftime('%Y-%m-%d')
        response = client.get(f"/api/dashboard/concert-details?date={future_date}")
        assert response.status_code == 200
        assert "No concerts scheduled" in response.text

    def test_concert_details_with_invalid_date(self):
        """Test concert details endpoint with invalid date format"""
        response = client.get("/api/dashboard/concert-details?date=invalid-date")
        assert response.status_code == 200
        assert "Invalid date format" in response.text

    def test_dashboard_responsive_elements(self):
        """Test that dashboard HTML contains responsive design elements"""
        response = client.get("/")
        assert response.status_code == 200
        
        # Check for mobile responsive CSS
        assert "@media (max-width: 768px)" in response.text
        assert "grid-template-columns" in response.text
        assert "viewport" in response.text

    def test_htmx_attributes_present(self):
        """Test that HTMX attributes are properly set"""
        response = client.get("/")
        assert response.status_code == 200
        
        # Check for HTMX attributes
        assert 'hx-get="/api/dashboard/stats"' in response.text
        assert 'hx-get="/api/dashboard/calendar"' in response.text
        assert 'hx-trigger="load"' in response.text
        assert 'hx-target="#calendar-content"' in response.text


class TestCalendarFunctionality:
    def test_calendar_shows_concert_dates(self, sample_concert):
        """Test that calendar properly highlights concert dates"""
        response = client.get("/api/dashboard/calendar")
        assert response.status_code == 200
        
        # Check for concert indicators
        assert "has-concert" in response.text
        assert "concert-indicator" in response.text

    def test_calendar_month_year_display(self):
        """Test that calendar displays current month and year"""
        response = client.get("/api/dashboard/calendar")
        assert response.status_code == 200
        
        current_month = datetime.now().strftime('%B')
        current_year = str(datetime.now().year)
        
        # Month name should be in JavaScript that updates the title
        assert f'"{current_month} {current_year}"' in response.text

    def test_multiple_concerts_same_day(self, db_session, sample_venue):
        """Test calendar display with multiple concerts on same day"""
        concert_date = datetime.now() + timedelta(days=10)
        
        # Create multiple concerts on same day
        for i in range(3):
            concert = Concert(
                date=concert_date + timedelta(hours=i*2),
                venue_id=sample_venue.id,
                notes=f"Concert {i+1}"
            )
            db_session.add(concert)
        
        db_session.commit()
        
        response = client.get("/api/dashboard/calendar")
        assert response.status_code == 200
        
        # Should show "+X more" indicator for multiple concerts
        assert "more" in response.text


# Cleanup
def teardown_module():
    """Clean up test database"""
    import os
    try:
        os.remove("test_dashboard.db")
    except FileNotFoundError:
        pass
