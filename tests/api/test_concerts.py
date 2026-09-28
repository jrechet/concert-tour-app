"""End-to-end integration tests for the `min_price`/`max_price` filter on
GET /api/v1/concerts, exercised against real seeded tour/venue/concert
fixtures (real foreign keys, not hardcoded IDs).
"""

from datetime import datetime, timedelta

from tests.fixtures.dashboard_fixtures import create_concert, create_tour, create_venues


def _seed_priced_concerts(db_session):
    """Seed one tour with six concerts across distinct venues: one with no
    price, and five priced at 20, 50, 75, 100, and 150, so range/boundary
    filters can be asserted against a mix of in-range, out-of-range, and
    unpriced concerts. Returns a dict of concerts keyed by price label.
    """
    tour = create_tour(
        db_session,
        name="Price Filter Integration Tour",
        artist="Test Artist",
        start_date=(datetime.now() - timedelta(days=1)).date(),
        end_date=(datetime.now() + timedelta(days=90)).date(),
        status="active",
    )
    venues = create_venues(db_session, count=6)
    base_time = datetime.now() + timedelta(days=30)

    prices = {
        "no_price": None,
        "20": "20.00",
        "50": "50.00",
        "75": "75.00",
        "100": "100.00",
        "150": "150.00",
    }
    concerts = {
        label: create_concert(db_session, tour, venue, day_offset=i, ticket_price=price, base_time=base_time)
        for i, (venue, (label, price)) in enumerate(zip(venues, prices.items()))
    }
    return concerts


def _ids(response):
    return {concert["id"] for concert in response.json()}


def test_min_price_only_excludes_below_bound_and_unpriced(client, db_session):
    concerts = _seed_priced_concerts(db_session)

    response = client.get("/api/v1/concerts/", params={"min_price": 50})

    assert response.status_code == 200
    assert _ids(response) == {concerts["50"].id, concerts["75"].id, concerts["100"].id, concerts["150"].id}


def test_max_price_only_excludes_above_bound_and_unpriced(client, db_session):
    concerts = _seed_priced_concerts(db_session)

    response = client.get("/api/v1/concerts/", params={"max_price": 100})

    assert response.status_code == 200
    assert _ids(response) == {concerts["20"].id, concerts["50"].id, concerts["75"].id, concerts["100"].id}


def test_min_and_max_price_returns_only_priced_concerts_within_inclusive_range(client, db_session):
    concerts = _seed_priced_concerts(db_session)

    response = client.get("/api/v1/concerts/", params={"min_price": 50, "max_price": 100})

    assert response.status_code == 200
    assert _ids(response) == {concerts["50"].id, concerts["75"].id, concerts["100"].id}


def test_concert_priced_exactly_at_min_price_bound_is_included(client, db_session):
    concerts = _seed_priced_concerts(db_session)

    response = client.get("/api/v1/concerts/", params={"min_price": 50, "max_price": 100})

    assert response.status_code == 200
    assert concerts["50"].id in _ids(response)


def test_concert_priced_exactly_at_max_price_bound_is_included(client, db_session):
    concerts = _seed_priced_concerts(db_session)

    response = client.get("/api/v1/concerts/", params={"min_price": 50, "max_price": 100})

    assert response.status_code == 200
    assert concerts["100"].id in _ids(response)


def test_min_price_greater_than_max_price_returns_422(client, db_session):
    _seed_priced_concerts(db_session)

    response = client.get("/api/v1/concerts/", params={"min_price": 100, "max_price": 50})

    assert response.status_code == 422


def test_no_price_params_includes_unpriced_concerts_matching_prior_behavior(client, db_session):
    concerts = _seed_priced_concerts(db_session)

    response = client.get("/api/v1/concerts/")

    assert response.status_code == 200
    assert _ids(response) == {concert.id for concert in concerts.values()}
