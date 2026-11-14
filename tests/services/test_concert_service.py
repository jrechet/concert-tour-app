"""Unit tests for `update_ticket_price`, `clear_lineup`, and
`list_concerts_for_artist`."""

from datetime import datetime
from decimal import Decimal

import pytest
from sqlalchemy import event as sa_event

from src.models import LineupEntry
from src.services.concert_service import list_concerts_for_artist
from src.services.concerts_service import (
    ConcertCancelledError,
    ConcertNotFoundError,
    update_ticket_price,
)
from src.services.lineup_service import clear_lineup
from tests.fixtures.dashboard_fixtures import create_concert, create_tour, create_venues

BASE_TIME = datetime(2024, 6, 15, 20, 0, 0)


def _create_active_concert(db_session, ticket_price="80.00"):
    venue = create_venues(db_session, count=1)[0]
    tour = create_tour(
        db_session, "Neon Skyline World Tour", "Aurora Belle",
        BASE_TIME.date(), BASE_TIME.date(), "active",
    )
    return create_concert(db_session, tour, venue, day_offset=0, ticket_price=ticket_price, base_time=BASE_TIME)


def _add_lineup_entry(db_session, concert, artist_name="Opening Act", set_order=1):
    entry = LineupEntry(concert_id=concert.id, artist_name=artist_name, set_order=set_order)
    db_session.add(entry)
    db_session.commit()
    db_session.refresh(entry)
    return entry


class TestUpdateTicketPrice:
    """Coverage for `update_ticket_price`."""

    def test_unknown_concert_raises_not_found(self, db_session):
        with pytest.raises(ConcertNotFoundError):
            update_ticket_price(db_session, 999, Decimal("50.00"))

    def test_cancelled_concert_raises_conflict_and_does_not_mutate_price(self, db_session):
        concert = _create_active_concert(db_session, ticket_price="80.00")
        concert.is_cancelled = True
        concert.cancellation_reason = "Artist illness"
        db_session.commit()

        with pytest.raises(ConcertCancelledError):
            update_ticket_price(db_session, concert.id, Decimal("50.00"))

        db_session.refresh(concert)
        assert concert.ticket_price == Decimal("80.00")

    def test_active_concert_price_is_updated_committed_and_returned(self, db_session):
        concert = _create_active_concert(db_session, ticket_price="80.00")

        updated = update_ticket_price(db_session, concert.id, Decimal("125.50"))

        assert updated.id == concert.id
        assert updated.ticket_price == Decimal("125.50")

        db_session.refresh(concert)
        assert concert.ticket_price == Decimal("125.50")


class TestClearLineup:
    """Coverage for `clear_lineup`."""

    def test_clear_lineup_removes_all_acts_keeps_concert(self, db_session):
        concert = _create_active_concert(db_session)
        _add_lineup_entry(db_session, concert, artist_name="Opening Act", set_order=1)
        _add_lineup_entry(db_session, concert, artist_name="Support Act", set_order=2)

        clear_lineup(db_session, concert.id)

        assert db_session.query(LineupEntry).filter(LineupEntry.concert_id == concert.id).count() == 0
        db_session.refresh(concert)
        assert concert is not None

    def test_clear_lineup_unknown_concert_raises_not_found(self, db_session):
        with pytest.raises(ConcertNotFoundError):
            clear_lineup(db_session, 999)

    def test_clear_lineup_on_empty_lineup_is_noop(self, db_session):
        concert = _create_active_concert(db_session)

        clear_lineup(db_session, concert.id)

        assert db_session.query(LineupEntry).filter(LineupEntry.concert_id == concert.id).count() == 0
        db_session.refresh(concert)
        assert concert is not None


def _create_concert(db_session, day_offset, is_cancelled=False, cancellation_reason=None):
    """Persist a concert on its own tour/venue, for lineup-matching tests
    where concerts must not share a tour/venue with each other."""
    venue = create_venues(db_session, count=1)[0]
    tour = create_tour(
        db_session, "Neon Skyline World Tour", "Aurora Belle",
        BASE_TIME.date(), BASE_TIME.date(), "active",
    )
    return create_concert(
        db_session, tour, venue, day_offset=day_offset, ticket_price="80.00", base_time=BASE_TIME,
        is_cancelled=is_cancelled, cancellation_reason=cancellation_reason,
    )


class TestListConcertsForArtist:
    """Coverage for `list_concerts_for_artist`."""

    def test_returns_concerts_sorted_by_date_ascending(self, db_session):
        later_concert = _create_concert(db_session, day_offset=30)
        soonest_concert = _create_concert(db_session, day_offset=5)
        middle_concert = _create_concert(db_session, day_offset=10)
        for concert in (later_concert, soonest_concert, middle_concert):
            _add_lineup_entry(db_session, concert, artist_name="Nova Rae", set_order=1)

        result = list_concerts_for_artist(db_session, "Nova Rae")

        assert [concert.id for concert in result] == [
            soonest_concert.id, middle_concert.id, later_concert.id,
        ]

    def test_excludes_cancelled_concerts(self, db_session):
        cancelled_concert = _create_concert(
            db_session, day_offset=5, is_cancelled=True, cancellation_reason="Artist illness",
        )
        active_concert = _create_concert(db_session, day_offset=10)
        _add_lineup_entry(db_session, cancelled_concert, artist_name="Nova Rae", set_order=1)
        _add_lineup_entry(db_session, active_concert, artist_name="Nova Rae", set_order=1)

        result = list_concerts_for_artist(db_session, "Nova Rae")

        returned_ids = [concert.id for concert in result]
        assert returned_ids == [active_concert.id]
        assert cancelled_concert.id not in returned_ids

    def test_excludes_concerts_without_the_artist_in_lineup(self, db_session):
        with_artist = _create_concert(db_session, day_offset=5)
        without_artist = _create_concert(db_session, day_offset=10)
        _add_lineup_entry(db_session, with_artist, artist_name="Nova Rae", set_order=1)
        _add_lineup_entry(db_session, without_artist, artist_name="Opening Act", set_order=1)

        result = list_concerts_for_artist(db_session, "Nova Rae")

        returned_ids = [concert.id for concert in result]
        assert returned_ids == [with_artist.id]
        assert without_artist.id not in returned_ids

    def test_returns_empty_list_when_artist_has_no_concerts(self, db_session):
        concert = _create_concert(db_session, day_offset=5)
        _add_lineup_entry(db_session, concert, artist_name="Opening Act", set_order=1)

        result = list_concerts_for_artist(db_session, "Nova Rae")

        assert result == []

    def test_venue_and_city_are_loaded_without_extra_query(self, db_session):
        concert = _create_concert(db_session, day_offset=5)
        _add_lineup_entry(db_session, concert, artist_name="Nova Rae", set_order=1)
        expected_city = concert.venue.city
        db_session.expire_all()

        queries = []
        engine = db_session.get_bind()

        def _record(conn, cursor, statement, parameters, context, executemany):
            queries.append(statement)

        sa_event.listen(engine, "before_cursor_execute", _record)
        try:
            result = list_concerts_for_artist(db_session, "Nova Rae")
            cities = [concert.venue.city for concert in result]
        finally:
            sa_event.remove(engine, "before_cursor_execute", _record)

        select_queries = [q for q in queries if q.strip().upper().startswith("SELECT")]
        assert len(select_queries) == 1
        assert cities == [expected_city]
