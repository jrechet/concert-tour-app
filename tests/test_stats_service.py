"""Tests for `src.services.stats_service` query logic."""

from datetime import datetime, timedelta

from src.models import Venue
from src.services.stats_service import (
    get_concert_counts_by_country,
    get_concert_counts_by_month,
    get_distinct_cities,
    get_distinct_venue_names,
    get_price_stats,
)
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


def test_get_concert_counts_by_country_excludes_country_with_only_cancelled_concerts(db_session):
    tour = _seed_tour(db_session)
    venue_germany = Venue(name="Arena Berlin", city="Berlin", country="Germany", capacity=5000)
    venue_italy = Venue(name="Arena Rome", city="Rome", country="Italy", capacity=5000)
    db_session.add_all([venue_germany, venue_italy])
    db_session.commit()
    db_session.refresh(venue_germany)
    db_session.refresh(venue_italy)
    base_time = datetime.now()
    create_concert(
        db_session, tour, venue_germany, day_offset=1, ticket_price="50.00", base_time=base_time,
        is_cancelled=True, cancellation_reason="Artist illness",
    )
    create_concert(db_session, tour, venue_italy, day_offset=2, ticket_price="50.00", base_time=base_time)

    result = get_concert_counts_by_country(db_session)

    assert result == [("Italy", 1)]
    assert "Germany" not in [country for country, _ in result]


def test_get_concert_counts_by_country_orders_by_count_descending(db_session):
    tour = _seed_tour(db_session)
    venue_germany = Venue(name="Arena Berlin", city="Berlin", country="Germany", capacity=5000)
    venue_france = Venue(name="Arena Paris", city="Paris", country="France", capacity=5000)
    venue_italy = Venue(name="Arena Rome", city="Rome", country="Italy", capacity=5000)
    db_session.add_all([venue_germany, venue_france, venue_italy])
    db_session.commit()
    for venue in (venue_germany, venue_france, venue_italy):
        db_session.refresh(venue)
    base_time = datetime.now()
    for i in range(3):
        create_concert(db_session, tour, venue_germany, day_offset=i, ticket_price="50.00", base_time=base_time)
    for i in range(2):
        create_concert(db_session, tour, venue_france, day_offset=10 + i, ticket_price="50.00", base_time=base_time)
    create_concert(db_session, tour, venue_italy, day_offset=20, ticket_price="50.00", base_time=base_time)

    result = get_concert_counts_by_country(db_session)

    assert result == [("Germany", 3), ("France", 2), ("Italy", 1)]


def test_get_concert_counts_by_country_counts_mixed_cancelled_and_active_concerts(db_session):
    tour = _seed_tour(db_session)
    venue = Venue(name="Arena Berlin", city="Berlin", country="Germany", capacity=5000)
    db_session.add(venue)
    db_session.commit()
    db_session.refresh(venue)
    base_time = datetime.now()
    create_concert(db_session, tour, venue, day_offset=1, ticket_price="50.00", base_time=base_time)
    create_concert(db_session, tour, venue, day_offset=2, ticket_price="50.00", base_time=base_time)
    create_concert(
        db_session, tour, venue, day_offset=3, ticket_price="50.00", base_time=base_time,
        is_cancelled=True, cancellation_reason="Venue unavailable",
    )

    result = get_concert_counts_by_country(db_session)

    assert result == [("Germany", 2)]


def test_get_concert_counts_by_country_returns_empty_list_when_no_concerts(db_session):
    assert get_concert_counts_by_country(db_session) == []


def test_get_concert_counts_by_month_groups_and_orders_chronologically(db_session):
    tour = _seed_tour(db_session)
    venue = create_venues(db_session, count=1)[0]
    base_time = datetime(2026, 1, 15)
    # March, then January, then February, seeded out of order.
    create_concert(db_session, tour, venue, day_offset=50, ticket_price="50.00", base_time=base_time)
    create_concert(db_session, tour, venue, day_offset=0, ticket_price="50.00", base_time=base_time)
    create_concert(db_session, tour, venue, day_offset=1, ticket_price="50.00", base_time=base_time)
    create_concert(db_session, tour, venue, day_offset=20, ticket_price="50.00", base_time=base_time)

    result = get_concert_counts_by_month(db_session)

    assert result == [("2026-01", 2), ("2026-02", 1), ("2026-03", 1)]


