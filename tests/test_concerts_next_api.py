"""Integration tests for `GET /api/v1/concerts/next`.

Concerts are seeded through real `Venue`/`Tour` foreign keys (via the
`tests/fixtures/dashboard_fixtures.py` helpers) rather than hardcoded ids,
and `reference_time` is overridden to a fixed moment so "soonest upcoming"
assertions don't depend on the real wall clock, mirroring
`tests/test_concerts_upcoming.py`.
"""

from datetime import datetime, timedelta

import pytest

from src.database import get_reference_time
from src.main import app
from tests.fixtures.dashboard_fixtures import create_concert, create_tour, create_venues

REFERENCE_TIME = datetime(2024, 6, 15, 18, 0, 0)


@pytest.fixture(autouse=True)
def frozen_reference_time():
    """Pin `get_reference_time` to `REFERENCE_TIME` for every test in this
    module, restoring whatever override (if any) was in place before."""
    previous_override = app.dependency_overrides.get(get_reference_time)
    app.dependency_overrides[get_reference_time] = lambda: REFERENCE_TIME
    yield
    if previous_override is None:
        app.dependency_overrides.pop(get_reference_time, None)
    else:
        app.dependency_overrides[get_reference_time] = previous_override


class TestNextConcert:
    """Coverage for `GET /api/v1/concerts/next`."""

    def test_no_concerts_returns_404(self, client):
        response = client.get("/api/v1/concerts/next")
        assert response.status_code == 404
        assert response.json() == {"detail": "No upcoming concert"}

    def test_all_past_or_cancelled_returns_404(self, client, db_session):
        venues = create_venues(db_session, count=2)
        tour = create_tour(
            db_session, "Farewell Tour", "Test Artist",
            (REFERENCE_TIME - timedelta(days=60)).date(),
            (REFERENCE_TIME + timedelta(days=30)).date(),
            "active",
        )
        create_concert(db_session, tour, venues[0], day_offset=-1, ticket_price="80.00", base_time=REFERENCE_TIME)
        create_concert(
            db_session, tour, venues[1], day_offset=5, ticket_price="80.00", base_time=REFERENCE_TIME,
            is_cancelled=True, cancellation_reason="Weather",
        )

        response = client.get("/api/v1/concerts/next")
        assert response.status_code == 404
        assert response.json() == {"detail": "No upcoming concert"}

    def test_returns_soonest_future_non_cancelled_concert(self, client, db_session):
        venues = create_venues(db_session, count=3)
        tour = create_tour(
            db_session, "Scramble Tour", "Test Artist",
            (REFERENCE_TIME - timedelta(days=5)).date(),
            (REFERENCE_TIME + timedelta(days=30)).date(),
            "active",
        )
        # Inserted deliberately out of chronological order, with a
        # cancelled show that would otherwise be soonest.
        create_concert(db_session, tour, venues[0], day_offset=20, ticket_price="80.00", base_time=REFERENCE_TIME)
        create_concert(
            db_session, tour, venues[1], day_offset=1, ticket_price="80.00", base_time=REFERENCE_TIME,
            is_cancelled=True, cancellation_reason="Weather",
        )
        soonest = create_concert(db_session, tour, venues[2], day_offset=5, ticket_price="80.00", base_time=REFERENCE_TIME)

        response = client.get("/api/v1/concerts/next")
        assert response.status_code == 200
        payload = response.json()

        assert payload["id"] == soonest.id
        assert payload["is_cancelled"] is False
        assert payload["venue"] == {"name": venues[2].name, "capacity": venues[2].capacity}
        assert payload["city"] == {"name": venues[2].city, "country": venues[2].country}
        assert set(payload.keys()) == {"id", "date_time", "is_cancelled", "venue", "city"}

    def test_concert_at_exact_reference_time_is_included(self, client, db_session):
        venues = create_venues(db_session, count=1)
        tour = create_tour(
            db_session, "Exact Time Tour", "Test Artist",
            (REFERENCE_TIME - timedelta(days=5)).date(),
            (REFERENCE_TIME + timedelta(days=5)).date(),
            "active",
        )
        concert = create_concert(db_session, tour, venues[0], day_offset=0, ticket_price="80.00", base_time=REFERENCE_TIME)

        response = client.get("/api/v1/concerts/next")
        assert response.status_code == 200
        assert response.json()["id"] == concert.id

    def test_next_route_not_swallowed_by_concert_id_route(self, client):
        """`/next` must resolve to this endpoint, not `GET /{concert_id}`
        with `concert_id="next"` (which would 422 on the int path param)."""
        response = client.get("/api/v1/concerts/next")
        assert response.status_code in (200, 404)
