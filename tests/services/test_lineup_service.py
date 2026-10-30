"""Unit tests for `move_lineup_entry`, independent of the HTTP layer."""

from datetime import datetime

import pytest

from src.models import LineupEntry
from src.services.concerts_service import ConcertNotFoundError
from src.services.lineup_service import LineupEntryNotFoundError, move_lineup_entry
from tests.fixtures.dashboard_fixtures import create_concert, create_tour, create_venues

REFERENCE_TIME = datetime(2024, 6, 15, 18, 0, 0)


def _make_concert(db_session):
    venues = create_venues(db_session, count=1)
    tour = create_tour(
        db_session, "Test Tour", "Test Artist",
        REFERENCE_TIME.date(), REFERENCE_TIME.date(), "active",
    )
    return create_concert(db_session, tour, venues[0], day_offset=1, ticket_price="80.00", base_time=REFERENCE_TIME)


def _make_entry(db_session, concert, artist_name="Opening Act", set_order=1):
    entry = LineupEntry(concert_id=concert.id, artist_name=artist_name, set_order=set_order)
    db_session.add(entry)
    db_session.commit()
    db_session.refresh(entry)
    return entry


def _make_lineup(db_session, concert, count):
    """Persist `count` entries with contiguous `set_order` 1..count."""
    return [
        _make_entry(db_session, concert, artist_name=f"Act {i}", set_order=i)
        for i in range(1, count + 1)
    ]


def _all_set_orders(db_session, concert_id):
    rows = (
        db_session.query(LineupEntry)
        .filter(LineupEntry.concert_id == concert_id)
        .order_by(LineupEntry.set_order)
        .all()
    )
    return [row.set_order for row in rows]


class TestMoveLineupEntry:
    """Coverage for `move_lineup_entry`."""

    def test_moving_down_yields_contiguous_ordering(self, db_session):
        concert = _make_concert(db_session)
        entries = _make_lineup(db_session, concert, 5)
        moved = entries[0]  # set_order 1

        result = move_lineup_entry(db_session, concert.id, moved.id, set_order=4)

        assert result.set_order == 4
        assert _all_set_orders(db_session, concert.id) == [1, 2, 3, 4, 5]

    def test_moving_up_yields_contiguous_ordering(self, db_session):
        concert = _make_concert(db_session)
        entries = _make_lineup(db_session, concert, 5)
        moved = entries[3]  # set_order 4

        result = move_lineup_entry(db_session, concert.id, moved.id, set_order=2)

        assert result.set_order == 2
        assert _all_set_orders(db_session, concert.id) == [1, 2, 3, 4, 5]

    def test_moving_down_shifts_only_entries_between_old_and_new_position(self, db_session):
        concert = _make_concert(db_session)
        entries = _make_lineup(db_session, concert, 5)
        moved = entries[0]  # set_order 1

        move_lineup_entry(db_session, concert.id, moved.id, set_order=4)

        for entry in entries:
            db_session.refresh(entry)
        assert entries[0].set_order == 4  # moved
        assert entries[1].set_order == 1  # was 2
        assert entries[2].set_order == 2  # was 3
        assert entries[3].set_order == 3  # was 4
        assert entries[4].set_order == 5  # unaffected

    def test_moving_up_shifts_only_entries_between_new_and_old_position(self, db_session):
        concert = _make_concert(db_session)
        entries = _make_lineup(db_session, concert, 5)
        moved = entries[3]  # set_order 4

        move_lineup_entry(db_session, concert.id, moved.id, set_order=2)

        for entry in entries:
            db_session.refresh(entry)
        assert entries[0].set_order == 1  # unaffected
        assert entries[1].set_order == 3  # was 2
        assert entries[2].set_order == 4  # was 3
        assert entries[3].set_order == 2  # moved
        assert entries[4].set_order == 5  # unaffected

    def test_moving_to_current_set_order_is_a_no_op(self, db_session):
        concert = _make_concert(db_session)
        entries = _make_lineup(db_session, concert, 3)
        entry = entries[1]  # set_order 2

        result = move_lineup_entry(db_session, concert.id, entry.id, set_order=2)

        assert result.id == entry.id
        assert result.set_order == 2
        assert _all_set_orders(db_session, concert.id) == [1, 2, 3]

    def test_out_of_range_set_order_above_n_is_clamped_to_last_position(self, db_session):
        concert = _make_concert(db_session)
        entries = _make_lineup(db_session, concert, 3)
        moved = entries[0]  # set_order 1

        result = move_lineup_entry(db_session, concert.id, moved.id, set_order=999)

        assert result.set_order == 3
        assert _all_set_orders(db_session, concert.id) == [1, 2, 3]

    def test_raises_when_concert_does_not_exist(self, db_session):
        with pytest.raises(ConcertNotFoundError):
            move_lineup_entry(db_session, concert_id=999, entry_id=1, set_order=1)

    def test_raises_when_entry_does_not_exist(self, db_session):
        concert = _make_concert(db_session)

        with pytest.raises(LineupEntryNotFoundError):
            move_lineup_entry(db_session, concert.id, entry_id=999, set_order=1)

    def test_raises_when_entry_belongs_to_a_different_concert(self, db_session):
        concert_a = _make_concert(db_session)
        concert_b = _make_concert(db_session)
        entry_a = _make_entry(db_session, concert_a, artist_name="A1", set_order=1)
        entry_b = _make_entry(db_session, concert_b, artist_name="B1", set_order=1)

        with pytest.raises(LineupEntryNotFoundError):
            move_lineup_entry(db_session, concert_a.id, entry_b.id, set_order=1)

        # Both concerts' lineups survive untouched.
        db_session.refresh(entry_a)
        db_session.refresh(entry_b)
        assert entry_a.set_order == 1
        assert entry_b.set_order == 1
