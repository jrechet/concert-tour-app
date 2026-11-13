"""Integration tests for `GET /api/v1/tour-dates`.

Concerts are seeded through real `Venue`/`Tour` foreign keys (via
`tests/fixtures/dashboard_fixtures.py`) rather than a hardcoded `venue_id`,
and `reference_time` is pinned via a dependency override (not a global
clock patch), mirroring `tests/test_tour_date_ordering.py`.
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


class TestTourDatesList:
    """Coverage for `GET /api/v1/tour-dates`."""

    def test_list_returns_200_with_next_concert_first(self, client, db_session):
        venues = create_venues(db_session, count=3)
        tour = _make_tour(db_session)

        far_future = create_concert(db_session, tour, venues[0], day_offset=30, ticket_price="50.00", base_time=REFERENCE_TIME)
        next_concert = create_concert(db_session, tour, venues[1], day_offset=1, ticket_price="50.00", base_time=REFERENCE_TIME)
        mid_future = create_concert(db_session, tour, venues[2], day_offset=10, ticket_price="50.00", base_time=REFERENCE_TIME)

        response = client.get("/api/v1/tour-dates")
        assert response.status_code == 200
        data = response.json()

        assert [item["id"] for item in data] == [next_concert.id, mid_future.id, far_future.id]
        assert data[0]["date_time"] == (REFERENCE_TIME + timedelta(days=1)).isoformat() + "Z"

    def test_list_include_past_false_returns_200_without_past_dates(self, client, db_session):
        venues = create_venues(db_session, count=2)
        tour = _make_tour(db_session)

        upcoming = create_concert(db_session, tour, venues[0], day_offset=5, ticket_price="50.00", base_time=REFERENCE_TIME)
        create_concert(db_session, tour, venues[1], day_offset=-5, ticket_price="50.00", base_time=REFERENCE_TIME)

        response = client.get("/api/v1/tour-dates", params={"include_past": "false"})
        assert response.status_code == 200
        data = response.json()

        assert [item["id"] for item in data] == [upcoming.id]

    def test_list_sort_date_desc_returns_200_in_descending_order(self, client, db_session):
        venues = create_venues(db_session, count=4)
        tour = _make_tour(db_session)

        upcoming = create_concert(db_session, tour, venues[0], day_offset=5, ticket_price="50.00", base_time=REFERENCE_TIME)
        recent_past = create_concert(db_session, tour, venues[1], day_offset=-3, ticket_price="50.00", base_time=REFERENCE_TIME)
        older_past = create_concert(db_session, tour, venues[2], day_offset=-20, ticket_price="50.00", base_time=REFERENCE_TIME)
        far_future = create_concert(db_session, tour, venues[3], day_offset=40, ticket_price="50.00", base_time=REFERENCE_TIME)

        response = client.get("/api/v1/tour-dates", params={"sort": "date_desc"})
        assert response.status_code == 200
        data = response.json()

        assert [item["id"] for item in data] == [far_future.id, upcoming.id, recent_past.id, older_past.id]
        returned_dates = [item["date_time"] for item in data]
        assert returned_dates == sorted(returned_dates, reverse=True)

    def test_list_invalid_sort_value_returns_422(self, client):
        response = client.get("/api/v1/tour-dates", params={"sort": "banana"})
        assert response.status_code == 422

    def test_list_invalid_include_past_value_returns_422(self, client):
        response = client.get("/api/v1/tour-dates", params={"include_past": "maybe"})
        assert response.status_code == 422

    def test_list_returns_200_and_empty_list_when_no_tour_dates(self, client):
        response = client.get("/api/v1/tour-dates")
        assert response.status_code == 200
        assert response.json() == []
