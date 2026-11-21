"""Unit tests for `get_artist_detail`."""

from datetime import datetime

from src.models import Artist, LineupEntry
from src.models.concert import ConcertStatus
from src.schemas.artist import ArtistDetail
from src.services.artist_service import get_artist_detail
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


class TestGetArtistDetail:
    """Coverage for `get_artist_detail`."""

    def test_counts_only_non_cancelled_concerts(self, db_session):
        venue = create_venues(db_session, count=1)[0]
        tour = create_tour(
            db_session, "Groundwork Tour", "Test Headliner", BASE_TIME.date(), BASE_TIME.date(), "active",
        )
        artist = _make_artist(db_session, "Real Artist")
        for i in range(3):
            concert = create_concert(db_session, tour, venue, day_offset=i, ticket_price="50.00", base_time=BASE_TIME)
            if i == 0:
                concert.status = ConcertStatus.cancelled
                db_session.commit()
            _book(db_session, artist, concert, set_order=i + 1)

        detail = get_artist_detail(db_session, artist.id)

        assert detail == ArtistDetail(id=artist.id, name="Real Artist", concert_count=2)

    def test_artist_with_zero_concerts_has_zero_count(self, db_session):
        artist = _make_artist(db_session, "Unbooked Artist")

        detail = get_artist_detail(db_session, artist.id)

        assert detail == ArtistDetail(id=artist.id, name="Unbooked Artist", concert_count=0)

    def test_artist_whose_every_concert_is_cancelled_has_zero_count(self, db_session):
        venue = create_venues(db_session, count=1)[0]
        tour = create_tour(
            db_session, "Groundwork Tour", "Test Headliner", BASE_TIME.date(), BASE_TIME.date(), "active",
        )
        artist = _make_artist(db_session, "Unlucky Artist")
        for i in range(2):
            concert = create_concert(db_session, tour, venue, day_offset=i, ticket_price="50.00", base_time=BASE_TIME)
            concert.status = ConcertStatus.cancelled
            db_session.commit()
            _book(db_session, artist, concert, set_order=i + 1)

        detail = get_artist_detail(db_session, artist.id)

        assert detail == ArtistDetail(id=artist.id, name="Unlucky Artist", concert_count=0)

    def test_unknown_artist_id_returns_none(self, db_session):
        assert get_artist_detail(db_session, 999) is None

    def test_another_artists_cancelled_concerts_do_not_affect_count(self, db_session):
        venue = create_venues(db_session, count=1)[0]
        tour = create_tour(
            db_session, "Groundwork Tour", "Test Headliner", BASE_TIME.date(), BASE_TIME.date(), "active",
        )
        artist = _make_artist(db_session, "Main Artist")
        other_artist = _make_artist(db_session, "Other Artist")

        own_concert = create_concert(db_session, tour, venue, day_offset=0, ticket_price="50.00", base_time=BASE_TIME)
        _book(db_session, artist, own_concert, set_order=1)

        other_concert = create_concert(db_session, tour, venue, day_offset=1, ticket_price="50.00", base_time=BASE_TIME)
        other_concert.status = ConcertStatus.cancelled
        db_session.commit()
        _book(db_session, other_artist, other_concert, set_order=1)

        detail = get_artist_detail(db_session, artist.id)

        assert detail == ArtistDetail(id=artist.id, name="Main Artist", concert_count=1)
