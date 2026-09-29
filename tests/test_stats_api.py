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


def test_get_cities_returns_distinct_sorted_cities(client, db_session):
    tour = _seed_tour(db_session)
    venues = create_venues(db_session, count=3)  # New York, London, Paris
    base_time = datetime.now()
    for i, venue in enumerate(venues):
        create_concert(db_session, tour, venue, day_offset=i, ticket_price="50.00", base_time=base_time)
    # A second concert in the same city as an existing venue should not duplicate it.
    create_concert(db_session, tour, venues[0], day_offset=5, ticket_price="50.00", base_time=base_time)

    response = client.get("/api/v1/stats/cities")

    assert response.status_code == 200
    assert response.json() == {"cities": sorted(venue.city for venue in venues)}


def test_get_cities_excludes_cities_with_no_concerts(client, db_session):
    tour = _seed_tour(db_session)
    venue_with_concert = Venue(name="Arena One", city="Berlin", country="Germany", capacity=5000)
    venue_without_concert = Venue(name="Arena Two", city="Rome", country="Italy", capacity=5000)
    db_session.add_all([venue_with_concert, venue_without_concert])
    db_session.commit()
    db_session.refresh(venue_with_concert)
    create_concert(db_session, tour, venue_with_concert, day_offset=1, ticket_price="50.00", base_time=datetime.now())

    response = client.get("/api/v1/stats/cities")

    assert response.status_code == 200
    assert response.json() == {"cities": ["Berlin"]}


def test_get_cities_returns_empty_list_when_no_concerts(client, db_session):
    response = client.get("/api/v1/stats/cities")

    assert response.status_code == 200
    assert response.json() == {"cities": []}


def test_get_venues_returns_distinct_sorted_venue_names(client, db_session):
    tour = _seed_tour(db_session)
    venues = create_venues(db_session, count=3)
    base_time = datetime.now()
    for i, venue in enumerate(venues):
        create_concert(db_session, tour, venue, day_offset=i, ticket_price="50.00", base_time=base_time)
    # A second concert at the same venue should not duplicate it.
    create_concert(db_session, tour, venues[0], day_offset=5, ticket_price="50.00", base_time=base_time)

    response = client.get("/api/v1/stats/venues")

    assert response.status_code == 200
    assert response.json() == {"venues": sorted(venue.name for venue in venues)}


def test_get_venues_excludes_venues_with_no_concerts(client, db_session):
    tour = _seed_tour(db_session)
    venue_with_concert = Venue(name="Arena One", city="Berlin", country="Germany", capacity=5000)
    venue_without_concert = Venue(name="Arena Two", city="Rome", country="Italy", capacity=5000)
    db_session.add_all([venue_with_concert, venue_without_concert])
    db_session.commit()
    db_session.refresh(venue_with_concert)
    create_concert(db_session, tour, venue_with_concert, day_offset=1, ticket_price="50.00", base_time=datetime.now())

    response = client.get("/api/v1/stats/venues")

    assert response.status_code == 200
    assert response.json() == {"venues": ["Arena One"]}


def test_get_venues_returns_empty_list_when_no_concerts(client, db_session):
    response = client.get("/api/v1/stats/venues")

    assert response.status_code == 200
    assert response.json() == {"venues": []}


def test_get_countries_returns_counts_ordered_descending_excluding_cancelled(client, db_session):
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
    # A cancelled concert in a fourth country must not appear in the response.
    venue_spain = Venue(name="Arena Madrid", city="Madrid", country="Spain", capacity=5000)
    db_session.add(venue_spain)
    db_session.commit()
    db_session.refresh(venue_spain)
    create_concert(
        db_session, tour, venue_spain, day_offset=30, ticket_price="50.00", base_time=base_time,
        is_cancelled=True, cancellation_reason="Weather",
    )
    # A cancelled concert in an otherwise-active country must not be counted.
    create_concert(
        db_session, tour, venue_italy, day_offset=21, ticket_price="50.00", base_time=base_time,
        is_cancelled=True, cancellation_reason="Artist illness",
    )

    response = client.get("/api/v1/stats/countries")

    assert response.status_code == 200
    assert response.json() == [
        {"country": "Germany", "concert_count": 3},
        {"country": "France", "concert_count": 2},
        {"country": "Italy", "concert_count": 1},
    ]


def test_get_countries_returns_empty_list_when_no_concerts(client, db_session):
    response = client.get("/api/v1/stats/countries")

    assert response.status_code == 200
    assert response.json() == []


def test_get_prices_returns_lowest_average_highest_for_eligible_concerts(client, db_session):
    tour = _seed_tour(db_session)
    venues = create_venues(db_session, count=3)
    base_time = datetime.now()
    create_concert(db_session, tour, venues[0], day_offset=1, ticket_price="50.00", base_time=base_time)
    create_concert(db_session, tour, venues[1], day_offset=2, ticket_price="100.00", base_time=base_time)
    create_concert(db_session, tour, venues[2], day_offset=3, ticket_price="150.00", base_time=base_time)
    # A past concert must not affect the stats.
    create_concert(db_session, tour, venues[0], day_offset=-10, ticket_price="1.00", base_time=base_time)
    # A cancelled concert must not affect the stats.
    create_concert(
        db_session, tour, venues[1], day_offset=4, ticket_price="9999.00", base_time=base_time,
        is_cancelled=True, cancellation_reason="Weather",
    )
    # A concert with no ticket price must not affect the stats.
    create_concert(db_session, tour, venues[2], day_offset=5, ticket_price=None, base_time=base_time)

    response = client.get("/api/v1/stats/prices")

    assert response.status_code == 200
    assert response.json() == {"lowest": 50.0, "average": 100.0, "highest": 150.0}


def test_get_prices_returns_nulls_when_no_eligible_concerts(client, db_session):
    response = client.get("/api/v1/stats/prices")

    assert response.status_code == 200
    assert response.json() == {"lowest": None, "average": None, "highest": None}


def test_stats_endpoints_documented_in_openapi_schema(client):
    schema = client.get("/openapi.json").json()

    cities_get = schema["paths"]["/api/v1/stats/cities"]["get"]
    venues_get = schema["paths"]["/api/v1/stats/venues"]["get"]

    assert cities_get["responses"]["200"]["content"]["application/json"]["schema"]["$ref"] == (
        "#/components/schemas/CitiesResponse"
    )
    assert venues_get["responses"]["200"]["content"]["application/json"]["schema"]["$ref"] == (
        "#/components/schemas/VenuesResponse"
    )

    countries_get = schema["paths"]["/api/v1/stats/countries"]["get"]
    countries_schema = countries_get["responses"]["200"]["content"]["application/json"]["schema"]
    assert countries_schema["items"]["$ref"] == "#/components/schemas/CountryConcertCount"

    prices_get = schema["paths"]["/api/v1/stats/prices"]["get"]
    assert prices_get["responses"]["200"]["content"]["application/json"]["schema"]["$ref"] == (
        "#/components/schemas/PriceStatsResponse"
    )
