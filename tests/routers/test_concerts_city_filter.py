"""Tests for the `city` filter on the HTMX concert list page (`GET /concerts`):
unfiltered/filtered/cleared/no-match results, the over-length validation
error, the HTMX-partial-vs-full-page split, and HTML-escaping of the
echoed search term.
"""

from datetime import datetime, timedelta

from src.models import Venue
from src.services.concerts_service import MAX_CITY_QUERY_LENGTH
from tests.fixtures.dashboard_fixtures import create_concert, create_tour


def _seed_tour_and_venue(db_session, city):
    tour = create_tour(
        db_session,
        name=f"{city} City Filter Tour",
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


def _seed_paris_and_berlin(db_session):
    paris_tour, paris_venue = _seed_tour_and_venue(db_session, "Paris")
    create_concert(db_session, paris_tour, paris_venue, day_offset=1, ticket_price="50.00", base_time=datetime.now())
    berlin_tour, berlin_venue = _seed_tour_and_venue(db_session, "Berlin")
    create_concert(db_session, berlin_tour, berlin_venue, day_offset=2, ticket_price="60.00", base_time=datetime.now())


def test_no_city_param_returns_every_concert(client, db_session):
    _seed_paris_and_berlin(db_session)

    response = client.get("/concerts")

    assert response.status_code == 200
    assert "Paris" in response.text
    assert "Berlin" in response.text


def test_city_param_filters_case_insensitively(client, db_session):
    _seed_paris_and_berlin(db_session)

    response = client.get("/concerts", params={"city": "par"})

    assert response.status_code == 200
    assert "Paris" in response.text
    assert "Berlin" not in response.text


def test_blank_city_param_restores_every_concert(client, db_session):
    _seed_paris_and_berlin(db_session)

    response = client.get("/concerts", params={"city": ""})

    assert response.status_code == 200
    assert "Paris" in response.text
    assert "Berlin" in response.text


def test_no_matching_city_returns_empty_state_not_404(client, db_session):
    _seed_paris_and_berlin(db_session)

    response = client.get("/concerts", params={"city": "Atlantis"})

    assert response.status_code == 200
    assert "No concerts found" in response.text
    assert "Paris" not in response.text
    assert "Berlin" not in response.text


def test_overlength_city_returns_422_and_skips_the_database(client, db_session):
    """FastAPI's `Query(max_length=...)` rejects an over-length `city` before
    the route body (and therefore any database query) ever runs."""
    _seed_paris_and_berlin(db_session)
    overlength_city = "x" * (MAX_CITY_QUERY_LENGTH + 1)

    response = client.get("/concerts", params={"city": overlength_city})

    assert response.status_code == 422


def test_htmx_request_returns_rows_partial_only(client, db_session):
    _seed_paris_and_berlin(db_session)

    full_page = client.get("/concerts")
    htmx_response = client.get("/concerts", headers={"HX-Request": "true"})

    assert full_page.status_code == 200
    assert "<html" in full_page.text
    assert "<body" in full_page.text

    assert htmx_response.status_code == 200
    assert "<html" not in htmx_response.text
    assert "<body" not in htmx_response.text

    for city in ("Paris", "Berlin"):
        assert city in full_page.text
        assert city in htmx_response.text


def test_city_value_with_script_tag_is_escaped(client, db_session):
    _seed_tour_and_venue(db_session, "Paris")

    response = client.get(
        "/concerts", params={"city": "<script>alert(1)</script>"}, headers={"HX-Request": "true"}
    )

    assert response.status_code == 200
    assert "<script>" not in response.text
    assert "&lt;script&gt;" in response.text
