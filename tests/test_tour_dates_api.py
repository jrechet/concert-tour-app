"""Integration tests for the chronologically ordered tour dates API.

Concerts are seeded through real `Venue`/`Tour` foreign keys (via
`tests/fixtures/dashboard_fixtures.py`) rather than hardcoded ids, and
`reference_time` is pinned via a dependency override so "upcoming vs.
past" assertions never depend on the real wall clock.
"""

from datetime import datetime, timedelta

import pytest

from src.database import get_reference_time
from src.main import app
from tests.fixtures.dashboard_fixtures import create_concert, create_tour, create_venues

REFERENCE_TIME = datetime(2026, 6, 1, 12, 0, 0)


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


def _make_tour(db_session):
    return create_tour(
        db_session, "Reunion Tour", "Test Artist",
        (REFERENCE_TIME - timedelta(days=60)).date(),
        (REFERENCE_TIME + timedelta(days=60)).date(),
        "active",
    )


class TestTourDatesListOrdering:
    """Coverage for `GET /api/v1/tour-dates` returning next-concert-first."""

    def test_mixed_past_and_future_returns_200_ordered_soonest_first(self, client, db_session):
        venues = create_venues(db_session, count=4)
        tour = _make_tour(db_session)

        far_future = create_concert(db_session, tour, venues[0], day_offset=30, ticket_price="50.00", base_time=REFERENCE_TIME)
        next_concert = create_concert(db_session, tour, venues[1], day_offset=1, ticket_price="50.00", base_time=REFERENCE_TIME)
        recent_past = create_concert(db_session, tour, venues[2], day_offset=-3, ticket_price="50.00", base_time=REFERENCE_TIME)
        older_past = create_concert(db_session, tour, venues[3], day_offset=-20, ticket_price="50.00", base_time=REFERENCE_TIME)

        response = client.get("/api/v1/tour-dates")
        assert response.status_code == 200
        data = response.json()

        assert [item["id"] for item in data] == [
            next_concert.id,
            far_future.id,
            recent_past.id,
            older_past.id,
        ]

    def test_no_tour_dates_returns_200_with_empty_list(self, client):
        response = client.get("/api/v1/tour-dates")
        assert response.status_code == 200
        assert response.json() == []

    def test_upcoming_concert_precedes_past_concert_in_response(self, client, db_session):
        venues = create_venues(db_session, count=2)
        tour = _make_tour(db_session)

        past_concert = create_concert(db_session, tour, venues[0], day_offset=-10, ticket_price="50.00", base_time=REFERENCE_TIME)
        upcoming_concert = create_concert(db_session, tour, venues[1], day_offset=10, ticket_price="50.00", base_time=REFERENCE_TIME)

        response = client.get("/api/v1/tour-dates")
        assert response.status_code == 200
        data = response.json()

        ids = [item["id"] for item in data]
        assert ids.index(upcoming_concert.id) < ids.index(past_concert.id)
        assert data[0]["date_time"] == (REFERENCE_TIME + timedelta(days=10)).isoformat() + "Z"

    def test_detail_route_still_returns_404_for_unknown_tour_date_id(self, client):
        response = client.get("/api/v1/tours/999999/dates")
        assert response.status_code == 404
