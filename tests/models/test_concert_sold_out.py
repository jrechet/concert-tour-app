"""Tests for `Concert.capacity`-driven sold-out logic: `tickets_remaining`
and `is_sold_out`.

Concerts are created through real `Tour`/`Venue` foreign keys (via
`tests/fixtures/dashboard_fixtures.py`), never a hardcoded `venue_id=1`.
Only the public `tickets_remaining`/`is_sold_out` properties are exercised,
never the private `_effective_capacity` helper.
"""

from datetime import datetime, timedelta

import pytest

from src.models import Concert
from tests.fixtures.dashboard_fixtures import create_concert, create_tour, create_venues

BASE_TIME = datetime(2024, 6, 15, 9, 0, 0)


def _make_tour(db_session, name="Capacity Test Tour"):
    return create_tour(
        db_session,
        name=name,
        artist="Test Artist",
        start_date=BASE_TIME.date(),
        end_date=(BASE_TIME + timedelta(days=30)).date(),
        status="planned",
    )


def _make_concert(db_session, capacity, tickets_sold):
    venue = create_venues(db_session, count=1)[0]
    tour = _make_tour(db_session)
    concert = create_concert(
        db_session, tour, venue, day_offset=10, ticket_price="50.00",
        base_time=BASE_TIME, tickets_sold=0,
    )
    concert.capacity = capacity
    concert.tickets_sold = tickets_sold
    db_session.commit()
    db_session.refresh(concert)
    return concert


def test_tickets_remaining_counts_down(db_session):
    concert = _make_concert(db_session, capacity=100, tickets_sold=40)

    assert concert.tickets_remaining == 60


def test_tickets_remaining_never_negative(db_session):
    """A concert whose capacity is reduced after tickets were already sold
    against it must clamp to 0 rather than reporting a negative count."""
    concert = _make_concert(db_session, capacity=100, tickets_sold=100)
    concert.capacity = 60

    assert concert.tickets_remaining == 0


def test_is_sold_out_true_when_no_tickets_remain(db_session):
    concert = _make_concert(db_session, capacity=100, tickets_sold=100)

    assert concert.is_sold_out is True


def test_is_sold_out_false_when_tickets_remain(db_session):
    concert = _make_concert(db_session, capacity=100, tickets_sold=40)

    assert concert.is_sold_out is False


def test_oversold_tickets_rejected(db_session):
    venue = create_venues(db_session, count=1)[0]
    tour = _make_tour(db_session)
    concert = create_concert(
        db_session, tour, venue, day_offset=10, ticket_price="50.00",
        base_time=BASE_TIME, tickets_sold=0,
    )
    concert.capacity = 100

    with pytest.raises(ValueError):
        concert.tickets_sold = 101


def test_negative_capacity_rejected(db_session):
    venue = create_venues(db_session, count=1)[0]
    tour = _make_tour(db_session)
    concert = create_concert(
        db_session, tour, venue, day_offset=10, ticket_price="50.00",
        base_time=BASE_TIME, tickets_sold=0,
    )

    with pytest.raises(ValueError):
        concert.capacity = -1
