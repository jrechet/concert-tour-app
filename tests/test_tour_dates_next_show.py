"""Tests for the `upcoming_only` param on the concert list endpoints and the
"Next Show" highlight rendered on the first (soonest) tour date.

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


def _make_tour(db_session, name="Test Tour"):
    return create_tour(
        db_session, name, "Test Artist",
        (REFERENCE_TIME - timedelta(days=60)).date(),
        (REFERENCE_TIME + timedelta(days=60)).date(),
        "active",
    )


class TestDashboardConcertsUpcomingOnly:
    """Coverage for `upcoming_only` on `GET /api/v1/dashboard/concerts`."""

    def test_upcoming_only_excludes_past_and_orders_soonest_first(self, client, db_session):
        venues = create_venues(db_session, count=3)
        tour = _make_tour(db_session)
        create_concert(db_session, tour, venues[0], day_offset=-5, ticket_price="80.00", base_time=REFERENCE_TIME)
        create_concert(db_session, tour, venues[1], day_offset=1, ticket_price="80.00", base_time=REFERENCE_TIME)
        create_concert(db_session, tour, venues[2], day_offset=10, ticket_price="80.00", base_time=REFERENCE_TIME)

        response = client.get("/api/v1/dashboard/concerts", params={"upcoming_only": "true"})

        assert response.status_code == 200
        text = response.text
        assert venues[0].name not in text
        assert text.index(venues[1].name) < text.index(venues[2].name)

    def test_first_card_gets_next_show_badge_when_upcoming_only(self, client, db_session):
        venues = create_venues(db_session, count=2)
        tour = _make_tour(db_session, "Badge Tour")
        create_concert(db_session, tour, venues[0], day_offset=1, ticket_price="80.00", base_time=REFERENCE_TIME)
        create_concert(db_session, tour, venues[1], day_offset=10, ticket_price="80.00", base_time=REFERENCE_TIME)

        response = client.get("/api/v1/dashboard/concerts", params={"upcoming_only": "true"})

        assert response.status_code == 200
        text = response.text
        assert "Next Show" in text
        assert text.count("next-show-badge") == 1
        # The badge appears before the second venue's card in the markup.
        assert text.index("Next Show") < text.index(venues[1].name)

    def test_no_badge_when_upcoming_only_not_requested(self, client, db_session):
        venues = create_venues(db_session, count=1)
        tour = _make_tour(db_session, "No Badge Tour")
        create_concert(db_session, tour, venues[0], day_offset=1, ticket_price="80.00", base_time=REFERENCE_TIME)

        response = client.get("/api/v1/dashboard/concerts")

        assert response.status_code == 200
        assert "Next Show" not in response.text

    def test_upcoming_only_defaults_to_false_for_existing_clients(self, client, db_session):
        venues = create_venues(db_session, count=2)
        tour = _make_tour(db_session, "Default Tour")
        past = create_concert(db_session, tour, venues[0], day_offset=-5, ticket_price="80.00", base_time=REFERENCE_TIME)
        create_concert(db_session, tour, venues[1], day_offset=1, ticket_price="80.00", base_time=REFERENCE_TIME)

        response = client.get("/api/v1/dashboard/concerts")

        assert response.status_code == 200
        assert past.venue.name in response.text

    def test_venue_name_is_escaped_in_upcoming_only_view(self, client, db_session):
        from src.models import Venue

        venue = Venue(name="<script>alert('xss')</script>", city="Testville", country="USA", capacity=100)
        db_session.add(venue)
        db_session.commit()
        db_session.refresh(venue)
        tour = _make_tour(db_session, "XSS Tour")
        create_concert(db_session, tour, venue, day_offset=1, ticket_price="50.00", base_time=REFERENCE_TIME)

        response = client.get("/api/v1/dashboard/concerts", params={"upcoming_only": "true"})

        assert response.status_code == 200
        assert "<script>alert" not in response.text
        assert "&lt;script&gt;" in response.text


class TestConcertsListUpcomingOnly:
    """Coverage for `upcoming_only` on `GET /api/v1/concerts/`."""

    def test_upcoming_only_excludes_past_concerts(self, client, db_session):
        venues = create_venues(db_session, count=2)
        tour = _make_tour(db_session, "JSON Tour")
        create_concert(db_session, tour, venues[0], day_offset=-5, ticket_price="80.00", base_time=REFERENCE_TIME)
        upcoming = create_concert(db_session, tour, venues[1], day_offset=1, ticket_price="80.00", base_time=REFERENCE_TIME)

        response = client.get("/api/v1/concerts/", params={"upcoming_only": "true"})

        assert response.status_code == 200
        data = response.json()
        assert [item["id"] for item in data] == [upcoming.id]

    def test_upcoming_only_combines_with_city_filter(self, client, db_session):
        venues = create_venues(db_session, count=2)
        tour = _make_tour(db_session, "Combined Filter Tour")
        create_concert(db_session, tour, venues[0], day_offset=-5, ticket_price="80.00", base_time=REFERENCE_TIME)
        matching = create_concert(db_session, tour, venues[1], day_offset=1, ticket_price="80.00", base_time=REFERENCE_TIME)

        response = client.get(
            "/api/v1/concerts/", params={"upcoming_only": "true", "city": venues[1].city}
        )

        assert response.status_code == 200
        data = response.json()
        assert [item["id"] for item in data] == [matching.id]


class TestDashboardPageWiring:
    """Coverage for the dashboard page pointing its concert list fetches at
    the upcoming-only endpoint."""

    def test_dashboard_wires_calendar_grid_to_upcoming_only(self, client):
        response = client.get("/dashboard")

        assert response.status_code == 200
        assert "/api/v1/dashboard/concerts?upcoming_only=true" in response.text
