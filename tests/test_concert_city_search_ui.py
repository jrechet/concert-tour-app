"""Tests for the debounced city search box on the dashboard concert list.

Covers the markup on the dashboard shell (a "Filter by city" input plus the
`concert-search.js` module wired to it), the `venue_name`/`venue_city`
fields the JS needs from `GET /api/v1/concerts/` to render cards client
side, and that XSS-unsafe venue data is escaped by the renderer's own
`escapeHtml` helper.
"""

from datetime import datetime, timedelta

from src.models import Venue
from tests.fixtures.dashboard_fixtures import create_concert, create_tour, create_venues


def _seed_tour_and_venue(db_session, city="Paris"):
    tour = create_tour(
        db_session,
        name="City Search Tour",
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


def test_dashboard_contains_city_search_input(client):
    """The dashboard shell renders a "Filter by city" input and loads the
    concert-search.js module that drives it."""
    response = client.get("/dashboard")

    assert response.status_code == 200
    assert 'id="city-search-input"' in response.text
    assert 'placeholder="Filter by city"' in response.text
    assert "concert-search.js" in response.text


def test_concert_search_js_is_served_and_debounces(client):
    """The JS module is served as a static asset and debounces input by
    ~300ms before calling the concerts API."""
    response = client.get("/static/js/concert-search.js")

    assert response.status_code == 200
    body = response.text
    assert "DEBOUNCE_MS = 300" in body
    assert '"/api/v1/concerts/"' in body
    assert "city-search-input" in body
    assert "calendar-grid" in body
    assert "No concerts found." in body


def test_get_concerts_includes_venue_name_and_city(client, db_session):
    """The concerts JSON API exposes venue name/city so the search box can
    render a readable card without a second lookup."""
    tour, venue = _seed_tour_and_venue(db_session, city="Paris")
    create_concert(
        db_session, tour, venue, day_offset=1, ticket_price="50.00",
        base_time=datetime.now(), tickets_sold=0,
    )

    response = client.get("/api/v1/concerts/")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["venue_name"] == venue.name
    assert data[0]["venue_city"] == "Paris"


def test_get_concerts_city_filter_is_case_insensitive_for_lowercase_query(client, db_session):
    """Typing "paris" (lowercase) still matches a venue in "Paris"."""
    tour, venue = _seed_tour_and_venue(db_session, city="Paris")
    create_concert(
        db_session, tour, venue, day_offset=1, ticket_price="50.00",
        base_time=datetime.now(), tickets_sold=0,
    )
    other_tour, other_venue = _seed_tour_and_venue(db_session, city="Berlin")
    create_concert(
        db_session, other_tour, other_venue, day_offset=2, ticket_price="60.00",
        base_time=datetime.now(), tickets_sold=0,
    )

    response = client.get("/api/v1/concerts/?city=paris")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["venue_city"] == "Paris"


def test_get_concerts_no_matching_city_returns_empty_list(client, db_session):
    """A city with no concerts returns an empty list, which the client
    renders as a "no concerts found" empty state."""
    tour, venue = _seed_tour_and_venue(db_session, city="Paris")
    create_concert(
        db_session, tour, venue, day_offset=1, ticket_price="50.00",
        base_time=datetime.now(), tickets_sold=0,
    )

    response = client.get("/api/v1/concerts/?city=Atlantis")

    assert response.status_code == 200
    assert response.json() == []


def test_get_concerts_blank_city_restores_full_list(client, db_session):
    """No `city` param (a cleared search box) returns every concert."""
    tour = create_tour(
        db_session,
        name="Full List Tour",
        artist="Test Artist",
        start_date=(datetime.now() - timedelta(days=1)).date(),
        end_date=(datetime.now() + timedelta(days=90)).date(),
        status="active",
    )
    venues = create_venues(db_session, count=3)
    base_time = datetime.now()
    for i, venue in enumerate(venues):
        create_concert(
            db_session, tour, venue, day_offset=i, ticket_price="50.00",
            base_time=base_time, tickets_sold=0,
        )

    response = client.get("/api/v1/concerts/")

    assert response.status_code == 200
    assert len(response.json()) == 3


def test_get_concerts_venue_name_and_city_are_escaped_source_data(client, db_session):
    """The API returns raw venue data (escaping happens client-side in
    concert-search.js's escapeHtml, mirroring the server-side `|e` filter
    used elsewhere); confirm the raw value round-trips untouched so the
    client has something safe to escape."""
    tour, venue = _seed_tour_and_venue(db_session, city="<script>alert('xss')</script>")
    create_concert(
        db_session, tour, venue, day_offset=1, ticket_price="50.00",
        base_time=datetime.now(), tickets_sold=0,
    )

    response = client.get("/api/v1/concerts/")

    assert response.status_code == 200
    data = response.json()
    assert data[0]["venue_city"] == "<script>alert('xss')</script>"


def test_concert_search_js_escapes_rendered_values():
    """The renderer escapes every field it interpolates (venue name/city,
    ticket count, cancellation reason) via a shared escapeHtml helper
    rather than string-concatenating raw values."""
    from pathlib import Path

    js_source = Path("src/static/js/concert-search.js").read_text()

    assert "function escapeHtml(" in js_source
    for field in ("venue_name", "venue_city", "cancellation_reason", "remaining_tickets"):
        assert f"escapeHtml(concert.{field})" in js_source
