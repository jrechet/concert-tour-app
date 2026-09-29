"""Unit tests for `sell_tickets`, independent of the HTTP layer."""

from datetime import datetime

import pytest

from src.services.concerts_service import (
    ConcertCancelledError,
    ConcertCapacityExceededError,
    ConcertNotFoundError,
    sell_tickets,
)
from tests.fixtures.dashboard_fixtures import create_concert, create_tour, create_venues

BASE_TIME = datetime(2024, 6, 15, 20, 0, 0)


def _make_tour(db_session, name="Sell Tickets Tour"):
    return create_tour(
        db_session, name, "Test Artist", BASE_TIME.date(), BASE_TIME.date(), "active",
    )


class TestSellTickets:
    """Coverage for `sell_tickets`."""

    def test_selling_under_capacity_increases_tickets_sold(self, db_session):
        venue = create_venues(db_session, count=1)[0]
        tour = _make_tour(db_session)
        concert = create_concert(
            db_session, tour, venue, day_offset=0, ticket_price="80.00",
            base_time=BASE_TIME, tickets_sold=10,
        )

        updated = sell_tickets(concert.id, 5, db_session)

        assert updated.id == concert.id
        assert updated.tickets_sold == 15

    def test_selling_up_to_exact_capacity_succeeds(self, db_session):
        venue = create_venues(db_session, count=1)[0]
        tour = _make_tour(db_session, "Exact Capacity Tour")
        concert = create_concert(
            db_session, tour, venue, day_offset=0, ticket_price="80.00",
            base_time=BASE_TIME, tickets_sold=venue.capacity - 5,
        )

        updated = sell_tickets(concert.id, 5, db_session)

        assert updated.tickets_sold == venue.capacity

    def test_selling_beyond_capacity_raises_and_does_not_mutate(self, db_session):
        venue = create_venues(db_session, count=1)[0]
        tour = _make_tour(db_session, "Over Capacity Tour")
        concert = create_concert(
            db_session, tour, venue, day_offset=0, ticket_price="80.00",
            base_time=BASE_TIME, tickets_sold=venue.capacity - 5,
        )

        with pytest.raises(ConcertCapacityExceededError):
            sell_tickets(concert.id, 6, db_session)

        db_session.refresh(concert)
        assert concert.tickets_sold == venue.capacity - 5

    def test_selling_on_cancelled_concert_raises_and_does_not_mutate(self, db_session):
        venue = create_venues(db_session, count=1)[0]
        tour = _make_tour(db_session, "Cancelled Tour")
        concert = create_concert(
            db_session, tour, venue, day_offset=0, ticket_price="80.00",
            base_time=BASE_TIME, tickets_sold=10,
            is_cancelled=True, cancellation_reason="Weather",
        )

        with pytest.raises(ConcertCancelledError):
            sell_tickets(concert.id, 1, db_session)

        db_session.refresh(concert)
        assert concert.tickets_sold == 10

    def test_selling_on_nonexistent_concert_raises_not_found(self, db_session):
        with pytest.raises(ConcertNotFoundError):
            sell_tickets(999999, 1, db_session)
