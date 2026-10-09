"""Unit tests for `update_ticket_price` and `clear_lineup`."""

from datetime import datetime
from decimal import Decimal

import pytest

from src.models import LineupEntry
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
