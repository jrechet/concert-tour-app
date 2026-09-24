"""Integration/template tests for the days-remaining countdown on the
rendered concert card (`GET /api/v1/dashboard/concerts`).

`reference_time` is overridden to a fixed moment so "N days remaining" /
"Today" / "Tomorrow" assertions don't depend on the real wall clock, and
concerts are seeded through real `Venue`/`Tour` foreign keys (via
`tests/fixtures/dashboard_fixtures.py`) rather than hardcoded ids.
"""

from datetime import datetime, timedelta

import pytest

from src.database import get_reference_time
from src.main import app
from tests.fixtures.dashboard_fixtures import create_concert, create_tour, create_venues

REFERENCE_TIME = datetime(2024, 6, 15, 9, 0, 0)


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


def _make_tour(db_session, name="Countdown Tour"):
    return create_tour(
        db_session,
        name=name,
        artist="Test Artist",
        start_date=(REFERENCE_TIME - timedelta(days=5)).date(),
        end_date=(REFERENCE_TIME + timedelta(days=60)).date(),
        status="active",
    )


def test_concert_card_shows_days_remaining_for_future_concert(client, db_session):
    venue = create_venues(db_session, count=1)[0]
    tour = _make_tour(db_session)
    create_concert(
        db_session, tour, venue, day_offset=10, ticket_price="50.00", base_time=REFERENCE_TIME,
    )

    response = client.get("/api/v1/dashboard/concerts")

    assert response.status_code == 200
    assert "10 days remaining" in response.text


def test_concert_card_shows_today_for_concert_scheduled_today(client, db_session):
    venue = create_venues(db_session, count=1)[0]
    tour = _make_tour(db_session)
    create_concert(
        db_session, tour, venue, day_offset=0, ticket_price="50.00", base_time=REFERENCE_TIME,
    )

    response = client.get("/api/v1/dashboard/concerts")

    assert response.status_code == 200
    assert "Today" in response.text


def test_concert_card_shows_tomorrow_for_concert_scheduled_tomorrow(client, db_session):
    venue = create_venues(db_session, count=1)[0]
    tour = _make_tour(db_session)
    create_concert(
        db_session, tour, venue, day_offset=1, ticket_price="50.00", base_time=REFERENCE_TIME,
    )

    response = client.get("/api/v1/dashboard/concerts")

    assert response.status_code == 200
    assert "Tomorrow" in response.text
