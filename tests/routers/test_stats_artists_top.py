"""Tests for `GET /api/v1/stats/artists/top`."""

from datetime import datetime

from src.models import LineupEntry
from src.services.concert_service import cancel_concert
from tests.fixtures.dashboard_fixtures import create_concert, create_tour, create_venues

BASE_TIME = datetime(2024, 6, 17, 20, 0, 0)


def _make_concert_for_artist(db_session, venue, day_offset, tour_name, artist):
    """Persist a scheduled concert linked to a real tour and venue via FK."""
    tour = create_tour(db_session, tour_name, artist, BASE_TIME.date(), BASE_TIME.date(), "active")
    return create_concert(db_session, tour, venue, day_offset=day_offset, ticket_price="80.00", base_time=BASE_TIME)


def _add_appearance(db_session, concert, artist_name, set_order=1):
    """Record `artist_name` as a lineup appearance on `concert`."""
    entry = LineupEntry(concert_id=concert.id, artist_name=artist_name, set_order=set_order)
    db_session.add(entry)
    db_session.commit()
    db_session.refresh(entry)
    return entry


class TestTopArtistsStatsEndpoint:
    """Coverage for `GET /api/v1/stats/artists/top`."""

    def test_returns_200_and_empty_list_when_no_artists(self, client):
        response = client.get("/api/v1/stats/artists/top")

        assert response.status_code == 200
        assert response.json() == []

    def test_returns_200_with_top_five_ordered_by_count(self, client, db_session):
        venue = create_venues(db_session, count=1)[0]
        artists = ["Artist F", "Artist E", "Artist D", "Artist C", "Artist B", "Artist A"]

        for i, artist in enumerate(artists):
            appearance_count = len(artists) - i
            for appearance_index in range(appearance_count):
                concert = _make_concert_for_artist(
                    db_session, venue,
                    day_offset=i * 10 + appearance_index,
                    tour_name=f"{artist} Tour {appearance_index}",
                    artist=artist,
                )
                _add_appearance(db_session, concert, artist)

        response = client.get("/api/v1/stats/artists/top")

        assert response.status_code == 200
        assert response.json() == [
            {"name": "Artist F", "appearances": 6},
            {"name": "Artist E", "appearances": 5},
            {"name": "Artist D", "appearances": 4},
            {"name": "Artist C", "appearances": 3},
            {"name": "Artist B", "appearances": 2},
        ]

    def test_returns_200_with_ties_ordered_by_name(self, client, db_session):
        venue = create_venues(db_session, count=1)[0]

        concert_z = _make_concert_for_artist(db_session, venue, 0, "Tour Z", "Zebra Collective")
        _add_appearance(db_session, concert_z, "Zebra Collective")

        concert_a = _make_concert_for_artist(db_session, venue, 1, "Tour A", "Antler Brothers")
        _add_appearance(db_session, concert_a, "Antler Brothers")

        response = client.get("/api/v1/stats/artists/top")

        assert response.status_code == 200
        assert response.json() == [
            {"name": "Antler Brothers", "appearances": 1},
            {"name": "Zebra Collective", "appearances": 1},
        ]

    def test_returns_200_excluding_cancelled_concerts(self, client, db_session):
        venue = create_venues(db_session, count=1)[0]

        scheduled_concert = _make_concert_for_artist(db_session, venue, 0, "Tour 1", "Aurora Belle")
        _add_appearance(db_session, scheduled_concert, "Aurora Belle")

        cancelled_concert = _make_concert_for_artist(db_session, venue, 1, "Tour 2", "Aurora Belle")
        _add_appearance(db_session, cancelled_concert, "Aurora Belle")
        cancel_concert(db_session, cancelled_concert.id)

        response = client.get("/api/v1/stats/artists/top")

        assert response.status_code == 200
        assert response.json() == [{"name": "Aurora Belle", "appearances": 1}]

    def test_response_items_expose_name_and_appearances_keys(self, client, db_session):
        venue = create_venues(db_session, count=1)[0]
        concert = _make_concert_for_artist(db_session, venue, 0, "Tour 1", "Aurora Belle")
        _add_appearance(db_session, concert, "Aurora Belle")

        response = client.get("/api/v1/stats/artists/top")

        assert response.status_code == 200
        body = response.json()
        assert len(body) == 1
        assert set(body[0].keys()) == {"name", "appearances"}

    def test_unknown_stats_path_returns_404(self, client):
        response = client.get("/api/v1/stats/artists/nope")

        assert response.status_code == 404
