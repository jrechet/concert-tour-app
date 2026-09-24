"""Unit tests for the `days_until_concert` computed field on `ConcertResponse`.

Concerts are seeded through real `Venue`/`Tour` foreign keys (via
`tests/fixtures/dashboard_fixtures.py`) rather than hardcoded ids, assertions
go through the public `ConcertResponse.model_validate` serialization method (not
the `Concert.days_until_concert` property directly), and `get_reference_time`
(the shared "current date" utility) is mocked so results don't depend on the
real wall clock.
"""

from datetime import datetime
from decimal import Decimal
from unittest.mock import patch

from src.models import Concert
from src.schemas.concert import ConcertResponse
from tests.fixtures.dashboard_fixtures import create_concert, create_tour, create_venues

REFERENCE_TIME = datetime(2024, 6, 15, 9, 0, 0)


def _make_tour(db_session):
    return create_tour(
        db_session,
        name="Countdown Tour",
        artist="Test Artist",
        start_date=REFERENCE_TIME.date(),
        end_date=REFERENCE_TIME.date(),
        status="active",
    )


def _make_concert(db_session, day_offset):
    venue = create_venues(db_session, count=1)[0]
    tour = _make_tour(db_session)
    return create_concert(
        db_session, tour, venue, day_offset=day_offset, ticket_price="50.00", base_time=REFERENCE_TIME,
    )


def _make_concert_at(db_session, date_time):
    venue = create_venues(db_session, count=1)[0]
    tour = _make_tour(db_session)
    concert = Concert(
        tour_id=tour.id, venue_id=venue.id, date_time=date_time, ticket_price=Decimal("50.00"),
    )
    db_session.add(concert)
    db_session.commit()
    db_session.refresh(concert)
    return concert


class TestDaysUntilConcert:
    """Coverage for `ConcertResponse.days_until_concert`."""

    @patch("src.models.concert.get_reference_time", return_value=REFERENCE_TIME)
    def test_future_concert_returns_correct_positive_days(self, mock_reference_time, db_session):
        concert = _make_concert(db_session, day_offset=10)

        response = ConcertResponse.model_validate(concert, from_attributes=True)

        assert response.days_until_concert == 10

    @patch("src.models.concert.get_reference_time", return_value=REFERENCE_TIME)
    def test_concert_scheduled_today_returns_zero(self, mock_reference_time, db_session):
        concert = _make_concert(db_session, day_offset=0)

        response = ConcertResponse.model_validate(concert, from_attributes=True)

        assert response.days_until_concert == 0

    @patch("src.models.concert.get_reference_time", return_value=REFERENCE_TIME)
    def test_concert_scheduled_tomorrow_returns_one(self, mock_reference_time, db_session):
        concert = _make_concert(db_session, day_offset=1)

        response = ConcertResponse.model_validate(concert, from_attributes=True)

        assert response.days_until_concert == 1

    @patch("src.models.concert.get_reference_time")
    def test_midnight_boundary_does_not_produce_off_by_one_error(self, mock_reference_time, db_session):
        """A concert 10 minutes after midnight, with the reference time 5
        minutes before midnight the previous day, is one calendar day away
        even though barely 15 minutes separate the two timestamps — the
        comparison must be by date, not elapsed time.
        """
        mock_reference_time.return_value = datetime(2024, 6, 15, 23, 55, 0)
        concert = _make_concert_at(db_session, datetime(2024, 6, 16, 0, 10, 0))

        response = ConcertResponse.model_validate(concert, from_attributes=True)

        assert response.days_until_concert == 1
