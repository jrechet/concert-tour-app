"""Coverage for the `Artist` model and its link to `Concert` through the
existing `LineupEntry` association table.

Groundwork for story #1011 (the artist detail endpoint counting
non-cancelled concerts): every concert here is created through real
`Venue`/`Tour` foreign keys (via `tests/fixtures/dashboard_fixtures.py`),
never a hardcoded id like `venue_id=1`.
"""

from datetime import datetime
from decimal import Decimal

import pytest

from src.models import Artist, Concert, LineupEntry
from src.models.concert import ConcertStatus
from tests.fixtures.dashboard_fixtures import create_tour, create_venues

REFERENCE_TIME = datetime(2024, 6, 15, 20, 0, 0)


def _make_concert(db_session, **kwargs):
    venue = create_venues(db_session, count=1)[0]
    tour = create_tour(
        db_session,
        name="Groundwork Tour",
        artist="Test Headliner",
        start_date=REFERENCE_TIME.date(),
        end_date=REFERENCE_TIME.date(),
        status="active",
    )
    concert = Concert(
        tour_id=tour.id,
        venue_id=venue.id,
        date_time=REFERENCE_TIME,
        ticket_price=Decimal("50.00"),
        **kwargs,
    )
    db_session.add(concert)
    db_session.commit()
    db_session.refresh(concert)
    return concert


def test_artist_concerts_relationship_exposes_fk_linked_concert(db_session):
    """An artist linked to a concert via a real `LineupEntry.artist_id` FK
    row shows up in `Artist.concerts`, all within one session."""
    concert = _make_concert(db_session)
    artist = Artist(name="Real Artist")
    db_session.add(artist)
    db_session.commit()
    db_session.refresh(artist)

    lineup_entry = LineupEntry(
        concert_id=concert.id,
        artist_id=artist.id,
        artist_name=artist.name,
        set_order=1,
    )
    db_session.add(lineup_entry)
    db_session.commit()

    assert [c.id for c in artist.concerts] == [concert.id]


def test_artist_concerts_relationship_reloads_cleanly_in_a_fresh_query(db_session):
    """The relationship is still loadable after the session's identity map
    is cleared, i.e. it isn't just reflecting in-memory objects."""
    concert = _make_concert(db_session)
    artist = Artist(name="Reloadable Artist")
    db_session.add(artist)
    db_session.commit()
    db_session.refresh(artist)

    db_session.add(
        LineupEntry(
            concert_id=concert.id,
            artist_id=artist.id,
            artist_name=artist.name,
            set_order=1,
        )
    )
    db_session.commit()

    db_session.expire_all()
    reloaded = db_session.query(Artist).filter(Artist.id == artist.id).one()

    assert [c.id for c in reloaded.concerts] == [concert.id]


def test_artist_with_no_lineup_entries_has_no_concerts(db_session):
    artist = Artist(name="Unbooked Artist")
    db_session.add(artist)
    db_session.commit()
    db_session.refresh(artist)

    assert artist.concerts == []


@pytest.mark.parametrize("name", ["", "   ", None])
def test_blank_or_missing_artist_name_is_rejected(name):
    with pytest.raises(ValueError):
        Artist(name=name)


def test_concert_can_be_persisted_with_cancelled_status(db_session):
    concert = _make_concert(db_session, status=ConcertStatus.cancelled)

    db_session.expire_all()
    persisted = db_session.query(Concert).filter(Concert.id == concert.id).one()

    assert persisted.status is ConcertStatus.cancelled


def test_concert_can_be_persisted_with_a_non_cancelled_status(db_session):
    concert = _make_concert(db_session, status=ConcertStatus.scheduled)

    db_session.expire_all()
    persisted = db_session.query(Concert).filter(Concert.id == concert.id).one()

    assert persisted.status is ConcertStatus.scheduled
