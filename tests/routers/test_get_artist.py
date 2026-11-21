"""Tests for `GET /api/v1/artists/{artist_id}`."""

from datetime import datetime

from src.main import app
from src.models import Artist, LineupEntry
from src.models.concert import ConcertStatus
from tests.fixtures.dashboard_fixtures import create_concert, create_tour, create_venues

BASE_TIME = datetime(2024, 6, 15, 20, 0, 0)


def _make_artist(db_session, name):
    artist = Artist(name=name)
    db_session.add(artist)
    db_session.commit()
    db_session.refresh(artist)
    return artist


def _book(db_session, artist, concert, set_order=1):
    db_session.add(
        LineupEntry(
            concert_id=concert.id,
            artist_id=artist.id,
            artist_name=artist.name,
            set_order=set_order,
        )
    )
    db_session.commit()


def test_200_returns_artist_with_non_cancelled_concert_count(client, db_session):
    venue = create_venues(db_session, count=1)[0]
    tour = create_tour(
        db_session, "Groundwork Tour", "Test Headliner", BASE_TIME.date(), BASE_TIME.date(), "active",
    )
    artist = _make_artist(db_session, "Real Artist")
    active_concert = create_concert(
        db_session, tour, venue, day_offset=0, ticket_price="50.00", base_time=BASE_TIME,
    )
    cancelled_concert = create_concert(
        db_session, tour, venue, day_offset=1, ticket_price="50.00", base_time=BASE_TIME,
    )
    cancelled_concert.status = ConcertStatus.cancelled
    db_session.commit()
    _book(db_session, artist, active_concert, set_order=1)
    _book(db_session, artist, cancelled_concert, set_order=2)

    response = client.get(f"/api/v1/artists/{artist.id}")

    assert response.status_code == 200
    assert response.json() == {"id": artist.id, "name": "Real Artist", "concert_count": 1}


def test_200_zero_concert_count_for_artist_with_no_concerts(client, db_session):
    artist = _make_artist(db_session, "Unbooked Artist")

    response = client.get(f"/api/v1/artists/{artist.id}")

    assert response.status_code == 200
    assert response.json() == {"id": artist.id, "name": "Unbooked Artist", "concert_count": 0}


def test_404_for_unknown_artist_id(client):
    response = client.get("/api/v1/artists/999999")

    assert response.status_code == 404
    assert response.json() == {"detail": "Artist not found"}


def test_422_for_non_integer_artist_id(client):
    response = client.get("/api/v1/artists/abc")

    assert response.status_code == 422


def test_route_is_registered_on_the_app():
    paths = app.openapi()["paths"]

    assert "/api/v1/artists/{artist_id}" in paths
    assert "get" in paths["/api/v1/artists/{artist_id}"]
