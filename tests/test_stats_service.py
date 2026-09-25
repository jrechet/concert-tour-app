"""Tests for `src.services.stats_service` query logic."""

from datetime import datetime, timedelta

from src.models import Venue
from src.services.stats_service import get_distinct_cities, get_distinct_venue_names
from tests.fixtures.dashboard_fixtures import create_concert, create_tour, create_venues


def _seed_tour(db_session):
    return create_tour(
        db_session,
        name="Stats Service Tour",
        artist="Test Artist",
        start_date=(datetime.now() - timedelta(days=1)).date(),
        end_date=(datetime.now() + timedelta(days=90)).date(),
        status="active",
    )


def test_get_distinct_cities_returns_sorted_deduplicated_cities(db_session):
    tour = _seed_tour(db_session)
    venues = create_venues(db_session, count=3)
    base_time = datetime.now()
    for i, venue in enumerate(venues):
        create_concert(db_session, tour, venue, day_offset=i, ticket_price="50.00", base_time=base_time)
    # A second concert at the same venue/city should not produce a duplicate.
    create_concert(db_session, tour, venues[0], day_offset=5, ticket_price="50.00", base_time=base_time)

    result = get_distinct_cities(db_session)

    expected = sorted({venue.city for venue in venues})
    assert result == expected
    assert len(result) == len(set(result))


def test_get_distinct_cities_excludes_venues_with_no_concerts(db_session):
    tour = _seed_tour(db_session)
    venue_with_concert = Venue(name="Arena One", city="Berlin", country="Germany", capacity=5000)
    venue_without_concert = Venue(name="Arena Two", city="Rome", country="Italy", capacity=5000)
    db_session.add_all([venue_with_concert, venue_without_concert])
    db_session.commit()
    db_session.refresh(venue_with_concert)
    create_concert(db_session, tour, venue_with_concert, day_offset=1, ticket_price="50.00", base_time=datetime.now())

    result = get_distinct_cities(db_session)

    assert result == ["Berlin"]


def test_get_distinct_cities_returns_empty_list_when_no_concerts(db_session):
    assert get_distinct_cities(db_session) == []


def test_get_distinct_venue_names_returns_sorted_deduplicated_venues(db_session):
    tour = _seed_tour(db_session)
    venues = create_venues(db_session, count=3)
    base_time = datetime.now()
    for i, venue in enumerate(venues):
        create_concert(db_session, tour, venue, day_offset=i, ticket_price="50.00", base_time=base_time)
    # A second concert at the same venue should not produce a duplicate.
    create_concert(db_session, tour, venues[0], day_offset=5, ticket_price="50.00", base_time=base_time)

    result = get_distinct_venue_names(db_session)

    expected = sorted(venue.name for venue in venues)
    assert result == expected
    assert len(result) == len(set(result))


def test_get_distinct_venue_names_excludes_venues_with_no_concerts(db_session):
    tour = _seed_tour(db_session)
    venue_with_concert = Venue(name="Arena One", city="Berlin", country="Germany", capacity=5000)
    venue_without_concert = Venue(name="Arena Two", city="Rome", country="Italy", capacity=5000)
    db_session.add_all([venue_with_concert, venue_without_concert])
    db_session.commit()
    db_session.refresh(venue_with_concert)
    create_concert(db_session, tour, venue_with_concert, day_offset=1, ticket_price="50.00", base_time=datetime.now())

    result = get_distinct_venue_names(db_session)

    assert result == ["Arena One"]


def test_get_distinct_venue_names_returns_empty_list_when_no_concerts(db_session):
    assert get_distinct_venue_names(db_session) == []
