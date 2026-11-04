"""Tests for `GET /api/v1/venues/{venue_id}`."""

from datetime import datetime, timedelta

from tests.fixtures.dashboard_fixtures import create_concert, create_tour, create_venues

NOW = datetime.now()


def _make_tour(db_session):
    return create_tour(
        db_session, "Reunion Tour", "Test Artist",
        (NOW - timedelta(days=60)).date(),
        (NOW + timedelta(days=60)).date(),
        "active",
    )


def test_get_venue_returns_200_and_venue_fields(client, db_session):
    venue = create_venues(db_session, count=1)[0]

    response = client.get(f"/api/v1/venues/{venue.id}")

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == venue.name
    assert data["city"] == venue.city
    assert data["country"] == venue.country
    assert data["capacity"] == venue.capacity
    assert data["upcoming_concerts"] == []


def test_get_venue_lists_upcoming_concerts_soonest_first(client, db_session):
    venue = create_venues(db_session, count=1)[0]
    tour = _make_tour(db_session)
    later_concert = create_concert(
        db_session, tour, venue, day_offset=30, ticket_price="50.00", base_time=NOW,
    )
    soonest_concert = create_concert(
        db_session, tour, venue, day_offset=10, ticket_price="50.00", base_time=NOW,
    )

    response = client.get(f"/api/v1/venues/{venue.id}")

    assert response.status_code == 200
    returned_ids = [concert["id"] for concert in response.json()["upcoming_concerts"]]
    assert returned_ids == [soonest_concert.id, later_concert.id]


def test_get_venue_omits_cancelled_concerts(client, db_session):
    venue = create_venues(db_session, count=1)[0]
    tour = _make_tour(db_session)
    upcoming_concert = create_concert(
        db_session, tour, venue, day_offset=10, ticket_price="50.00", base_time=NOW,
    )
    cancelled_concert = create_concert(
        db_session, tour, venue, day_offset=5, ticket_price="50.00", base_time=NOW,
        is_cancelled=True, cancellation_reason="Artist illness",
    )

    response = client.get(f"/api/v1/venues/{venue.id}")

    assert response.status_code == 200
    returned_ids = [concert["id"] for concert in response.json()["upcoming_concerts"]]
    assert returned_ids == [upcoming_concert.id]
    assert cancelled_concert.id not in returned_ids


def test_get_venue_returns_empty_concert_list_when_none_upcoming(client, db_session):
    venue = create_venues(db_session, count=1)[0]
    tour = _make_tour(db_session)
    create_concert(
        db_session, tour, venue, day_offset=-10, ticket_price="50.00", base_time=NOW,
    )

    response = client.get(f"/api/v1/venues/{venue.id}")

    assert response.status_code == 200
    assert response.json()["upcoming_concerts"] == []


def test_get_unknown_venue_returns_404(client):
    response = client.get("/api/v1/venues/999999")

    assert response.status_code == 404
    assert response.json() == {"detail": "Venue not found"}


def test_get_venue_with_non_integer_id_returns_422(client):
    response = client.get("/api/v1/venues/not-an-id")

    assert response.status_code == 422
