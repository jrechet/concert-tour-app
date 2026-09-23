"""Tests for chronological ordering of `GET /api/v1/concerts/`.

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


class TestConcertsListOrdering:
    """Coverage for the chronological ordering behavior of
    `GET /api/v1/concerts/`."""

    def test_out_of_order_dates_returned_ascending_nearest_future_first(self, client, db_session):
        venues = create_venues(db_session, count=3)
        tour = create_tour(
            db_session, "Scramble Tour", "Test Artist",
            (REFERENCE_TIME - timedelta(days=5)).date(),
            (REFERENCE_TIME + timedelta(days=30)).date(),
            "active",
        )
        # Inserted deliberately out of chronological order.
        create_concert(db_session, tour, venues[0], day_offset=20, ticket_price="80.00", base_time=REFERENCE_TIME)
        create_concert(db_session, tour, venues[1], day_offset=1, ticket_price="80.00", base_time=REFERENCE_TIME)
        create_concert(db_session, tour, venues[2], day_offset=10, ticket_price="80.00", base_time=REFERENCE_TIME)

        response = client.get("/api/v1/concerts/")
        assert response.status_code == 200
        data = response.json()

        returned_dates = [item["date_time"] for item in data]
        assert returned_dates == sorted(returned_dates)
        assert len(data) == 3

    def test_past_concerts_are_appended_after_future_dates_oldest_first(self, client, db_session):
        venues = create_venues(db_session, count=4)
        tour = create_tour(
            db_session, "Mixed Tour", "Test Artist",
            (REFERENCE_TIME - timedelta(days=60)).date(),
            (REFERENCE_TIME + timedelta(days=60)).date(),
            "active",
        )
        future_soon = create_concert(db_session, tour, venues[0], day_offset=2, ticket_price="80.00", base_time=REFERENCE_TIME)
        future_later = create_concert(db_session, tour, venues[1], day_offset=15, ticket_price="80.00", base_time=REFERENCE_TIME)
        past_recent = create_concert(db_session, tour, venues[2], day_offset=-3, ticket_price="80.00", base_time=REFERENCE_TIME)
        past_older = create_concert(db_session, tour, venues[3], day_offset=-20, ticket_price="80.00", base_time=REFERENCE_TIME)

        response = client.get("/api/v1/concerts/")
        assert response.status_code == 200
        returned_ids = [item["id"] for item in response.json()]

        # Behavior: past concerts are appended after all upcoming ones,
        # ordered oldest-first within each group.
        assert returned_ids == [future_soon.id, future_later.id, past_older.id, past_recent.id]

    def test_todays_concert_is_upcoming_and_precedes_future_dates(self, client, db_session):
        venues = create_venues(db_session, count=3)
        tour = create_tour(
            db_session, "Today Tour", "Test Artist",
            (REFERENCE_TIME - timedelta(days=5)).date(),
            (REFERENCE_TIME + timedelta(days=30)).date(),
            "active",
        )
        today_concert = create_concert(
            db_session, tour, venues[0], day_offset=0, ticket_price="80.00",
            base_time=REFERENCE_TIME.replace(hour=9, minute=0),
        )
        future_concert = create_concert(
            db_session, tour, venues[1], day_offset=1, ticket_price="80.00", base_time=REFERENCE_TIME
        )
        yesterday_concert = create_concert(
            db_session, tour, venues[2], day_offset=-1, ticket_price="80.00", base_time=REFERENCE_TIME
        )

        response = client.get("/api/v1/concerts/")
        assert response.status_code == 200
        returned_ids = [item["id"] for item in response.json()]

        assert returned_ids.index(today_concert.id) < returned_ids.index(future_concert.id)
        assert returned_ids.index(today_concert.id) < returned_ids.index(yesterday_concert.id)

    def test_ordering_is_applied_before_pagination(self, client, db_session):
        venues = create_venues(db_session, count=3)
        tour = create_tour(
            db_session, "Paginated Tour", "Test Artist",
            (REFERENCE_TIME - timedelta(days=5)).date(),
            (REFERENCE_TIME + timedelta(days=30)).date(),
            "active",
        )
        soonest = create_concert(db_session, tour, venues[0], day_offset=1, ticket_price="80.00", base_time=REFERENCE_TIME)
        create_concert(db_session, tour, venues[1], day_offset=10, ticket_price="80.00", base_time=REFERENCE_TIME)
        create_concert(db_session, tour, venues[2], day_offset=20, ticket_price="80.00", base_time=REFERENCE_TIME)

        response = client.get("/api/v1/concerts/", params={"skip": 0, "limit": 1})
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["id"] == soonest.id

    def test_empty_result_set_returns_empty_list(self, client):
        response = client.get("/api/v1/concerts/")
        assert response.status_code == 200
        assert response.json() == []
