"""Unit tests for `delete_lineup_entry`, independent of the HTTP layer."""

from datetime import datetime

import pytest

from src.models import LineupEntry
from src.services.concerts_service import ConcertNotFoundError
from src.services.lineup_service import (
    InvalidSetOrderError,
    LineupEntryNotFoundError,
    delete_lineup_entry,
    reorder_lineup_entry,
)
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


class TestDeleteLineupEntry:
    """Coverage for `delete_lineup_entry`."""

    def test_deletes_entry_and_commits(self, db_session):
        concert = _make_concert(db_session)
        entry = _make_entry(db_session, concert)

        delete_lineup_entry(db_session, concert.id, entry.id)

        assert db_session.query(LineupEntry).filter(LineupEntry.id == entry.id).first() is None

    def test_raises_when_concert_does_not_exist(self, db_session):
        with pytest.raises(ConcertNotFoundError):
            delete_lineup_entry(db_session, concert_id=999, entry_id=1)

    def test_raises_when_entry_does_not_exist(self, db_session):
        concert = _make_concert(db_session)

        with pytest.raises(LineupEntryNotFoundError):
            delete_lineup_entry(db_session, concert.id, entry_id=999)

    def test_raises_when_entry_belongs_to_a_different_concert(self, db_session):
        concert_a = _make_concert(db_session)
        concert_b = _make_concert(db_session)
        entry = _make_entry(db_session, concert_b)

        with pytest.raises(LineupEntryNotFoundError):
            delete_lineup_entry(db_session, concert_a.id, entry.id)

        # The entry must survive untouched on its real concert.
        assert db_session.query(LineupEntry).filter(LineupEntry.id == entry.id).first() is not None

    def test_other_entries_on_the_same_concert_are_left_untouched(self, db_session):
        concert = _make_concert(db_session)
        keep = _make_entry(db_session, concert, artist_name="Keep Me", set_order=1)
        remove = _make_entry(db_session, concert, artist_name="Remove Me", set_order=2)

        delete_lineup_entry(db_session, concert.id, remove.id)

        assert db_session.query(LineupEntry).filter(LineupEntry.id == keep.id).first() is not None
        assert db_session.query(LineupEntry).filter(LineupEntry.id == remove.id).first() is None


class TestReorderLineupEntry:
    """Coverage for `reorder_lineup_entry`."""

    def test_moving_to_later_position_shifts_entries_between_down_by_one(self, db_session):
        concert = _make_concert(db_session)
        entries = [
            _make_entry(db_session, concert, artist_name=f"Act {i}", set_order=i)
            for i in range(1, 6)
        ]
        moved = entries[0]  # set_order 1

        result = reorder_lineup_entry(db_session, concert.id, moved.id, new_set_order=4)

        assert result.set_order == 4
        for entry in entries:
            db_session.refresh(entry)
        assert entries[0].set_order == 4  # moved
        assert entries[1].set_order == 1  # was 2
        assert entries[2].set_order == 2  # was 3
        assert entries[3].set_order == 3  # was 4
        assert entries[4].set_order == 5  # unaffected

    def test_moving_to_earlier_position_shifts_entries_between_up_by_one(self, db_session):
        concert = _make_concert(db_session)
        entries = [
            _make_entry(db_session, concert, artist_name=f"Act {i}", set_order=i)
            for i in range(1, 6)
        ]
        moved = entries[3]  # set_order 4

        result = reorder_lineup_entry(db_session, concert.id, moved.id, new_set_order=2)

        assert result.set_order == 2
        for entry in entries:
            db_session.refresh(entry)
        assert entries[0].set_order == 1  # unaffected
        assert entries[1].set_order == 3  # was 2
        assert entries[2].set_order == 4  # was 3
        assert entries[3].set_order == 2  # moved
        assert entries[4].set_order == 5  # unaffected

    def test_new_set_order_zero_raises_invalid_set_order_error(self, db_session):
        concert = _make_concert(db_session)
        entry = _make_entry(db_session, concert)

        with pytest.raises(InvalidSetOrderError):
            reorder_lineup_entry(db_session, concert.id, entry.id, new_set_order=0)

    def test_new_set_order_negative_raises_invalid_set_order_error(self, db_session):
        concert = _make_concert(db_session)
        entry = _make_entry(db_session, concert)

        with pytest.raises(InvalidSetOrderError):
            reorder_lineup_entry(db_session, concert.id, entry.id, new_set_order=-1)

    def test_raises_when_concert_does_not_exist(self, db_session):
        with pytest.raises(ConcertNotFoundError):
            reorder_lineup_entry(db_session, concert_id=999, entry_id=1, new_set_order=1)

    def test_raises_when_entry_does_not_exist(self, db_session):
        concert = _make_concert(db_session)

        with pytest.raises(LineupEntryNotFoundError):
            reorder_lineup_entry(db_session, concert.id, entry_id=999, new_set_order=1)

    def test_raises_when_entry_belongs_to_a_different_concert(self, db_session):
        concert_a = _make_concert(db_session)
        concert_b = _make_concert(db_session)
        entry = _make_entry(db_session, concert_b)

        with pytest.raises(LineupEntryNotFoundError):
            reorder_lineup_entry(db_session, concert_a.id, entry.id, new_set_order=1)

        # The entry must survive untouched on its real concert.
        db_session.refresh(entry)
        assert entry.set_order == 1
