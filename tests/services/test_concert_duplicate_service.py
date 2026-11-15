"""Tests for `duplicate_concert`."""

from datetime import datetime, timedelta
from decimal import Decimal

import pytest

from src.models import Concert, LineupEntry
from src.services.concert_service import VenueScheduleConflictError, duplicate_concert
from src.services.concerts_service import ConcertNotFoundError
from tests.fixtures.dashboard_fixtures import create_concert, create_tour, create_venues

BASE_TIME = datetime(2025, 9, 1, 20, 0, 0)


def _create_source(db_session, ticket_price="80.00", tickets_sold=0, is_cancelled=False, cancellation_reason=None):
    venue = create_venues(db_session, count=1)[0]
    tour = create_tour(
        db_session, "Neon Skyline World Tour", "Aurora Belle",
        BASE_TIME.date(), BASE_TIME.date(), "active",
    )
    return create_concert(
        db_session, tour, venue, day_offset=0, ticket_price=ticket_price, base_time=BASE_TIME,
        tickets_sold=tickets_sold, is_cancelled=is_cancelled, cancellation_reason=cancellation_reason,
    )


def _add_lineup_entry(db_session, concert, artist_name, set_order):
    entry = LineupEntry(concert_id=concert.id, artist_name=artist_name, set_order=set_order)
    db_session.add(entry)
    db_session.commit()
    db_session.refresh(entry)
    return entry


class TestDuplicateConcertNotFound:
    """Coverage for the not-found rule."""

    def test_unknown_concert_id_raises_not_found_and_writes_nothing(self, db_session):
        source = _create_source(db_session)
        concert_count_before = db_session.query(Concert).count()

        with pytest.raises(ConcertNotFoundError):
            duplicate_concert(db_session, source.id + 999999, BASE_TIME + timedelta(days=1))

        assert db_session.query(Concert).count() == concert_count_before


class TestDuplicateConcertVenueConflict:
    """Coverage for the venue/date_time conflict rule."""

    def test_same_venue_same_time_raises_conflict_and_writes_nothing(self, db_session):
        source = _create_source(db_session)
        other_tour = create_tour(
            db_session, "Other Tour", "Other Artist", BASE_TIME.date(), BASE_TIME.date(), "active",
        )
        conflicting_time = BASE_TIME + timedelta(days=5)
        create_concert(
            db_session, other_tour, source.venue, day_offset=5, ticket_price="60.00", base_time=BASE_TIME,
        )
        concert_count_before = db_session.query(Concert).count()

        with pytest.raises(VenueScheduleConflictError):
            duplicate_concert(db_session, source.id, conflicting_time)

        assert db_session.query(Concert).count() == concert_count_before

    def test_cancelled_concert_at_same_venue_and_time_does_not_conflict(self, db_session):
        source = _create_source(db_session)
        other_tour = create_tour(
            db_session, "Other Tour", "Other Artist", BASE_TIME.date(), BASE_TIME.date(), "active",
        )
        conflicting_time = BASE_TIME + timedelta(days=5)
        create_concert(
            db_session, other_tour, source.venue, day_offset=5, ticket_price="60.00", base_time=BASE_TIME,
            is_cancelled=True, cancellation_reason="Venue closed",
        )

        result = duplicate_concert(db_session, source.id, conflicting_time)

        assert result.id != source.id
        assert result.date_time == conflicting_time

    def test_same_venue_different_time_succeeds(self, db_session):
        source = _create_source(db_session)
        other_tour = create_tour(
            db_session, "Other Tour", "Other Artist", BASE_TIME.date(), BASE_TIME.date(), "active",
        )
        create_concert(
            db_session, other_tour, source.venue, day_offset=5, ticket_price="60.00", base_time=BASE_TIME,
        )
        requested_time = BASE_TIME + timedelta(days=10)

        result = duplicate_concert(db_session, source.id, requested_time)

        assert result.id != source.id
        assert result.venue_id == source.venue_id
        assert result.date_time == requested_time

    def test_same_time_different_venue_succeeds(self, db_session):
        source = _create_source(db_session)
        other_venue = create_venues(db_session, count=2)[1]
        other_tour = create_tour(
            db_session, "Other Tour", "Other Artist", BASE_TIME.date(), BASE_TIME.date(), "active",
        )
        conflicting_time = BASE_TIME + timedelta(days=5)
        create_concert(
            db_session, other_tour, other_venue, day_offset=5, ticket_price="60.00", base_time=BASE_TIME,
        )

        result = duplicate_concert(db_session, source.id, conflicting_time)

        assert result.id != source.id
        assert result.venue_id == source.venue_id
        assert result.date_time == conflicting_time


