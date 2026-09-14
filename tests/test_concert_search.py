"""Tests for the live artist-name search box wired into the dashboard.

Covers the HTMX markup on the dashboard shell (search input targeting the
`#calendar-grid` concert-list partial with a debounced trigger) and the
`artist_name` filter behavior of the `GET /api/v1/dashboard/concerts`
fragment endpoint it calls: case-insensitive partial matching, restoring
the full list on a blank query, and the no-match empty state.
"""

from datetime import datetime, timedelta

from src.models import Venue
from tests.fixtures.dashboard_fixtures import create_concert, create_tour


def _seed_tour_with_artist(db_session, artist, name=None):
    """A tour with its own dedicated (uniquely-named) venue for a specific
    artist, real FKs throughout.

    Builds the venue directly rather than via `create_venues`, which always
    returns the same leading slice of its template list — reusing it across
    multiple artists in one test would give every venue an identical name.
    """
    tour = create_tour(
        db_session,
        name=name or f"{artist} Tour",
        artist=artist,
        start_date=(datetime.now() - timedelta(days=1)).date(),
        end_date=(datetime.now() + timedelta(days=90)).date(),
        status="active",
    )
    venue = Venue(name=f"{artist} Arena", city="Testville", country="USA", capacity=5000)
    db_session.add(venue)
    db_session.commit()
    db_session.refresh(venue)
    return tour, venue


def test_dashboard_contains_debounced_search_input(client):
    """The dashboard shell renders a search box wired to the concert-list
    partial via a debounced HTMX trigger, not a full page reload."""
    response = client.get("/dashboard")

    assert response.status_code == 200
    assert 'name="artist_name"' in response.text
    assert 'hx-get="/api/v1/dashboard/concerts"' in response.text
    assert "keyup changed delay:300ms" in response.text
    assert 'hx-target="#calendar-grid"' in response.text


def test_dashboard_concerts_filters_by_partial_case_insensitive_artist_name(client, db_session):
    tour, venue = _seed_tour_with_artist(db_session, "Aurora Belle")
    create_concert(
        db_session, tour, venue, day_offset=1, ticket_price="50.00",
        base_time=datetime.now(), tickets_sold=0,
    )
    other_tour, other_venue = _seed_tour_with_artist(db_session, "River Stone")
    create_concert(
        db_session, other_tour, other_venue, day_offset=2, ticket_price="60.00",
        base_time=datetime.now(), tickets_sold=0,
    )

    response = client.get("/api/v1/dashboard/concerts?artist_name=aurora")

    assert response.status_code == 200
    assert venue.name in response.text
    assert other_venue.name not in response.text


def test_dashboard_concerts_blank_artist_name_returns_full_list(client, db_session):
    tour, venue = _seed_tour_with_artist(db_session, "Aurora Belle")
    create_concert(
        db_session, tour, venue, day_offset=1, ticket_price="50.00",
        base_time=datetime.now(), tickets_sold=0,
    )
    other_tour, other_venue = _seed_tour_with_artist(db_session, "River Stone")
    create_concert(
        db_session, other_tour, other_venue, day_offset=2, ticket_price="60.00",
        base_time=datetime.now(), tickets_sold=0,
    )

    response = client.get("/api/v1/dashboard/concerts?artist_name=")

    assert response.status_code == 200
    assert venue.name in response.text
    assert other_venue.name in response.text


def test_dashboard_concerts_no_match_shows_empty_state(client, db_session):
    tour, venue = _seed_tour_with_artist(db_session, "Aurora Belle")
    create_concert(
        db_session, tour, venue, day_offset=1, ticket_price="50.00",
        base_time=datetime.now(), tickets_sold=0,
    )

    response = client.get("/api/v1/dashboard/concerts?artist_name=Nonexistent Artist")

    assert response.status_code == 200
    assert "No concerts scheduled" in response.text
    assert venue.name not in response.text


def test_dashboard_concerts_search_response_still_escapes_venue_name(client, db_session):
    """Filtering by artist must not bypass the existing XSS escaping on
    echoed venue data in the concert-card partial."""
    from src.models import Venue

    venue = Venue(name="<script>alert('xss')</script>", city="Testville", country="USA", capacity=100)
    db_session.add(venue)
    db_session.commit()
    db_session.refresh(venue)
    tour = create_tour(
        db_session,
        name="XSS Search Tour",
        artist="Search Artist",
        start_date=(datetime.now() - timedelta(days=1)).date(),
        end_date=(datetime.now() + timedelta(days=90)).date(),
        status="active",
    )
    create_concert(
        db_session, tour, venue, day_offset=1, ticket_price="50.00",
        base_time=datetime.now(), tickets_sold=0,
    )

    response = client.get("/api/v1/dashboard/concerts?artist_name=search")

    assert response.status_code == 200
    assert "<script>alert" not in response.text
    assert "&lt;script&gt;" in response.text
