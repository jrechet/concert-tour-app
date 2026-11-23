"""Tests for the tour dates page: `GET /tour-dates`.

Covers the acceptance criteria for rendering tour dates in chronological
order with the next concert highlighted: venues must appear in the same
order the backend (`list_tour_dates`) returns them, exactly one
`next-concert` marker must appear on the soonest upcoming concert, no
marker is rendered when every concert is in the past or there are no
concerts at all, and user-supplied fields are HTML-escaped.
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


class TestTourDatesViews:
    """Coverage for the `GET /tour-dates` page."""

    def test_page_lists_venues_in_chronological_order(self, client, db_session):
        venues = create_venues(db_session, count=3)
        tour = _make_tour(db_session)

        create_concert(db_session, tour, venues[0], day_offset=30, ticket_price="50.00", base_time=REFERENCE_TIME)
        create_concert(db_session, tour, venues[1], day_offset=1, ticket_price="50.00", base_time=REFERENCE_TIME)
        create_concert(db_session, tour, venues[2], day_offset=10, ticket_price="50.00", base_time=REFERENCE_TIME)

        response = client.get(PAGE_ENDPOINT)
        assert response.status_code == 200

        html = response.text
        positions = [html.index(venues[1].name), html.index(venues[2].name), html.index(venues[0].name)]
        assert positions == sorted(positions)

    def test_next_concert_marker_appears_once_on_soonest_upcoming_row(self, client, db_session):
        venues = create_venues(db_session, count=3)
        tour = _make_tour(db_session)

        create_concert(db_session, tour, venues[0], day_offset=-5, ticket_price="50.00", base_time=REFERENCE_TIME)
        create_concert(db_session, tour, venues[1], day_offset=10, ticket_price="50.00", base_time=REFERENCE_TIME)
        create_concert(db_session, tour, venues[2], day_offset=1, ticket_price="50.00", base_time=REFERENCE_TIME)

        response = client.get(PAGE_ENDPOINT, params={"include_past": "true"})
        assert response.status_code == 200

        html = response.text
        assert html.count("next-concert") == 1
        assert html.count("Next concert") == 1

        next_concert_position = html.index("next-concert")
        soonest_venue_position = html.index(venues[2].name)
        later_venue_position = html.index(venues[1].name)
        assert next_concert_position < soonest_venue_position < later_venue_position

    def test_empty_state_message_and_no_marker_when_no_tour_dates(self, client, db_session):
        response = client.get(PAGE_ENDPOINT)
        assert response.status_code == 200

        html = response.text
        assert "No tour dates scheduled yet." in html
        assert "next-concert" not in html
        assert "Next concert" not in html

    def test_venue_name_with_script_tag_is_escaped(self, client, db_session):
        venues = create_venues(db_session, count=1)
        tour = _make_tour(db_session)
        venue = venues[0]
        venue.name = "<script>alert(1)</script>"
        db_session.add(venue)
        db_session.commit()

        create_concert(db_session, tour, venue, day_offset=1, ticket_price="50.00", base_time=REFERENCE_TIME)

        response = client.get(PAGE_ENDPOINT)
        assert response.status_code == 200

        assert "<script>alert(1)</script>" not in response.text
        assert "&lt;script&gt;alert(1)&lt;/script&gt;" in response.text
