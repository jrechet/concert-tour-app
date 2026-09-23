"""Tests for GET /api/v1/concerts/cities and the city filter dropdown it
feeds on the dashboard concert list.
"""

from datetime import datetime, timedelta

from src.models import Venue
from tests.fixtures.dashboard_fixtures import create_concert, create_tour, create_venues


def _seed_tour(db_session):
    return create_tour(
        db_session,
        name="City Filter Tour",
        artist="Test Artist",
        start_date=(datetime.now() - timedelta(days=1)).date(),
        end_date=(datetime.now() + timedelta(days=90)).date(),
        status="active",
    )


def test_get_concert_cities_returns_distinct_sorted_cities(client, db_session):
    tour = _seed_tour(db_session)
    venues = create_venues(db_session, count=3)  # New York, London, Paris
    base_time = datetime.now()
    for i, venue in enumerate(venues):
        create_concert(db_session, tour, venue, day_offset=i, ticket_price="50.00", base_time=base_time)
    # A second concert in the same city as an existing venue should not duplicate it.
    create_concert(db_session, tour, venues[0], day_offset=5, ticket_price="50.00", base_time=base_time)

    response = client.get("/api/v1/concerts/cities")

    assert response.status_code == 200
    assert response.json() == sorted(venue.city for venue in venues)


def test_get_concert_cities_excludes_cities_with_no_concerts(client, db_session):
    tour = _seed_tour(db_session)
    venue_with_concert = Venue(name="Arena One", city="Berlin", country="Germany", capacity=5000)
    venue_without_concert = Venue(name="Arena Two", city="Rome", country="Italy", capacity=5000)
    db_session.add_all([venue_with_concert, venue_without_concert])
    db_session.commit()
    db_session.refresh(venue_with_concert)
    create_concert(db_session, tour, venue_with_concert, day_offset=1, ticket_price="50.00", base_time=datetime.now())

    response = client.get("/api/v1/concerts/cities")

    assert response.status_code == 200
    assert response.json() == ["Berlin"]


def test_get_concert_cities_returns_empty_list_when_no_concerts(client, db_session):
    response = client.get("/api/v1/concerts/cities")

    assert response.status_code == 200
    assert response.json() == []


def test_cities_route_is_not_shadowed_by_concert_detail_route(client, db_session):
    """`/cities` must resolve to the cities list, not be swallowed by the
    `/{concert_id}` detail route as an invalid id."""
    response = client.get("/api/v1/concerts/cities")

    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_dashboard_contains_city_filter_select(client):
    """The dashboard shell renders a city filter dropdown with the default
    "All cities" option, above the concert list."""
    response = client.get("/dashboard")

    assert response.status_code == 200
    assert 'id="city-filter-select"' in response.text
    assert '<option value="">All cities</option>' in response.text
    assert response.text.index('id="city-filter-select"') < response.text.index('id="calendar-grid"')


def test_concert_search_js_populates_and_wires_city_filter_select():
    """The JS module fetches the cities endpoint to populate the dropdown
    and re-queries the concert list, scoped to the chosen city, on change."""
    from pathlib import Path

    js_source = Path("src/static/js/concert-search.js").read_text()

    assert '"/api/v1/concerts/cities"' in js_source
    assert "city-filter-select" in js_source
    assert 'addEventListener("change"' in js_source
