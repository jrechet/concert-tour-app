"""Tests for `GET /api/v1/venues/{venue_id}/concerts`."""

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


def test_returns_200_with_concerts_ordered_soonest_first(client, db_session):
    venue = create_venues(db_session, count=1)[0]
    tour = _make_tour(db_session)
    later_concert = create_concert(
        db_session, tour, venue, day_offset=30, ticket_price="50.00", base_time=NOW,
    )
    soonest_concert = create_concert(
        db_session, tour, venue, day_offset=5, ticket_price="50.00", base_time=NOW,
    )
    middle_concert = create_concert(
        db_session, tour, venue, day_offset=10, ticket_price="50.00", base_time=NOW,
    )

    response = client.get(f"/api/v1/venues/{venue.id}/concerts")

    assert response.status_code == 200
    returned_ids = [concert["id"] for concert in response.json()]
    assert returned_ids == [soonest_concert.id, middle_concert.id, later_concert.id]


def test_excludes_cancelled_concerts(client, db_session):
    venue = create_venues(db_session, count=1)[0]
    tour = _make_tour(db_session)
    active_concert = create_concert(
        db_session, tour, venue, day_offset=10, ticket_price="50.00", base_time=NOW,
    )
    cancelled_concert = create_concert(
        db_session, tour, venue, day_offset=5, ticket_price="50.00", base_time=NOW,
        is_cancelled=True, cancellation_reason="Artist illness",
    )

    response = client.get(f"/api/v1/venues/{venue.id}/concerts")

    assert response.status_code == 200
    returned_ids = [concert["id"] for concert in response.json()]
    assert returned_ids == [active_concert.id]
    assert cancelled_concert.id not in returned_ids


def test_returns_200_with_empty_list_when_venue_has_no_concerts(client, db_session):
    venue = create_venues(db_session, count=1)[0]

    response = client.get(f"/api/v1/venues/{venue.id}/concerts")

    assert response.status_code == 200
    assert response.json() == []


def test_returns_404_for_unknown_venue(client):
    response = client.get("/api/v1/venues/999999/concerts")

    assert response.status_code == 404
    assert response.json() == {"detail": "Venue not found"}


def test_returns_422_for_non_integer_venue_id(client):
    response = client.get("/api/v1/venues/not-an-id/concerts")

    assert response.status_code == 422
