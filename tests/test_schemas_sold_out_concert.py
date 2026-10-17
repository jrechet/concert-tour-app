"""Unit tests for `SoldOutConcertRead`.

Concerts are seeded through real `Venue`/`Tour` foreign keys (via
`tests/fixtures/dashboard_fixtures.py`) rather than hardcoded ids, matching
the convention used for `ConcertResponse` in `tests/test_concert_schema.py`.
"""

from datetime import date, datetime

import pytest
from pydantic import ValidationError

from src.schemas.concert import SoldOutConcertRead
from tests.fixtures.dashboard_fixtures import create_concert, create_tour, create_venues


def _make_sold_out_concert(db_session, capacity_override=None, tickets_sold=100):
    venue = create_venues(db_session, count=1)[0]
    if capacity_override is not None:
        venue.capacity = capacity_override
        db_session.commit()
        db_session.refresh(venue)
    tour = create_tour(
        db_session,
        name="World Tour",
        artist="Test Artist",
        start_date=date(2024, 1, 1),
        end_date=date(2024, 12, 31),
        status="active",
    )
    return create_concert(
        db_session, tour, venue, day_offset=0, ticket_price="50.00",
        base_time=datetime(2024, 6, 1, 20, 0), tickets_sold=tickets_sold,
    )


class TestSoldOutConcertRead:
    """Coverage for `SoldOutConcertRead.model_validate`."""

    def test_serialises_concert_orm_instance(self, db_session):
        concert = _make_sold_out_concert(db_session, capacity_override=100, tickets_sold=100)

        read = SoldOutConcertRead.model_validate(concert)

        assert read.id == concert.id
        assert read.title == concert.tour.name
        assert read.start_datetime == concert.date_time
        assert read.start_datetime.isoformat() == "2024-06-01T20:00:00"
        assert read.venue.id == concert.venue.id
        assert read.venue.name == concert.venue.name
        assert read.venue.city == concert.venue.city
        assert read.capacity == concert.venue.capacity
        assert read.tickets_sold == concert.tickets_sold

    def test_tickets_remaining_is_zero(self, db_session):
        # Capacity (100) exceeds tickets_sold (40), so this concert is not
        # actually sold out; tickets_remaining must still read 0.
        concert = _make_sold_out_concert(db_session, capacity_override=100, tickets_sold=40)

        read = SoldOutConcertRead.model_validate(concert)

        assert read.tickets_remaining == 0

    def test_rejects_missing_required_fields(self):
        with pytest.raises(ValidationError):
            SoldOutConcertRead(id=1)
