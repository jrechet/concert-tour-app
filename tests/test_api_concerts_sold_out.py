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


def _make_sold_out_concert(db_session, tour_name, day_offset, venue=None):
    venue = venue or create_venues(db_session, count=1)[0]
    tour = create_tour(
        db_session, tour_name, "Test Artist",
        REFERENCE_TIME.date(),
        (REFERENCE_TIME + timedelta(days=60)).date(),
        "active",
    )
    return create_concert(
        db_session, tour, venue, day_offset=day_offset, ticket_price="80.00",
        base_time=REFERENCE_TIME, tickets_sold=venue.capacity,
    )


class TestSoldOutConcertsEndpoint:
    """Coverage for `GET /api/v1/concerts/sold-out`."""

    def test_sold_out_returns_200_and_payload_shape(self, client, db_session):
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
        assert payload["title"] == tour.name
        assert payload["start_datetime"] == concert.date_time.isoformat()
        assert payload["venue"] == {
            "id": venues[0].id, "name": venues[0].name, "city": venues[0].city,
        }
        assert payload["capacity"] == venues[0].capacity
        assert payload["tickets_sold"] == venues[0].capacity
        assert payload["tickets_remaining"] == 0

    def test_sold_out_ordered_soonest_first(self, client, db_session):
        venues = create_venues(db_session, count=2)
        later = _make_sold_out_concert(db_session, "Scramble Tour", day_offset=20, venue=venues[0])
        soonest = _make_sold_out_concert(db_session, "Scramble Tour", day_offset=1, venue=venues[1])

        response = client.get("/api/v1/concerts/sold-out")
        assert response.status_code == 200
        payload = response.json()

        assert [c["id"] for c in payload] == [soonest.id, later.id]

    def test_sold_out_excludes_cancelled_concerts(self, client, db_session):
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

    def test_sold_out_excludes_past_concerts(self, client, db_session):
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

    def test_sold_out_excludes_concerts_with_tickets_left(self, client, db_session):
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

    def test_sold_out_returns_200_empty_list_when_none(self, client):
        response = client.get("/api/v1/concerts/sold-out")
        assert response.status_code == 200
        assert response.json() == []

    def test_sold_out_route_not_shadowed_by_concert_detail_route(self, client):
        """`/sold-out` must resolve to this endpoint, not `GET /{concert_id}`
        with `concert_id="sold-out"` (which would 422 on the int path param)."""
        response = client.get("/api/v1/concerts/sold-out")
        assert response.status_code == 200
        assert response.json() == []
