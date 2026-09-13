"""Tests for the LineupEntry model: ordering, optional set_time, and
cascade deletion when the parent concert is removed."""

from datetime import datetime, timedelta

from src.models import LineupEntry
from tests.fixtures.dashboard_fixtures import create_concert, create_tour, create_venues


def _build_concert(db_session):
    base_time = datetime(2026, 11, 1, 20, 0, 0)
    venue = create_venues(db_session, count=1)[0]
    tour = create_tour(
        db_session,
        name="Test Tour",
        artist="Test Artist",
        start_date=base_time.date(),
        end_date=(base_time + timedelta(days=10)).date(),
        status="planned",
    )
    return create_concert(
        db_session, tour, venue, day_offset=0, ticket_price="50.00", base_time=base_time
    )


def test_lineup_is_empty_by_default(db_session):
    concert = _build_concert(db_session)

    assert concert.lineup == []


def test_lineup_entries_are_ordered_by_running_order_not_insertion_order(db_session):
    concert = _build_concert(db_session)
    db_session.add_all([
        LineupEntry(concert_id=concert.id, artist_name="Plays Third", running_order=3),
        LineupEntry(concert_id=concert.id, artist_name="Plays First", running_order=1),
        LineupEntry(concert_id=concert.id, artist_name="Plays Second", running_order=2),
    ])
    db_session.commit()
    db_session.refresh(concert)

    assert [entry.artist_name for entry in concert.lineup] == [
        "Plays First", "Plays Second", "Plays Third",
    ]


def test_lineup_entry_set_time_is_optional(db_session):
    concert = _build_concert(db_session)
    entry = LineupEntry(concert_id=concert.id, artist_name="No Set Time Yet", running_order=1)
    db_session.add(entry)
    db_session.commit()
    db_session.refresh(entry)

    assert entry.set_time is None


def test_deleting_concert_cascades_to_lineup_entries(db_session):
    concert = _build_concert(db_session)
    db_session.add(LineupEntry(concert_id=concert.id, artist_name="Opener", running_order=1))
    db_session.commit()
    concert_id = concert.id

    db_session.delete(concert)
    db_session.commit()

    remaining = db_session.query(LineupEntry).filter(LineupEntry.concert_id == concert_id).count()
    assert remaining == 0
