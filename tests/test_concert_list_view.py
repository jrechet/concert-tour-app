"""Tests for the HTMX-driven concert list page (GET /concerts): the full
page on a plain request, the rows partial on an `HX-Request`, city
filtering, the empty-state message, and HTML-escaping of the echoed
search term.
"""

from datetime import datetime, timedelta

from src.models import Venue
from tests.fixtures.dashboard_fixtures import create_concert, create_tour, create_venues


def _seed_tour_and_venue(db_session, city="Paris"):
    tour = create_tour(
        db_session,
        name="List View Tour",
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


def test_full_page_load_renders_search_box_and_every_concert(client, db_session):
    tour = create_tour(
        db_session,
        name="Full Page Tour",
        artist="Test Artist",
        start_date=(datetime.now() - timedelta(days=1)).date(),
        end_date=(datetime.now() + timedelta(days=90)).date(),
        status="active",
    )
    venues = create_venues(db_session, count=3)
    base_time = datetime.now()
    for i, venue in enumerate(venues):
        create_concert(db_session, tour, venue, day_offset=i, ticket_price="50.00", base_time=base_time)

    response = client.get("/concerts")

    assert response.status_code == 200
    assert "<html" in response.text
    assert 'id="concert-city-search-input"' in response.text
    for venue in venues:
        assert venue.city in response.text


def test_htmx_request_returns_partial_only(client, db_session):
    tour, venue = _seed_tour_and_venue(db_session, city="Paris")
    create_concert(db_session, tour, venue, day_offset=1, ticket_price="50.00", base_time=datetime.now())

    response = client.get("/concerts", headers={"HX-Request": "true"})

    assert response.status_code == 200
    assert "<html" not in response.text
    assert "<body" not in response.text
    assert venue.city in response.text


def test_htmx_city_filter_returns_only_matching_concerts(client, db_session):
    tour, paris_venue = _seed_tour_and_venue(db_session, city="Paris")
    create_concert(db_session, tour, paris_venue, day_offset=1, ticket_price="50.00", base_time=datetime.now())
    berlin_tour, berlin_venue = _seed_tour_and_venue(db_session, city="Berlin")
    create_concert(db_session, berlin_tour, berlin_venue, day_offset=2, ticket_price="60.00", base_time=datetime.now())

    response = client.get("/concerts", params={"city": "Paris"}, headers={"HX-Request": "true"})

    assert response.status_code == 200
    assert "Paris" in response.text
    assert "Berlin" not in response.text


def test_htmx_empty_city_returns_every_concert(client, db_session):
    tour, paris_venue = _seed_tour_and_venue(db_session, city="Paris")
    create_concert(db_session, tour, paris_venue, day_offset=1, ticket_price="50.00", base_time=datetime.now())
    berlin_tour, berlin_venue = _seed_tour_and_venue(db_session, city="Berlin")
    create_concert(db_session, berlin_tour, berlin_venue, day_offset=2, ticket_price="60.00", base_time=datetime.now())

    response = client.get("/concerts", params={"city": ""}, headers={"HX-Request": "true"})

    assert response.status_code == 200
    assert "Paris" in response.text
    assert "Berlin" in response.text


def test_htmx_no_match_renders_empty_state_message(client, db_session):
    tour, venue = _seed_tour_and_venue(db_session, city="Paris")
    create_concert(db_session, tour, venue, day_offset=1, ticket_price="50.00", base_time=datetime.now())

    response = client.get("/concerts", params={"city": "Atlantis"}, headers={"HX-Request": "true"})

    assert response.status_code == 200
    assert "No concerts found" in response.text
    assert "Paris" not in response.text


def test_city_value_with_script_tag_is_escaped(client, db_session):
    tour, venue = _seed_tour_and_venue(db_session, city="Paris")
    create_concert(db_session, tour, venue, day_offset=1, ticket_price="50.00", base_time=datetime.now())

    response = client.get(
        "/concerts", params={"city": "<script>alert(1)</script>"}, headers={"HX-Request": "true"}
    )

    assert response.status_code == 200
    assert "<script>" not in response.text
