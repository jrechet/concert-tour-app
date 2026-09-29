"""Tests for the "Show past concerts" toggle on the dashboard: the
`show_past` param on `GET /api/v1/dashboard/concerts`, its interaction with
`upcoming_only`, and the checkbox markup rendered on the dashboard shell.
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


class TestDashboardShowPastToggleMarkup:
    def test_dashboard_renders_show_past_checkbox(self, client):
        response = client.get("/dashboard")

        assert response.status_code == 200
        assert 'id="show-past-checkbox"' in response.text
        assert 'name="show_past"' in response.text
        assert "Show past concerts" in response.text

    def test_show_past_checkbox_unchecked_by_default(self, client):
        response = client.get("/dashboard")

        assert response.status_code == 200
        text = response.text
        checkbox_start = text.index('id="show-past-checkbox"')
        checkbox_markup = text[checkbox_start - 200:checkbox_start + 200]
        assert "checked" not in checkbox_markup


class TestDashboardConcertsShowPast:
    def test_show_past_true_overrides_upcoming_only_filter(self, client, db_session):
        venues = create_venues(db_session, count=2)
        tour = _make_tour(db_session)
        past = create_concert(db_session, tour, venues[0], day_offset=-5, ticket_price="80.00", base_time=REFERENCE_TIME)
        future = create_concert(db_session, tour, venues[1], day_offset=1, ticket_price="80.00", base_time=REFERENCE_TIME)

        response = client.get(
            "/api/v1/dashboard/concerts",
            params={"upcoming_only": "true", "show_past": "true"},
        )

        assert response.status_code == 200
        text = response.text
        assert past.venue.name in text
        assert future.venue.name in text

    def test_show_past_false_keeps_upcoming_only_filtering_past_concerts(self, client, db_session):
        venues = create_venues(db_session, count=2)
        tour = _make_tour(db_session)
        past = create_concert(db_session, tour, venues[0], day_offset=-5, ticket_price="80.00", base_time=REFERENCE_TIME)
        future = create_concert(db_session, tour, venues[1], day_offset=1, ticket_price="80.00", base_time=REFERENCE_TIME)

        response = client.get(
            "/api/v1/dashboard/concerts",
            params={"upcoming_only": "true", "show_past": "false"},
        )

        assert response.status_code == 200
        text = response.text
        assert past.venue.name not in text
        assert future.venue.name in text

    def test_missing_show_past_defaults_to_upcoming_only_behavior(self, client, db_session):
        venues = create_venues(db_session, count=2)
        tour = _make_tour(db_session)
        past = create_concert(db_session, tour, venues[0], day_offset=-5, ticket_price="80.00", base_time=REFERENCE_TIME)
        future = create_concert(db_session, tour, venues[1], day_offset=1, ticket_price="80.00", base_time=REFERENCE_TIME)

        response = client.get("/api/v1/dashboard/concerts", params={"upcoming_only": "true"})

        assert response.status_code == 200
        text = response.text
        assert past.venue.name not in text
        assert future.venue.name in text

    def test_next_show_badge_withheld_when_show_past_true(self, client, db_session):
        venues = create_venues(db_session, count=2)
        tour = _make_tour(db_session, "Badge Tour")
        create_concert(db_session, tour, venues[0], day_offset=-5, ticket_price="80.00", base_time=REFERENCE_TIME)
        create_concert(db_session, tour, venues[1], day_offset=1, ticket_price="80.00", base_time=REFERENCE_TIME)

        response = client.get(
            "/api/v1/dashboard/concerts",
            params={"upcoming_only": "true", "show_past": "true"},
        )

        assert response.status_code == 200
        assert "Next Show" not in response.text

    def test_next_show_badge_still_present_when_show_past_false(self, client, db_session):
        venues = create_venues(db_session, count=2)
        tour = _make_tour(db_session, "Badge Tour")
        create_concert(db_session, tour, venues[0], day_offset=1, ticket_price="80.00", base_time=REFERENCE_TIME)
        create_concert(db_session, tour, venues[1], day_offset=10, ticket_price="80.00", base_time=REFERENCE_TIME)

        response = client.get(
            "/api/v1/dashboard/concerts",
            params={"upcoming_only": "true", "show_past": "false"},
        )

        assert response.status_code == 200
        assert "Next Show" in response.text

    def test_invalid_show_past_value_falls_back_to_upcoming_only_behavior(self, client, db_session):
        venues = create_venues(db_session, count=1)
        tour = _make_tour(db_session)
        past = create_concert(db_session, tour, venues[0], day_offset=-5, ticket_price="80.00", base_time=REFERENCE_TIME)

        response = client.get(
            "/api/v1/dashboard/concerts",
            params={"upcoming_only": "true", "show_past": "not-a-boolean"},
        )

        assert response.status_code == 200
        assert past.venue.name not in response.text

    def test_venue_name_is_escaped_when_show_past_true(self, client, db_session):
        from src.models import Venue

        venue = Venue(name="<script>alert('xss')</script>", city="Testville", country="USA", capacity=100)
        db_session.add(venue)
        db_session.commit()
        db_session.refresh(venue)
        tour = _make_tour(db_session, "XSS Tour")
        create_concert(db_session, tour, venue, day_offset=-1, ticket_price="50.00", base_time=REFERENCE_TIME)

        response = client.get(
            "/api/v1/dashboard/concerts",
            params={"upcoming_only": "true", "show_past": "true"},
        )

        assert response.status_code == 200
        assert "<script>alert" not in response.text
        assert "&lt;script&gt;" in response.text
