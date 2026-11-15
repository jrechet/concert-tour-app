"""Tests for `DELETE /api/v1/venues/{venue_id}`."""

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


def test_returns_204_with_empty_body_and_removes_venue_with_no_concerts(client, db_session):
    venue = create_venues(db_session, count=1)[0]
    venue_id = venue.id

    response = client.delete(f"/api/v1/venues/{venue_id}")

    assert response.status_code == 204
    assert response.content == b""

    follow_up = client.get(f"/api/v1/venues/{venue_id}")
    assert follow_up.status_code == 404


def test_returns_409_with_concert_count_one_and_keeps_venue(client, db_session):
    venue = create_venues(db_session, count=1)[0]
    tour = _make_tour(db_session)
    create_concert(
        db_session, tour, venue, day_offset=5, ticket_price="50.00", base_time=NOW,
    )

    response = client.delete(f"/api/v1/venues/{venue.id}")

    assert response.status_code == 409
    assert response.json()["concert_count"] == 1

    follow_up = client.get(f"/api/v1/venues/{venue.id}")
    assert follow_up.status_code == 200


def test_returns_409_with_concert_count_three_and_keeps_venue(client, db_session):
    venue = create_venues(db_session, count=1)[0]
    tour = _make_tour(db_session)
    for day_offset in (5, 10, 15):
        create_concert(
            db_session, tour, venue, day_offset=day_offset, ticket_price="50.00",
            base_time=NOW,
        )

    response = client.delete(f"/api/v1/venues/{venue.id}")

    assert response.status_code == 409
    assert response.json()["concert_count"] == 3

    follow_up = client.get(f"/api/v1/venues/{venue.id}")
    assert follow_up.status_code == 200


def test_returns_404_for_unknown_venue_id(client, db_session):
    venue = create_venues(db_session, count=1)[0]
    unknown_venue_id = venue.id + 1

    response = client.delete(f"/api/v1/venues/{unknown_venue_id}")

    assert response.status_code == 404
