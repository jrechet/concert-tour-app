"""Unit tests for `reschedule_concert`, independent of the HTTP layer."""

from datetime import datetime, timedelta, timezone

import pytest

from src.services.concerts_service import (
    ConcertCancelledError,
    ConcertNotFoundError,
    InvalidDateError,
    reschedule_concert,
)
from tests.fixtures.dashboard_fixtures import create_concert, create_tour, create_venues

BASE_TIME = datetime.now(timezone.utc).replace(microsecond=0, tzinfo=None) + timedelta(days=30)


def _make_tour(db_session, name="Reschedule Tour"):
    return create_tour(
        db_session, name, "Test Artist", BASE_TIME.date(), BASE_TIME.date(), "active",
    )


class TestRescheduleConcert:
    """Coverage for `reschedule_concert`."""

    def test_reschedule_updates_date_time(self, db_session):
        venue = create_venues(db_session, count=1)[0]
        tour = _make_tour(db_session)
        concert = create_concert(
            db_session, tour, venue, day_offset=0, ticket_price="80.00", base_time=BASE_TIME,
        )
        new_date_time = BASE_TIME + timedelta(days=10)

        updated = reschedule_concert(db_session, concert.id, new_date_time)

        assert updated.id == concert.id
        assert updated.date_time == new_date_time

    def test_reschedule_accepts_timezone_aware_date_time(self, db_session):
        venue = create_venues(db_session, count=1)[0]
        tour = _make_tour(db_session, "Aware Tour")
        concert = create_concert(
            db_session, tour, venue, day_offset=0, ticket_price="80.00", base_time=BASE_TIME,
        )
        new_date_time = BASE_TIME.replace(tzinfo=timezone.utc) + timedelta(days=5)

        updated = reschedule_concert(db_session, concert.id, new_date_time)

        assert updated.id == concert.id

    def test_reschedule_nonexistent_concert_raises_not_found(self, db_session):
        with pytest.raises(ConcertNotFoundError):
            reschedule_concert(db_session, 999999, BASE_TIME + timedelta(days=1))

    def test_reschedule_cancelled_concert_raises_and_does_not_mutate(self, db_session):
        venue = create_venues(db_session, count=1)[0]
        tour = _make_tour(db_session, "Cancelled Tour")
        concert = create_concert(
            db_session, tour, venue, day_offset=0, ticket_price="80.00", base_time=BASE_TIME,
            is_cancelled=True, cancellation_reason="Weather",
        )
        original_date_time = concert.date_time

        with pytest.raises(ConcertCancelledError):
            reschedule_concert(db_session, concert.id, BASE_TIME + timedelta(days=1))

        db_session.refresh(concert)
        assert concert.date_time == original_date_time

    def test_reschedule_to_past_date_raises_and_does_not_mutate(self, db_session):
        venue = create_venues(db_session, count=1)[0]
        tour = _make_tour(db_session, "Past Date Tour")
        concert = create_concert(
            db_session, tour, venue, day_offset=0, ticket_price="80.00", base_time=BASE_TIME,
        )
        original_date_time = concert.date_time
        past_date_time = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=1)

        with pytest.raises(InvalidDateError):
            reschedule_concert(db_session, concert.id, past_date_time)

        db_session.refresh(concert)
        assert concert.date_time == original_date_time
