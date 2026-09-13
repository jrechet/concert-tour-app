"""Tests for the concert list/detail JSON API endpoints."""

from datetime import datetime, timedelta
from decimal import Decimal

from tests.fixtures.dashboard_fixtures import create_concert, create_tour, create_venues


def _seed_tour_and_venue(db_session):
    tour = create_tour(
        db_session,
        name="Test Tour",
        artist="Test Artist",
        start_date=(datetime.now() - timedelta(days=1)).date(),
        end_date=(datetime.now() + timedelta(days=90)).date(),
        status="active",
    )
    venue = create_venues(db_session, count=1)[0]
    return tour, venue


def _seed_multi_city_tour(db_session, venue_count=3, name="Multi-City E2E Tour"):
    """A single tour with `venue_count` distinct-city venues, real FKs throughout."""
    tour = create_tour(
        db_session,
        name=name,
        artist="Test Artist",
        start_date=(datetime.now() - timedelta(days=1)).date(),
        end_date=(datetime.now() + timedelta(days=90)).date(),
        status="active",
    )
    venues = create_venues(db_session, count=venue_count)
    return tour, venues


def test_get_concerts_includes_remaining_tickets_and_sold_out(client, db_session):
    """Every concert in the list response carries the derived fields."""
    tour, venue = _seed_tour_and_venue(db_session)
    create_concert(
        db_session, tour, venue, day_offset=10, ticket_price="50.00",
        base_time=datetime.now(), tickets_sold=100,
    )

    response = client.get("/api/v1/concerts/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["remaining_tickets"] == venue.capacity - 100
    assert data[0]["sold_out"] is False
    assert data[0]["tickets_sold"] == 100


def test_get_concerts_sold_out_when_zero_remaining(client, db_session):
    """A concert with tickets_sold == venue capacity reports sold_out."""
    tour, venue = _seed_tour_and_venue(db_session)
    create_concert(
        db_session, tour, venue, day_offset=10, ticket_price="50.00",
        base_time=datetime.now(), tickets_sold=venue.capacity,
    )

    response = client.get("/api/v1/concerts/")
    data = response.json()[0]
    assert data["remaining_tickets"] == 0
    assert data["sold_out"] is True


def test_get_concerts_pagination(client, db_session):
    """skip/limit continue to page results with the added fields present."""
    tour, venue = _seed_tour_and_venue(db_session)
    base_time = datetime.now()
    for i in range(5):
        create_concert(
            db_session, tour, venue, day_offset=i, ticket_price="50.00",
            base_time=base_time, tickets_sold=i,
        )

    response = client.get("/api/v1/concerts/?skip=2&limit=2")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    for concert in data:
        assert "remaining_tickets" in concert
        assert "sold_out" in concert


def test_get_concerts_empty(client):
    """An empty database returns an empty list, not an error."""
    response = client.get("/api/v1/concerts/")
    assert response.status_code == 200
    assert response.json() == []


def test_get_concert_by_id(client, db_session):
    """Fetching a single concert includes the derived fields too."""
    tour, venue = _seed_tour_and_venue(db_session)
    concert = create_concert(
        db_session, tour, venue, day_offset=10, ticket_price="50.00",
        base_time=datetime.now(), tickets_sold=venue.capacity,
    )

    response = client.get(f"/api/v1/concerts/{concert.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == concert.id
    assert data["sold_out"] is True
    assert data["remaining_tickets"] == 0


def test_get_concert_not_found(client):
    """Requesting a nonexistent concert returns 404."""
    response = client.get("/api/v1/concerts/999")
    assert response.status_code == 404


def test_get_concerts_filtered_by_city(client, db_session):
    """?city=<City> narrows results to concerts whose venue is in that city."""
    tour = create_tour(
        db_session,
        name="Multi-City Tour",
        artist="Test Artist",
        start_date=(datetime.now() - timedelta(days=1)).date(),
        end_date=(datetime.now() + timedelta(days=90)).date(),
        status="active",
    )
    venues = create_venues(db_session, count=2)  # New York, London
    base_time = datetime.now()
    create_concert(
        db_session, tour, venues[0], day_offset=1, ticket_price="50.00",
        base_time=base_time, tickets_sold=0,
    )
    create_concert(
        db_session, tour, venues[1], day_offset=2, ticket_price="60.00",
        base_time=base_time, tickets_sold=0,
    )

    response = client.get("/api/v1/concerts/?city=New York")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["venue_id"] == venues[0].id


def test_get_concerts_filtered_by_city_case_insensitive(client, db_session):
    """City filtering matches regardless of case."""
    tour, venue = _seed_tour_and_venue(db_session)
    create_concert(
        db_session, tour, venue, day_offset=1, ticket_price="50.00",
        base_time=datetime.now(), tickets_sold=0,
    )

    response = client.get(f"/api/v1/concerts/?city={venue.city.upper()}")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1


def test_get_concerts_unknown_city_returns_empty_list(client, db_session):
    """An unknown/nonexistent city returns an empty list, not an error."""
    tour, venue = _seed_tour_and_venue(db_session)
    create_concert(
        db_session, tour, venue, day_offset=1, ticket_price="50.00",
        base_time=datetime.now(), tickets_sold=0,
    )

    response = client.get("/api/v1/concerts/?city=Nonexistentville")
    assert response.status_code == 200
    assert response.json() == []


def test_get_concerts_city_filter_combines_with_pagination(client, db_session):
    """city filter and skip/limit combine correctly."""
    tour = create_tour(
        db_session,
        name="Repeat City Tour",
        artist="Test Artist",
        start_date=(datetime.now() - timedelta(days=1)).date(),
        end_date=(datetime.now() + timedelta(days=90)).date(),
        status="active",
    )
    venues = create_venues(db_session, count=1)
    venue = venues[0]
    base_time = datetime.now()
    for i in range(5):
        create_concert(
            db_session, tour, venue, day_offset=i, ticket_price="50.00",
            base_time=base_time, tickets_sold=i,
        )

    response = client.get(f"/api/v1/concerts/?city={venue.city}&skip=2&limit=2")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    for concert in data:
        assert concert["venue_id"] == venue.id


class TestCityFilterEndToEnd:
    """End-to-end coverage for the city filter: multi-city pagination
    interaction and the full apply/clear user flow, on top of the isolated
    single-scenario tests above."""

    def test_filter_by_valid_city_narrows_results(self, client, db_session):
        """Filtering by one of several distinct cities returns only that
        city's concerts."""
        tour, venues = _seed_multi_city_tour(db_session, venue_count=3)
        base_time = datetime.now()
        for i, venue in enumerate(venues):
            create_concert(
                db_session, tour, venue, day_offset=i, ticket_price="50.00",
                base_time=base_time, tickets_sold=0,
            )

        target = venues[1]
        response = client.get(f"/api/v1/concerts/?city={target.city}")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["venue_id"] == target.id

    def test_filter_by_city_with_no_matches_returns_empty(self, client, db_session):
        tour, venues = _seed_multi_city_tour(db_session, venue_count=2)
        base_time = datetime.now()
        for i, venue in enumerate(venues):
            create_concert(
                db_session, tour, venue, day_offset=i, ticket_price="50.00",
                base_time=base_time, tickets_sold=0,
            )

        response = client.get("/api/v1/concerts/?city=Atlantis")
        assert response.status_code == 200
        assert response.json() == []

    def test_no_filter_returns_concerts_across_all_cities(self, client, db_session):
        """With no `city` param, concerts from every city are returned."""
        tour, venues = _seed_multi_city_tour(db_session, venue_count=3)
        base_time = datetime.now()
        for i, venue in enumerate(venues):
            create_concert(
                db_session, tour, venue, day_offset=i, ticket_price="50.00",
                base_time=base_time, tickets_sold=0,
            )

        response = client.get("/api/v1/concerts/")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == len(venues)
        assert {c["venue_id"] for c in data} == {v.id for v in venues}

    def test_filter_then_clear_returns_to_unfiltered_state(self, client, db_session):
        """Full user flow: load the unfiltered list (as a UI would to
        populate a city picker), apply a city filter, then clear it and
        confirm the list matches what was originally loaded."""
        tour, venues = _seed_multi_city_tour(db_session, venue_count=3)
        base_time = datetime.now()
        for i, venue in enumerate(venues):
            create_concert(
                db_session, tour, venue, day_offset=i, ticket_price="50.00",
                base_time=base_time, tickets_sold=0,
            )

        baseline_response = client.get("/api/v1/concerts/")
        assert baseline_response.status_code == 200
        baseline = baseline_response.json()
        assert len(baseline) == 3

        filtered_response = client.get(f"/api/v1/concerts/?city={venues[0].city}")
        assert filtered_response.status_code == 200
        filtered = filtered_response.json()
        assert len(filtered) == 1
        assert filtered[0]["venue_id"] == venues[0].id

        cleared_response = client.get("/api/v1/concerts/")
        assert cleared_response.status_code == 200
        assert cleared_response.json() == baseline

    def test_filter_combined_with_pagination_uses_filtered_subset(self, client, db_session):
        """skip/limit must apply to the filtered result set, not the
        unfiltered total, confirming the filter is applied before
        pagination."""
        tour, venues = _seed_multi_city_tour(db_session, venue_count=2)
        target, other = venues
        base_time = datetime.now()
        for i in range(3):
            create_concert(
                db_session, tour, target, day_offset=i, ticket_price="50.00",
                base_time=base_time, tickets_sold=0,
            )
        for i in range(5):
            create_concert(
                db_session, tour, other, day_offset=10 + i, ticket_price="60.00",
                base_time=base_time, tickets_sold=0,
            )

        # 8 concerts total, but only 3 belong to `target`. skip=2, limit=5
        # against the filtered subset should yield exactly 1 result.
        response = client.get(f"/api/v1/concerts/?city={target.city}&skip=2&limit=5")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["venue_id"] == target.id

    def test_filter_combined_with_pagination_skip_beyond_filtered_count_is_empty(self, client, db_session):
        """skip past the end of the filtered subset returns an empty list,
        even though unfiltered data exists further along."""
        tour, venues = _seed_multi_city_tour(db_session, venue_count=2)
        target, other = venues
        base_time = datetime.now()
        for i in range(3):
            create_concert(
                db_session, tour, target, day_offset=i, ticket_price="50.00",
                base_time=base_time, tickets_sold=0,
            )
        for i in range(5):
            create_concert(
                db_session, tour, other, day_offset=10 + i, ticket_price="60.00",
                base_time=base_time, tickets_sold=0,
            )

        response = client.get(f"/api/v1/concerts/?city={target.city}&skip=3&limit=5")
        assert response.status_code == 200
        assert response.json() == []
