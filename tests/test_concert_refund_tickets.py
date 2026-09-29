"""Unit tests for `refund_tickets`, independent of the HTTP layer."""

from datetime import datetime

import pytest

from src.services.concerts_service import (
    ConcertNotFoundError,
    InsufficientSoldTicketsError,
    refund_tickets,
)
from tests.fixtures.dashboard_fixtures import create_concert, create_tour, create_venues

BASE_TIME = datetime(2024, 6, 15, 20, 0, 0)


def _make_tour(db_session, name="Refund Tickets Tour"):
    return create_tour(
        db_session, name, "Test Artist", BASE_TIME.date(), BASE_TIME.date(), "active",
    )


class TestRefundTickets:
    """Coverage for `refund_tickets`."""

    def test_refunding_under_sold_count_decreases_tickets_sold(self, db_session):
        venue = create_venues(db_session, count=1)[0]
        tour = _make_tour(db_session)
        concert = create_concert(
            db_session, tour, venue, day_offset=0, ticket_price="80.00",
            base_time=BASE_TIME, tickets_sold=10,
        )

        updated = refund_tickets(concert.id, 4, db_session)

        assert updated.id == concert.id
        assert updated.tickets_sold == 6

    def test_refunding_all_sold_tickets_succeeds(self, db_session):
        venue = create_venues(db_session, count=1)[0]
        tour = _make_tour(db_session, "Full Refund Tour")
        concert = create_concert(
            db_session, tour, venue, day_offset=0, ticket_price="80.00",
            base_time=BASE_TIME, tickets_sold=5,
        )

        updated = refund_tickets(concert.id, 5, db_session)

        assert updated.tickets_sold == 0

    def test_refunding_more_than_sold_raises_and_does_not_mutate(self, db_session):
        venue = create_venues(db_session, count=1)[0]
        tour = _make_tour(db_session, "Over Refund Tour")
        concert = create_concert(
            db_session, tour, venue, day_offset=0, ticket_price="80.00",
            base_time=BASE_TIME, tickets_sold=5,
        )

        with pytest.raises(InsufficientSoldTicketsError):
            refund_tickets(concert.id, 6, db_session)

        db_session.refresh(concert)
        assert concert.tickets_sold == 5

    def test_refunding_on_nonexistent_concert_raises_not_found(self, db_session):
        with pytest.raises(ConcertNotFoundError):
            refund_tickets(999999, 1, db_session)
