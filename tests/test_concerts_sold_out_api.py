"""Integration tests for `GET /api/v1/concerts/sold-out`.

Concerts are seeded through real `Venue`/`Tour` foreign keys (via the
`tests/fixtures/dashboard_fixtures.py` helpers) rather than hardcoded ids,
and `reference_time` is overridden to a fixed moment so "upcoming"
assertions don't depend on the real wall clock, mirroring
`tests/test_concerts_next_api.py`.
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


class TestSoldOutConcerts:
    """Coverage for `GET /api/v1/concerts/sold-out`."""

    def test_no_concerts_returns_empty_list(self, client):
        response = client.get("/api/v1/concerts/sold-out")
        assert response.status_code == 200
        assert response.json() == []

    def test_no_sold_out_concerts_returns_empty_list_not_404(self, client, db_session):
        venues = create_venues(db_session, count=1)
        tour = create_tour(
            db_session, "Farewell Tour", "Test Artist",
            REFERENCE_TIME.date(),
            (REFERENCE_TIME + timedelta(days=30)).date(),
            "active",
        )
        create_concert(
            db_session, tour, venues[0], day_offset=5, ticket_price="80.00", base_time=REFERENCE_TIME,
            tickets_sold=venues[0].capacity - 1,
        )

        response = client.get("/api/v1/concerts/sold-out")
        assert response.status_code == 200
        assert response.json() == []

    def test_returns_sold_out_concerts_soonest_first(self, client, db_session):
        venues = create_venues(db_session, count=2)
        tour = create_tour(
            db_session, "Scramble Tour", "Test Artist",
            REFERENCE_TIME.date(),
            (REFERENCE_TIME + timedelta(days=30)).date(),
            "active",
        )
        later = create_concert(
            db_session, tour, venues[0], day_offset=20, ticket_price="80.00", base_time=REFERENCE_TIME,
            tickets_sold=venues[0].capacity,
        )
        soonest = create_concert(
            db_session, tour, venues[1], day_offset=1, ticket_price="80.00", base_time=REFERENCE_TIME,
            tickets_sold=venues[1].capacity,
        )

        response = client.get("/api/v1/concerts/sold-out")
        assert response.status_code == 200
        payload = response.json()

        assert [c["id"] for c in payload] == [soonest.id, later.id]
        assert all(c["sold_out"] is True and c["is_sold_out"] is True for c in payload)

    def test_cancelled_sold_out_concert_is_excluded(self, client, db_session):
        venues = create_venues(db_session, count=1)
        tour = create_tour(
            db_session, "Cancelled Tour", "Test Artist",
            REFERENCE_TIME.date(),
            (REFERENCE_TIME + timedelta(days=30)).date(),
            "active",
        )
        create_concert(
            db_session, tour, venues[0], day_offset=5, ticket_price="80.00", base_time=REFERENCE_TIME,
            tickets_sold=venues[0].capacity, is_cancelled=True, cancellation_reason="Venue closed",
        )

        response = client.get("/api/v1/concerts/sold-out")
        assert response.status_code == 200
        assert response.json() == []

    def test_past_sold_out_concert_is_excluded(self, client, db_session):
        venues = create_venues(db_session, count=1)
        tour = create_tour(
            db_session, "Farewell Tour", "Test Artist",
            (REFERENCE_TIME - timedelta(days=30)).date(),
            (REFERENCE_TIME + timedelta(days=1)).date(),
            "active",
        )
        create_concert(
            db_session, tour, venues[0], day_offset=-1, ticket_price="80.00", base_time=REFERENCE_TIME,
            tickets_sold=venues[0].capacity,
        )

        response = client.get("/api/v1/concerts/sold-out")
        assert response.status_code == 200
        assert response.json() == []

    def test_response_matches_concert_response_schema(self, client, db_session):
        venues = create_venues(db_session, count=1)
        tour = create_tour(
            db_session, "Loaded Tour", "Test Artist",
            REFERENCE_TIME.date(),
            (REFERENCE_TIME + timedelta(days=10)).date(),
            "active",
        )
        concert = create_concert(
            db_session, tour, venues[0], day_offset=1, ticket_price="80.00", base_time=REFERENCE_TIME,
            tickets_sold=venues[0].capacity,
        )

        response = client.get("/api/v1/concerts/sold-out")
        assert response.status_code == 200
        payload = response.json()[0]

        assert payload["id"] == concert.id
        assert set(payload.keys()) == {
            "id", "tour_id", "venue_id", "venue_name", "venue_city", "date_time",
            "days_until_concert", "ticket_price", "tickets_sold", "remaining_tickets",
            "sold_out", "is_sold_out", "is_almost_sold_out", "is_cancelled",
            "cancellation_reason",
        }

    def test_sold_out_route_not_swallowed_by_concert_id_route(self, client):
        """`/sold-out` must resolve to this endpoint, not `GET /{concert_id}`
        with `concert_id="sold-out"` (which would 422 on the int path param)."""
        response = client.get("/api/v1/concerts/sold-out")
        assert response.status_code == 200
        assert response.json() == []
