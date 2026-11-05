"""Tests for `POST /api/v1/venues` (201/422/409).

Exercises the endpoint through the real FastAPI app and a real, shared
database session (`client`/`db_session` from `tests/conftest.py`), using
actual `Venue` ORM rows rather than hardcoded ids.
"""

import sqlalchemy as sa

from src.models import Venue
from src.routers import venues as venues_router
from tests.fixtures.dashboard_fixtures import create_venues


def _payload(**overrides):
    payload = {
        "name": "Madison Square Garden",
        "city": "New York",
        "country": "USA",
        "capacity": 20000,
    }
    payload.update(overrides)
    return payload


class TestCreateVenue:
    """Coverage for `POST /api/v1/venues`."""

    def test_valid_payload_returns_201_with_created_venue(self, client, db_session):
        response = client.post("/api/v1/venues", json=_payload())

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Madison Square Garden"
        assert data["city"] == "New York"
        assert data["country"] == "USA"
        assert data["capacity"] == 20000
        assert isinstance(data["id"], int)

        stored = db_session.query(Venue).filter_by(id=data["id"]).one()
        assert stored.name == "Madison Square Garden"
        assert stored.city == "New York"
        assert stored.country == "USA"
        assert stored.capacity == 20000

    def test_same_name_different_city_returns_201(self, client, db_session):
        existing = create_venues(db_session, count=1)[0]

        response = client.post(
            "/api/v1/venues",
            json=_payload(name=existing.name, city="A Different City"),
        )

        assert response.status_code == 201
        assert response.json()["city"] == "A Different City"
        assert db_session.query(Venue).filter_by(name=existing.name).count() == 2

    def test_duplicate_name_and_city_returns_409_and_creates_no_row(self, client, db_session):
        existing = create_venues(db_session, count=1)[0]
        before_count = db_session.query(Venue).count()

        response = client.post(
            "/api/v1/venues",
            json=_payload(name=existing.name, city=existing.city, country="Canada", capacity=5000),
        )

        assert response.status_code == 409
        assert "already exists" in response.json()["detail"]
        assert db_session.query(Venue).count() == before_count

    def test_integrity_error_fallback_returns_409_not_500(self, client, db_session, monkeypatch):
        """Simulates a race where two requests pass the pre-check at once:
        the real (name, city) unique index is added directly to this test's
        table (mirroring the production migration), and the pre-check is
        forced to report no conflict so the request reaches `create_venue`
        and fails at the real database level. The router's `IntegrityError`
        handler must still translate that into a 409, never a 500."""
        existing = create_venues(db_session, count=1)[0]
        db_session.execute(
            sa.text("CREATE UNIQUE INDEX uq_test_venues_name_city ON venues (name, city)")
        )
        db_session.commit()
        monkeypatch.setattr(venues_router, "venue_name_city_exists", lambda db, name, city: False)
        before_count = db_session.query(Venue).count()

        response = client.post(
            "/api/v1/venues",
            json=_payload(name=existing.name, city=existing.city, country="Canada", capacity=5000),
        )

        assert response.status_code == 409
        assert db_session.query(Venue).count() == before_count

    def test_capacity_zero_returns_422(self, client, db_session):
        response = client.post("/api/v1/venues", json=_payload(capacity=0))

        assert response.status_code == 422
        assert db_session.query(Venue).count() == 0

    def test_negative_capacity_returns_422(self, client, db_session):
        response = client.post("/api/v1/venues", json=_payload(capacity=-1))

        assert response.status_code == 422
        assert db_session.query(Venue).count() == 0

    def test_missing_name_returns_422(self, client, db_session):
        payload = _payload()
        del payload["name"]

        response = client.post("/api/v1/venues", json=payload)

        assert response.status_code == 422
        assert db_session.query(Venue).count() == 0

    def test_empty_name_returns_422(self, client, db_session):
        response = client.post("/api/v1/venues", json=_payload(name=""))

        assert response.status_code == 422
        assert db_session.query(Venue).count() == 0

    def test_missing_city_returns_422(self, client, db_session):
        payload = _payload()
        del payload["city"]

        response = client.post("/api/v1/venues", json=payload)

        assert response.status_code == 422
        assert db_session.query(Venue).count() == 0

    def test_missing_country_returns_422(self, client, db_session):
        payload = _payload()
        del payload["country"]

        response = client.post("/api/v1/venues", json=payload)

        assert response.status_code == 422
        assert db_session.query(Venue).count() == 0

    def test_missing_capacity_returns_422(self, client, db_session):
        payload = _payload()
        del payload["capacity"]

        response = client.post("/api/v1/venues", json=payload)

        assert response.status_code == 422
        assert db_session.query(Venue).count() == 0