class TestDuplicateConcertFieldCopy:
    """Coverage for the fields copied onto the duplicate."""

    def test_duplicate_copies_tour_venue_and_price_with_new_id(self, db_session):
        source = _create_source(db_session, ticket_price="125.50")
        requested_time = BASE_TIME + timedelta(days=7)

        result = duplicate_concert(db_session, source.id, requested_time)

        assert result.id != source.id
        assert result.tour_id == source.tour_id
        assert result.venue_id == source.venue_id
        assert result.ticket_price == Decimal("125.50")
        assert result.date_time == requested_time

    def test_duplicate_resets_tickets_sold_and_cancelled_flag(self, db_session):
        source = _create_source(
            db_session, tickets_sold=42, is_cancelled=True, cancellation_reason="Artist illness",
        )
        requested_time = BASE_TIME + timedelta(days=7)

        result = duplicate_concert(db_session, source.id, requested_time)

        assert result.tickets_sold == 0
        assert result.is_cancelled is False
        assert result.cancellation_reason is None

        db_session.refresh(source)
        assert source.tickets_sold == 42
        assert source.is_cancelled is True

    def test_duplicate_is_persisted(self, db_session):
        source = _create_source(db_session)
        requested_time = BASE_TIME + timedelta(days=7)

        result = duplicate_concert(db_session, source.id, requested_time)

        fetched = db_session.query(Concert).filter(Concert.id == result.id).first()
        assert fetched is not None
        assert fetched.date_time == requested_time


class TestDuplicateConcertLineupCopy:
    """Coverage for the lineup being copied, not re-pointed."""

    def test_lineup_entries_are_copied_with_new_rows(self, db_session):
        source = _create_source(db_session)
        _add_lineup_entry(db_session, source, "Opening Act", set_order=1)
        _add_lineup_entry(db_session, source, "Support Act", set_order=2)
        requested_time = BASE_TIME + timedelta(days=7)

        result = duplicate_concert(db_session, source.id, requested_time)

        duplicate_entries = (
            db_session.query(LineupEntry)
            .filter(LineupEntry.concert_id == result.id)
            .order_by(LineupEntry.set_order)
            .all()
        )
        assert [(e.artist_name, e.set_order) for e in duplicate_entries] == [
            ("Opening Act", 1), ("Support Act", 2),
        ]
        duplicate_entry_ids = {e.id for e in duplicate_entries}
        source_entry_ids = {
            e.id for e in db_session.query(LineupEntry).filter(LineupEntry.concert_id == source.id).all()
        }
        assert duplicate_entry_ids.isdisjoint(source_entry_ids)

    def test_mutating_duplicate_lineup_does_not_alter_source(self, db_session):
        source = _create_source(db_session)
        _add_lineup_entry(db_session, source, "Opening Act", set_order=1)
        requested_time = BASE_TIME + timedelta(days=7)

        result = duplicate_concert(db_session, source.id, requested_time)

        duplicate_entry = (
            db_session.query(LineupEntry).filter(LineupEntry.concert_id == result.id).first()
        )
        duplicate_entry.artist_name = "Changed Act"
        db_session.add(LineupEntry(concert_id=result.id, artist_name="Added Act", set_order=2))
        db_session.commit()

        source_entries = (
            db_session.query(LineupEntry).filter(LineupEntry.concert_id == source.id).all()
        )
        assert [e.artist_name for e in source_entries] == ["Opening Act"]

    def test_source_with_no_lineup_duplicates_with_no_lineup(self, db_session):
        source = _create_source(db_session)
        requested_time = BASE_TIME + timedelta(days=7)

        result = duplicate_concert(db_session, source.id, requested_time)

        assert db_session.query(LineupEntry).filter(LineupEntry.concert_id == result.id).count() == 0
