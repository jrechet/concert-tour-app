"""Tests for the tour dates page: `GET /tour-dates`.

Concerts are seeded through real `Venue`/`Tour` foreign keys (via
`tests/fixtures/dashboard_fixtures.py`) rather than a hardcoded `venue_id`,
and `reference_time` is pinned via a dependency override (not a global
clock patch), mirroring `tests/test_tour_date_ordering.py`. The page
consumes `list_tour_dates` directly, so its DOM order is expected to match
`GET /api/v1/tour-dates`'s own order exactly.
"""

from datetime import datetime, timedelta

import pytest

from src.database import get_reference_time
from src.main import app
from tests.fixtures.dashboard_fixtures import create_concert, create_tour, create_venues

REFERENCE_TIME = datetime(2026, 6, 1, 12, 0, 0)
PAGE_ENDPOINT = "/tour-dates"


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


def _item_positions(html, *markers):
    """Return each marker's first character offset in `html`, in the order
    the markers are given, for asserting on relative DOM order."""
    return [html.index(marker) for marker in markers]


class TestTourDatesTemplate:
    """Coverage for the `GET /tour-dates` page."""

    def test_rendered_page_returns_200_and_lists_dates_in_backend_order(self, client, db_session):
        venues = create_venues(db_session, count=3)
        tour = _make_tour(db_session)

        create_concert(db_session, tour, venues[0], day_offset=30, ticket_price="50.00", base_time=REFERENCE_TIME)
        create_concert(db_session, tour, venues[1], day_offset=1, ticket_price="50.00", base_time=REFERENCE_TIME)
        create_concert(db_session, tour, venues[2], day_offset=10, ticket_price="50.00", base_time=REFERENCE_TIME)

        response = client.get(PAGE_ENDPOINT)
        assert response.status_code == 200

        # Backend order (per `list_tour_dates`) is soonest upcoming first:
        # venues[1] (day 1), venues[2] (day 10), venues[0] (day 30).
        positions = _item_positions(response.text, venues[1].name, venues[2].name, venues[0].name)
        assert positions == sorted(positions)

    def test_soonest_upcoming_item_has_next_concert_marker(self, client, db_session):
        venues = create_venues(db_session, count=2)
        tour = _make_tour(db_session)

        create_concert(db_session, tour, venues[0], day_offset=10, ticket_price="50.00", base_time=REFERENCE_TIME)
        create_concert(db_session, tour, venues[1], day_offset=1, ticket_price="50.00", base_time=REFERENCE_TIME)

        response = client.get(PAGE_ENDPOINT)
        assert response.status_code == 200
        html = response.text

        assert html.count("next-concert") == 1
        assert html.count("Next concert") == 1
        next_concert_position = html.index("next-concert")
        soonest_venue_position = html.index(venues[1].name)
        later_venue_position = html.index(venues[0].name)
        assert next_concert_position < later_venue_position
        assert soonest_venue_position < later_venue_position
        assert next_concert_position < soonest_venue_position

    def test_no_next_concert_marker_when_all_dates_are_past(self, client, db_session):
        venues = create_venues(db_session, count=2)
        tour = _make_tour(db_session)

        create_concert(db_session, tour, venues[0], day_offset=-5, ticket_price="50.00", base_time=REFERENCE_TIME)
        create_concert(db_session, tour, venues[1], day_offset=-1, ticket_price="50.00", base_time=REFERENCE_TIME)

        response = client.get(PAGE_ENDPOINT, params={"include_past": "true"})
        assert response.status_code == 200
        html = response.text

        assert "next-concert" not in html
        assert "Next concert" not in html

    def test_past_dates_section_rendered_after_upcoming_section(self, client, db_session):
        venues = create_venues(db_session, count=2)
        tour = _make_tour(db_session)

        create_concert(db_session, tour, venues[0], day_offset=5, ticket_price="50.00", base_time=REFERENCE_TIME)
        create_concert(db_session, tour, venues[1], day_offset=-5, ticket_price="50.00", base_time=REFERENCE_TIME)

        response_without_past = client.get(PAGE_ENDPOINT)
        assert response_without_past.status_code == 200
        assert "Past dates" not in response_without_past.text
        assert venues[1].name not in response_without_past.text

        response_with_past = client.get(PAGE_ENDPOINT, params={"include_past": "true"})
        assert response_with_past.status_code == 200
        html = response_with_past.text

        assert "Past dates" in html
        upcoming_position = html.index(venues[0].name)
        past_heading_position = html.index("Past dates")
        past_position = html.index(venues[1].name)
        assert upcoming_position < past_heading_position < past_position

    def test_venue_name_with_script_tag_is_escaped(self, client, db_session):
        venues = create_venues(db_session, count=1)
        tour = _make_tour(db_session)
        create_concert(db_session, tour, venues[0], day_offset=1, ticket_price="50.00", base_time=REFERENCE_TIME)

        malicious_name = "<script>alert(1)</script>"
        venue = venues[0]
        venue.name = malicious_name
        db_session.add(venue)
        db_session.commit()

        response = client.get(PAGE_ENDPOINT)
        assert response.status_code == 200

        assert "<script>alert(1)</script>" not in response.text
        assert "&lt;script&gt;alert(1)&lt;/script&gt;" in response.text
