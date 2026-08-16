"""Test configuration and fixtures."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.main import app
from src.database import get_db, Base
from tests.fixtures.dashboard_data import build_multi_concert_tour_fixtures, attach_tour_ids

# In-memory + StaticPool: a plain on-disk file here would be opened by both this
# module's engine and tests/test_tours.py's own separate engine/autouse fixture,
# and two independent SQLAlchemy engines issuing DDL (create_all/drop_all)
# against the same SQLite file can lock each other out. StaticPool keeps every
# connection (regardless of thread) on one shared in-memory database, which
# avoids that cross-engine file contention and matches FastAPI's documented
# pattern for testing against SQLite.
SQLALCHEMY_TEST_DATABASE_URL = "sqlite://"
engine = create_engine(
    SQLALCHEMY_TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """Override database dependency for testing."""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
def setup_database():
    """Create tables before each test, drop after."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client():
    """Create test client."""
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def multi_concert_tour_fixtures():
    """Raw realistic tour + concert payloads, not yet persisted."""
    return build_multi_concert_tour_fixtures()


@pytest.fixture
def seeded_multi_concert_tours(client, multi_concert_tour_fixtures):
    """Persist the fixture tours via the API and attach validated concert data."""
    tour_ids = []
    for fixture in multi_concert_tour_fixtures:
        response = client.post("/api/v1/tours/", json=fixture["tour"])
        assert response.status_code == 201
        tour_ids.append(response.json()["id"])
    return attach_tour_ids(multi_concert_tour_fixtures, tour_ids)
