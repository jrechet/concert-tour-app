"""Integration tests for `GET /api/v1/concerts/upcoming`.

Concerts are seeded through real `Venue`/`Tour` foreign keys (via the
`tests/fixtures/dashboard_fixtures.py` helpers) rather than hardcoded ids,
and `reference_time` is overridden to a fixed moment so "upcoming vs. past"
assertions don't depend on the real wall clock.
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


class TestUpcomingConcerts:
    """Coverage for `GET /api/v1/concerts/upcoming`."""

    def test_past_concerts_are_excluded(self, client, db_session):
        venues = create_venues(db_session, count=2)
        tour = create_tour(
            db_session, "Farewell Tour", "Test Artist",
            (REFERENCE_TIME - timedelta(days=60)).date(),
            (REFERENCE_TIME + timedelta(days=1)).date(),
            "active",
        )
        past_concert = create_concert(
            db_session, tour, venues[0], day_offset=-1, ticket_price="80.00", base_time=REFERENCE_TIME
        )
        create_concert(db_session, tour, venues[1], day_offset=-30, ticket_price="80.00", base_time=REFERENCE_TIME)

        response = client.get("/api/v1/concerts/upcoming")
        assert response.status_code == 200
        returned_ids = [item["id"] for item in response.json()]

        assert past_concert.id not in returned_ids
        assert returned_ids == []

    def test_concert_dated_exactly_today_is_included(self, client, db_session):
        venues = create_venues(db_session, count=1)
        tour = create_tour(
            db_session, "Today Tour", "Test Artist",
            (REFERENCE_TIME - timedelta(days=5)).date(),
            (REFERENCE_TIME + timedelta(days=5)).date(),
            "active",
        )
        today_concert = create_concert(
            db_session, tour, venues[0], day_offset=0, ticket_price="80.00",
            base_time=REFERENCE_TIME.replace(hour=9, minute=0),
        )

        response = client.get("/api/v1/concerts/upcoming")
        assert response.status_code == 200
        returned_ids = [item["id"] for item in response.json()]

        assert returned_ids == [today_concert.id]

    def test_multiple_future_concerts_ordered_soonest_first(self, client, db_session):
        venues = create_venues(db_session, count=3)
        tour = create_tour(
            db_session, "Scramble Tour", "Test Artist",
            (REFERENCE_TIME - timedelta(days=5)).date(),
            (REFERENCE_TIME + timedelta(days=30)).date(),
            "active",
        )
        # Inserted deliberately out of chronological order.
        later = create_concert(db_session, tour, venues[0], day_offset=20, ticket_price="80.00", base_time=REFERENCE_TIME)
        soonest = create_concert(db_session, tour, venues[1], day_offset=1, ticket_price="80.00", base_time=REFERENCE_TIME)
        middle = create_concert(db_session, tour, venues[2], day_offset=10, ticket_price="80.00", base_time=REFERENCE_TIME)

        response = client.get("/api/v1/concerts/upcoming")
        assert response.status_code == 200
        returned_ids = [item["id"] for item in response.json()]

        assert returned_ids == [soonest.id, middle.id, later.id]

    def test_no_upcoming_concerts_returns_empty_list(self, client):
        response = client.get("/api/v1/concerts/upcoming")
        assert response.status_code == 200
        assert response.json() == []

    def test_response_payload_matches_expected_schema(self, client, db_session):
        venues = create_venues(db_session, count=1)
        tour = create_tour(
            db_session, "Schema Tour", "Test Artist",
            (REFERENCE_TIME - timedelta(days=5)).date(),
            (REFERENCE_TIME + timedelta(days=5)).date(),
            "active",
        )
        concert = create_concert(
            db_session, tour, venues[0], day_offset=3, ticket_price="80.00",
            base_time=REFERENCE_TIME, tickets_sold=100,
        )

        response = client.get("/api/v1/concerts/upcoming")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1

        payload = data[0]
        assert payload["id"] == concert.id
        assert payload["tour_id"] == tour.id
        assert payload["venue_id"] == venues[0].id
        assert payload["venue_name"] == venues[0].name
        assert payload["venue_city"] == venues[0].city
        assert set(payload.keys()) == {
            "id",
            "tour_id",
            "venue_id",
            "venue_name",
            "venue_city",
            "date_time",
            "days_until_concert",
            "ticket_price",
            "tickets_sold",
            "remaining_tickets",
            "sold_out",
            "is_almost_sold_out",
            "is_cancelled",
            "cancellation_reason",
        }
