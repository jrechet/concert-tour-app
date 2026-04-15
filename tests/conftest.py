import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.main import app
from src.database import get_db
from src.models import Base

# Create in-memory SQLite database for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture
def client():
    """Create a test client."""
    Base.metadata.create_all(bind=engine)
    with TestClient(app) as test_client:
        yield test_client
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session():
    """Create a database session for tests."""
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def sample_tour_data():
    """Sample tour data for testing."""
    return {
        "name": "Test Tour",
        "artist": "Test Artist",
        "start_date": "2024-01-01",
        "end_date": "2024-12-31",
        "description": "Test tour description"
    }


@pytest.fixture
def sample_concert_data():
    """Sample concert data for testing."""
    return {
        "venue": "Test Venue",
        "city": "Test City",
        "date": "2024-06-15",
        "time": "20:00:00",
        "ticket_price": 99.99,
        "tour_id": 1
    }


@pytest.fixture
def created_tour(client, sample_tour_data):
    """Create a tour for testing concerts."""
    response = client.post("/api/v1/tours/", json=sample_tour_data)
    return response.json()


@pytest.fixture
def created_concert(client, created_tour, sample_concert_data):
    """Create a concert for testing."""
    sample_concert_data["tour_id"] = created_tour["id"]
    response = client.post("/api/v1/concerts/", json=sample_concert_data)
    return response.json()
