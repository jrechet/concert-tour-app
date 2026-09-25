"""Tests for GET /api/v1/stats/cities, GET /api/v1/stats/venues,
GET /api/v1/stats/count, and GET /api/v1/stats/upcoming-count."""

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


def test_get_count_returns_zero_when_no_concerts(client, db_session):
    response = client.get("/api/v1/stats/count")

    assert response.status_code == 200
    assert response.json() == {"count": 0}


def test_get_count_counts_all_concerts_regardless_of_date(client, db_session):
    tour = _seed_tour(db_session)
    venues = create_venues(db_session, count=4)
    base_time = datetime.now()
    day_offsets = [-30, -1, 0, 15]
    for venue, offset in zip(venues, day_offsets):
        create_concert(db_session, tour, venue, day_offset=offset, ticket_price="50.00", base_time=base_time)

    response = client.get("/api/v1/stats/count")

    assert response.status_code == 200
    assert response.json() == {"count": len(day_offsets)}


def test_get_count_response_shape(client, db_session):
    tour = _seed_tour(db_session)
    venue = create_venues(db_session, count=1)[0]
    create_concert(db_session, tour, venue, day_offset=1, ticket_price="50.00", base_time=datetime.now())

    response = client.get("/api/v1/stats/count")

    assert response.status_code == 200
    body = response.json()
    assert set(body.keys()) == {"count"}
    assert isinstance(body["count"], int)


def test_get_upcoming_count_returns_zero_when_no_concerts(client, db_session):
    response = client.get("/api/v1/stats/upcoming-count")

    assert response.status_code == 200
    assert response.json() == {"count": 0}


def test_get_upcoming_count_counts_all_seeded_concerts_when_all_upcoming(client, db_session):
    tour = _seed_tour(db_session)
    venues = create_venues(db_session, count=3)
    base_time = datetime.now()
    day_offsets = [0, 5, 20]
    for venue, offset in zip(venues, day_offsets):
        create_concert(db_session, tour, venue, day_offset=offset, ticket_price="50.00", base_time=base_time)

    response = client.get("/api/v1/stats/upcoming-count")

    assert response.status_code == 200
    assert response.json() == {"count": len(day_offsets)}


def test_get_upcoming_count_excludes_past_concerts(client, db_session):
    tour = _seed_tour(db_session)
    venues = create_venues(db_session, count=4)
    base_time = datetime.now()
    day_offsets = [-10, -1, 3, 15]
    for venue, offset in zip(venues, day_offsets):
        create_concert(db_session, tour, venue, day_offset=offset, ticket_price="50.00", base_time=base_time)

    response = client.get("/api/v1/stats/upcoming-count")

    assert response.status_code == 200
    assert response.json() == {"count": 2}


def test_get_upcoming_count_includes_concert_scheduled_exactly_today(client, db_session):
    tour = _seed_tour(db_session)
    venues = create_venues(db_session, count=2)
    base_time = datetime.now()
    create_concert(db_session, tour, venues[0], day_offset=0, ticket_price="50.00", base_time=base_time)
    create_concert(db_session, tour, venues[1], day_offset=-2, ticket_price="50.00", base_time=base_time)

    response = client.get("/api/v1/stats/upcoming-count")

    assert response.status_code == 200
    assert response.json() == {"count": 1}


def test_get_upcoming_count_response_shape(client, db_session):
    tour = _seed_tour(db_session)
    venue = create_venues(db_session, count=1)[0]
    create_concert(db_session, tour, venue, day_offset=1, ticket_price="50.00", base_time=datetime.now())

    response = client.get("/api/v1/stats/upcoming-count")

    assert response.status_code == 200
    body = response.json()
    assert set(body.keys()) == {"count"}
    assert isinstance(body["count"], int)