def test_get_concert_counts_by_month_excludes_cancelled_concerts(db_session):
    tour = _seed_tour(db_session)
    venue = create_venues(db_session, count=1)[0]
    base_time = datetime(2026, 1, 15)
    create_concert(db_session, tour, venue, day_offset=0, ticket_price="50.00", base_time=base_time)
    create_concert(
        db_session, tour, venue, day_offset=1, ticket_price="50.00", base_time=base_time,
        is_cancelled=True, cancellation_reason="Artist illness",
    )

    result = get_concert_counts_by_month(db_session)

    assert result == [("2026-01", 1)]


def test_get_concert_counts_by_month_omits_months_with_only_cancelled_concerts(db_session):
    tour = _seed_tour(db_session)
    venue = create_venues(db_session, count=1)[0]
    base_time = datetime(2026, 1, 15)
    create_concert(
        db_session, tour, venue, day_offset=0, ticket_price="50.00", base_time=base_time,
        is_cancelled=True, cancellation_reason="Venue unavailable",
    )
    create_concert(db_session, tour, venue, day_offset=20, ticket_price="50.00", base_time=base_time)

    result = get_concert_counts_by_month(db_session)

    assert result == [("2026-02", 1)]


def test_get_concert_counts_by_month_returns_empty_list_when_no_concerts(db_session):
    assert get_concert_counts_by_month(db_session) == []


def test_get_price_stats_returns_none_triple_when_no_concerts(db_session):
    result = get_price_stats(db_session)

    assert result.lowest is None
    assert result.average is None
    assert result.highest is None


def test_get_price_stats_computes_min_avg_max_over_upcoming_priced_concerts(db_session):
    tour = _seed_tour(db_session)
    venue = create_venues(db_session, count=1)[0]
    base_time = datetime.now()
    create_concert(db_session, tour, venue, day_offset=1, ticket_price="50.00", base_time=base_time)
    create_concert(db_session, tour, venue, day_offset=2, ticket_price="100.00", base_time=base_time)
    create_concert(db_session, tour, venue, day_offset=3, ticket_price="150.00", base_time=base_time)

    result = get_price_stats(db_session)

    assert result.lowest == 50.0
    assert result.average == 100.0
    assert result.highest == 150.0


def test_get_price_stats_excludes_cancelled_concerts(db_session):
    tour = _seed_tour(db_session)
    venue = create_venues(db_session, count=1)[0]
    base_time = datetime.now()
    create_concert(db_session, tour, venue, day_offset=1, ticket_price="50.00", base_time=base_time)
    create_concert(
        db_session, tour, venue, day_offset=2, ticket_price="1000.00", base_time=base_time,
        is_cancelled=True, cancellation_reason="Artist illness",
    )

    result = get_price_stats(db_session)

    assert result.lowest == 50.0
    assert result.average == 50.0
    assert result.highest == 50.0


def test_get_price_stats_excludes_past_concerts(db_session):
    tour = _seed_tour(db_session)
    venue = create_venues(db_session, count=1)[0]
    base_time = datetime.now()
    create_concert(db_session, tour, venue, day_offset=-5, ticket_price="1000.00", base_time=base_time)
    create_concert(db_session, tour, venue, day_offset=1, ticket_price="50.00", base_time=base_time)

    result = get_price_stats(db_session)

    assert result.lowest == 50.0
    assert result.average == 50.0
    assert result.highest == 50.0


def test_get_price_stats_excludes_concerts_with_no_price(db_session):
    tour = _seed_tour(db_session)
    venue = create_venues(db_session, count=1)[0]
    base_time = datetime.now()
    create_concert(db_session, tour, venue, day_offset=1, ticket_price=None, base_time=base_time)
    create_concert(db_session, tour, venue, day_offset=2, ticket_price="75.00", base_time=base_time)

    result = get_price_stats(db_session)

    assert result.lowest == 75.0
    assert result.average == 75.0
    assert result.highest == 75.0


def test_get_price_stats_returns_none_triple_when_only_ineligible_concerts(db_session):
    tour = _seed_tour(db_session)
    venue = create_venues(db_session, count=1)[0]
    base_time = datetime.now()
    create_concert(db_session, tour, venue, day_offset=-1, ticket_price="50.00", base_time=base_time)
    create_concert(db_session, tour, venue, day_offset=1, ticket_price=None, base_time=base_time)
    create_concert(
        db_session, tour, venue, day_offset=2, ticket_price="60.00", base_time=base_time,
        is_cancelled=True, cancellation_reason="Venue unavailable",
    )

    result = get_price_stats(db_session)

    assert result.lowest is None
    assert result.average is None
    assert result.highest is None
