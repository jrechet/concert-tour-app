"""Tests for the concert lineup model (`LineupEntry`): deterministic set
order, 1-based `set_order` validation, per-concert uniqueness, and cascade
deletion when the parent concert is removed.

`LineupEntry` is the project's existing concert/act association (there is
no separate `concert_act.py`): it carries a real FK to `concerts.id` and a
1-based `set_order` position, and `Concert.lineup` is ordered by it.
"""

from datetime import datetime, timedelta

import pytest

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


def test_lineup_sorted_by_ascending_set_order_regardless_of_insertion_order(db_session):
    concert = _build_concert(db_session)
    db_session.add_all([
        LineupEntry(concert_id=concert.id, artist_name="Plays Third", set_order=3),
        LineupEntry(concert_id=concert.id, artist_name="Plays First", set_order=1),
        LineupEntry(concert_id=concert.id, artist_name="Plays Second", set_order=2),
    ])
    db_session.commit()
    db_session.refresh(concert)

    assert [entry.artist_name for entry in concert.lineup] == [
        "Plays First", "Plays Second", "Plays Third",
    ]


def test_set_order_zero_is_rejected(db_session):
    concert = _build_concert(db_session)

    with pytest.raises(ValueError):
        LineupEntry(concert_id=concert.id, artist_name="Bad Order", set_order=0)


def test_negative_set_order_is_rejected(db_session):
    concert = _build_concert(db_session)

    with pytest.raises(ValueError):
        LineupEntry(concert_id=concert.id, artist_name="Bad Order", set_order=-1)


def test_duplicate_set_order_within_same_concert_is_rejected(db_session):
    concert = _build_concert(db_session)
    db_session.add(LineupEntry(concert_id=concert.id, artist_name="First Opener", set_order=1))
    db_session.commit()

    db_session.add(LineupEntry(concert_id=concert.id, artist_name="Second Opener", set_order=1))
    with pytest.raises(ValueError):
        db_session.commit()
    db_session.rollback()


def test_same_set_order_is_allowed_across_different_concerts(db_session):
    concert_a = _build_concert(db_session)
    concert_b = _build_concert(db_session)
    db_session.add_all([
        LineupEntry(concert_id=concert_a.id, artist_name="Opener A", set_order=1),
        LineupEntry(concert_id=concert_b.id, artist_name="Opener B", set_order=1),
    ])
    db_session.commit()

    assert [entry.artist_name for entry in concert_a.lineup] == ["Opener A"]
    assert [entry.artist_name for entry in concert_b.lineup] == ["Opener B"]


def test_deleting_concert_cascades_to_lineup_entries(db_session):
    concert = _build_concert(db_session)
    db_session.add(LineupEntry(concert_id=concert.id, artist_name="Opener", set_order=1))
    db_session.commit()
    concert_id = concert.id

    db_session.delete(concert)
    db_session.commit()

    remaining = db_session.query(LineupEntry).filter(LineupEntry.concert_id == concert_id).count()
    assert remaining == 0
