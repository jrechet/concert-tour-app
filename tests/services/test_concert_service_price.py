"""Unit tests for the concert price-update service logic (issue #817).

`update_ticket_price` in `src.services.concerts_service` already implements
the business logic this issue asks for (not-found/cancelled handling, price
assignment, commit, refresh); these tests exercise it end to end under the
names called out in the issue's acceptance criteria.
"""

from datetime import datetime
from decimal import Decimal

import pytest

from src.models import Concert
from src.services.concerts_service import (
    ConcertCancelledError,
    ConcertNotFoundError,
    update_ticket_price,
)
from tests.fixtures.dashboard_fixtures import create_concert, create_tour, create_venues

BASE_TIME = datetime(2024, 6, 15, 20, 0, 0)


def _create_concert(db_session, ticket_price="80.00", is_cancelled=False, cancellation_reason=None):
    venue = create_venues(db_session, count=1)[0]
    tour = create_tour(
        db_session, "Neon Skyline World Tour", "Aurora Belle",
        BASE_TIME.date(), BASE_TIME.date(), "active",
    )
    return create_concert(
        db_session, tour, venue, day_offset=0, ticket_price=ticket_price, base_time=BASE_TIME,
        is_cancelled=is_cancelled, cancellation_reason=cancellation_reason,
    )


def test_update_price_persists_new_price(db_session):
    concert = _create_concert(db_session, ticket_price="80.00")

    update_ticket_price(db_session, concert.id, Decimal("125.50"))

    reloaded = db_session.query(Concert).filter(Concert.id == concert.id).one()
    assert reloaded.ticket_price == Decimal("125.50")


def test_update_price_returns_concert(db_session):
    concert = _create_concert(db_session, ticket_price="80.00")

    result = update_ticket_price(db_session, concert.id, Decimal("99.99"))

    assert isinstance(result, Concert)
    assert result.id == concert.id
    assert result.ticket_price == Decimal("99.99")


def test_update_price_unknown_concert_raises_not_found(db_session):
    with pytest.raises(ConcertNotFoundError):
        update_ticket_price(db_session, 999, Decimal("50.00"))


def test_update_price_cancelled_concert_raises_conflict_error(db_session):
    concert = _create_concert(
        db_session, ticket_price="80.00", is_cancelled=True, cancellation_reason="Artist illness",
    )

    with pytest.raises(ConcertCancelledError):
        update_ticket_price(db_session, concert.id, Decimal("50.00"))

    reloaded = db_session.query(Concert).filter(Concert.id == concert.id).one()
    assert reloaded.ticket_price == Decimal("80.00")


def test_update_price_accepts_zero(db_session):
    concert = _create_concert(db_session, ticket_price="80.00")

    result = update_ticket_price(db_session, concert.id, Decimal("0"))

    assert result.ticket_price == Decimal("0")
    reloaded = db_session.query(Concert).filter(Concert.id == concert.id).one()
    assert reloaded.ticket_price == Decimal("0")
