"""Tests for GET /api/v1/stats/cities and GET /api/v1/stats/venues."""

from datetime import datetime, timedelta

from src.models import Venue
from tests.fixtures.dashboard_fixtures import create_concert, create_tour, create_venues


def _seed_tour(db_session):
    return create_tour(
        db_session,
        name="Stats Tour",
        artist="Test Artist",
        start_date=(datetime.now() - timedelta(days=1)).date(),
        end_date=(datetime.now() + timedelta(days=90)).date(),
        status="active",
    )


def test_get_stats_cities_returns_distinct_sorted_cities(client, db_session):
    tour = _seed_tour(db_session)
    venues = create_venues(db_session, count=3)  # New York, London, Paris
    base_time = datetime.now()
    for i, venue in enumerate(venues):
        create_concert(db_session, tour, venue, day_offset=i, ticket_price="50.00", base_time=base_time)
    # A second concert in the same city as an existing venue should not duplicate it.
    create_concert(db_session, tour, venues[0], day_offset=5, ticket_price="50.00", base_time=base_time)

    response = client.get("/api/v1/stats/cities")

    assert response.status_code == 200
    assert response.json() == sorted(venue.city for venue in venues)


def test_get_stats_cities_excludes_cities_with_no_concerts(client, db_session):
    tour = _seed_tour(db_session)
    venue_with_concert = Venue(name="Arena One", city="Berlin", country="Germany", capacity=5000)
    venue_without_concert = Venue(name="Arena Two", city="Rome", country="Italy", capacity=5000)
    db_session.add_all([venue_with_concert, venue_without_concert])
    db_session.commit()
    db_session.refresh(venue_with_concert)
    create_concert(db_session, tour, venue_with_concert, day_offset=1, ticket_price="50.00", base_time=datetime.now())

    response = client.get("/api/v1/stats/cities")

    assert response.status_code == 200
    assert response.json() == ["Berlin"]


def test_get_stats_cities_returns_empty_list_when_no_concerts(client, db_session):
    response = client.get("/api/v1/stats/cities")

    assert response.status_code == 200
    assert response.json() == []


def test_get_stats_venues_returns_distinct_sorted_venues(client, db_session):
    tour = _seed_tour(db_session)
    venues = create_venues(db_session, count=3)
    base_time = datetime.now()
    for i, venue in enumerate(venues):
        create_concert(db_session, tour, venue, day_offset=i, ticket_price="50.00", base_time=base_time)
    # A second concert at the same venue should not duplicate it.
    create_concert(db_session, tour, venues[0], day_offset=5, ticket_price="50.00", base_time=base_time)

    response = client.get("/api/v1/stats/venues")

    assert response.status_code == 200
    assert response.json() == sorted(venue.name for venue in venues)


def test_get_stats_venues_excludes_venues_with_no_concerts(client, db_session):
    tour = _seed_tour(db_session)
    venue_with_concert = Venue(name="Arena One", city="Berlin", country="Germany", capacity=5000)
    venue_without_concert = Venue(name="Arena Two", city="Rome", country="Italy", capacity=5000)
    db_session.add_all([venue_with_concert, venue_without_concert])
    db_session.commit()
    db_session.refresh(venue_with_concert)
    create_concert(db_session, tour, venue_with_concert, day_offset=1, ticket_price="50.00", base_time=datetime.now())

    response = client.get("/api/v1/stats/venues")

    assert response.status_code == 200
    assert response.json() == ["Arena One"]


def test_get_stats_venues_returns_empty_list_when_no_concerts(client, db_session):
    response = client.get("/api/v1/stats/venues")

    assert response.status_code == 200
    assert response.json() == []
