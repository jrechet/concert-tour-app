"""Tests for the live-filtering city search box on the concert list page
(`GET /concerts`): the HTMX attributes wired onto the input, the filtered
and cleared swaps it triggers, the value/escaping round-trip on a full
page reload, and the accessible wiring between the input, its label, and
the rows container it targets.
"""

import re
from datetime import datetime, timedelta

from src.models import Venue
from tests.fixtures.dashboard_fixtures import create_concert, create_tour


def _seed_tour_and_venue(db_session, city="Paris"):
    tour = create_tour(
        db_session,
        name="Search Box Tour",
        artist="Test Artist",
        start_date=(datetime.now() - timedelta(days=1)).date(),
        end_date=(datetime.now() + timedelta(days=90)).date(),
        status="active",
    )
    venue = Venue(name=f"{city} Arena", city=city, country="Testland", capacity=5000)
    db_session.add(venue)
    db_session.commit()
    db_session.refresh(venue)
    return tour, venue


def test_search_input_has_expected_htmx_attributes(client):
    """The input is named `city`, is a `type=search` box, and is wired via
    HTMX to a debounced `GET /concerts` that swaps the rows container."""
    response = client.get("/concerts")
    html = response.text

    assert response.status_code == 200
    input_match = re.search(r"<input[^>]*name=\"city\"[^>]*>", html)
    assert input_match, "expected a <input name=\"city\"> search box"
    input_tag = input_match.group(0)

    assert 'type="search"' in input_tag
    assert 'hx-get="/concerts"' in input_tag
    assert re.search(r'hx-trigger="keyup changed delay:\d+ms, search"', input_tag)
    assert 'hx-target="#concert-list"' in input_tag
    assert 'hx-swap="innerHTML"' in input_tag
    assert "hx-indicator=" in input_tag


def test_typing_a_term_returns_only_matching_concerts(client, db_session):
    """Simulated keystrokes (`GET /concerts?city=par` with `HX-Request`)
    return 200 and a fragment containing only the matching concerts."""
    tour, paris_venue = _seed_tour_and_venue(db_session, city="Paris")
    create_concert(db_session, tour, paris_venue, day_offset=1, ticket_price="50.00", base_time=datetime.now())
    berlin_tour, berlin_venue = _seed_tour_and_venue(db_session, city="Berlin")
    create_concert(db_session, berlin_tour, berlin_venue, day_offset=2, ticket_price="60.00", base_time=datetime.now())

    response = client.get("/concerts", params={"city": "par"}, headers={"HX-Request": "true"})

    assert response.status_code == 200
    assert "Paris" in response.text
    assert "Berlin" not in response.text


def test_clearing_the_box_restores_every_concert(client, db_session):
    """Simulated clearing (`GET /concerts?city=` with `HX-Request`) returns
    200 and a fragment containing every concert."""
    tour, paris_venue = _seed_tour_and_venue(db_session, city="Paris")
    create_concert(db_session, tour, paris_venue, day_offset=1, ticket_price="50.00", base_time=datetime.now())
    berlin_tour, berlin_venue = _seed_tour_and_venue(db_session, city="Berlin")
    create_concert(db_session, berlin_tour, berlin_venue, day_offset=2, ticket_price="60.00", base_time=datetime.now())

    response = client.get("/concerts", params={"city": ""}, headers={"HX-Request": "true"})

    assert response.status_code == 200
    assert "Paris" in response.text
    assert "Berlin" in response.text


def test_full_page_reload_preserves_typed_term_as_input_value(client, db_session):
    """Rendering the full page with `?city=par` sets the input's `value`
    attribute to `par` so the term survives a full reload."""
    tour, venue = _seed_tour_and_venue(db_session, city="Paris")
    create_concert(db_session, tour, venue, day_offset=1, ticket_price="50.00", base_time=datetime.now())

    response = client.get("/concerts", params={"city": "par"})

    assert response.status_code == 200
    assert 'value="par"' in response.text


def test_script_tag_in_term_is_escaped_in_input_value(client, db_session):
    """A term containing `<script>` appears escaped in the input's value,
    with no raw `<script>` tag anywhere on the page."""
    tour, venue = _seed_tour_and_venue(db_session, city="Paris")
    create_concert(db_session, tour, venue, day_offset=1, ticket_price="50.00", base_time=datetime.now())

    response = client.get("/concerts", params={"city": "<script>alert(1)</script>"})

    assert response.status_code == 200
    assert "<script>" not in response.text
    assert "&lt;script&gt;" in response.text


def test_rows_container_and_label_are_wired_for_accessibility(client):
    """The rows container has a stable id matching `hx-target`, announces
    updates via `aria-live`, and the input has an accessible label that is
    associated with it (and, in turn, with the rows container)."""
    response = client.get("/concerts")
    html = response.text

    assert response.status_code == 200
    assert 'id="concert-list"' in html

    rows_container_match = re.search(r'<div[^>]*id="concert-list"[^>]*>', html)
    assert rows_container_match, "expected the rows container <div id=\"concert-list\">"
    rows_container_tag = rows_container_match.group(0)
    assert "aria-live=" in rows_container_tag

    input_match = re.search(r"<input[^>]*name=\"city\"[^>]*>", html)
    input_tag = input_match.group(0)
    assert 'aria-controls="concert-list"' in input_tag

    label_for_match = re.search(r'<label for="([^"]+)"', html)
    assert label_for_match, "expected a <label for=...> for the search input"
    assert f'id="{label_for_match.group(1)}"' in input_tag
