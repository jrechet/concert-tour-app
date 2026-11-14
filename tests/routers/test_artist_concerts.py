"""Tests for `GET /api/v1/artists/{artist_id}/concerts`."""

from datetime import datetime, timedelta

from src.models import LineupEntry
from tests.fixtures.dashboard_fixtures import create_concert, create_tour, create_venues

NOW = datetime.now()

ARTIST = "Aurora Belle"


def _make_tour(db_session, artist=ARTIST):
    return create_tour(
        db_session, "Reunion Tour", artist,
        (NOW - timedelta(days=60)).date(),
        (NOW + timedelta(days=60)).date(),
        "active",
    )


def _add_to_lineup(db_session, concert, artist_name=ARTIST, set_order=1):
    db_session.add(LineupEntry(concert_id=concert.id, artist_name=artist_name, set_order=set_order))
    db_session.commit()


def test_200_lists_concerts_soonest_first(client, db_session):
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
    for concert in (later_concert, soonest_concert, middle_concert):
        _add_to_lineup(db_session, concert)

    response = client.get(f"/api/v1/artists/{ARTIST}/concerts")

    assert response.status_code == 200
    returned_ids = [concert["id"] for concert in response.json()]
    assert returned_ids == [soonest_concert.id, middle_concert.id, later_concert.id]


def test_200_item_contains_date_venue_and_city(client, db_session):
    venue = create_venues(db_session, count=1)[0]
    tour = _make_tour(db_session)
    concert = create_concert(
        db_session, tour, venue, day_offset=5, ticket_price="50.00", base_time=NOW,
    )
    _add_to_lineup(db_session, concert)

    response = client.get(f"/api/v1/artists/{ARTIST}/concerts")

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    item = body[0]
    assert item["id"] == concert.id
    assert datetime.fromisoformat(item["date"]) == concert.date_time
    assert item["venue"]["name"] == venue.name
    assert item["venue"]["city"] == venue.city


def test_200_excludes_cancelled_concerts(client, db_session):
    venue = create_venues(db_session, count=1)[0]
    tour = _make_tour(db_session)
    active_concert = create_concert(
        db_session, tour, venue, day_offset=10, ticket_price="50.00", base_time=NOW,
    )
    cancelled_concert = create_concert(
        db_session, tour, venue, day_offset=5, ticket_price="50.00", base_time=NOW,
        is_cancelled=True, cancellation_reason="Artist illness",
    )
    _add_to_lineup(db_session, active_concert)
    _add_to_lineup(db_session, cancelled_concert)

    response = client.get(f"/api/v1/artists/{ARTIST}/concerts")

    assert response.status_code == 200
    returned_ids = [concert["id"] for concert in response.json()]
    assert returned_ids == [active_concert.id]
    assert cancelled_concert.id not in returned_ids


def test_200_empty_list_when_artist_has_no_concerts(client, db_session):
    _make_tour(db_session, artist="Lonely Headliner")

    response = client.get("/api/v1/artists/Lonely Headliner/concerts")

    assert response.status_code == 200
    assert response.json() == []


def test_404_for_unknown_artist(client):
    response = client.get("/api/v1/artists/Unknown Artist/concerts")

    assert response.status_code == 404
    assert response.json() == {"detail": "Artist not found"}
