"""Dedicated boundary-condition tests for Concert.is_almost_sold_out.

Complements tests/test_concert_sold_out_threshold.py (which covers the
ALMOST_SOLD_OUT_THRESHOLD config plumbing) with the specific percentage
boundaries called out for this feature: 0%, just below/above the 10%
threshold, exactly at the threshold, fully sold out, and zero-capacity.
"""

from datetime import date, datetime, timedelta
from decimal import Decimal

import pytest

from src.models import Concert, Venue
from src.models.concert import ConcertStatus
from src.models.exceptions import ConcertDateInPastError, ConcertNotCancelledError
from tests.fixtures.dashboard_fixtures import create_tour, create_venues

REFERENCE_TIME = datetime(2024, 6, 15, 9, 0, 0)


def _make_concert(capacity, tickets_sold):
    venue = Venue(name="Test Arena", city="Testville", country="USA", capacity=capacity)
    return Concert(venue=venue, tickets_sold=tickets_sold)


def _make_persisted_concert(db_session, notes=None):
    venue = create_venues(db_session, count=1)[0]
    tour = create_tour(
        db_session,
        name="Countdown Tour",
        artist="Test Artist",
        start_date=REFERENCE_TIME.date(),
        end_date=REFERENCE_TIME.date(),
        status="active",
    )
    concert = Concert(
        tour_id=tour.id,
        venue_id=venue.id,
        date_time=REFERENCE_TIME,
        ticket_price=Decimal("50.00"),
        notes=notes,
    )
    db_session.add(concert)
    db_session.commit()
    db_session.refresh(concert)
    return concert


def test_is_almost_sold_out_false_at_zero_percent_sold():
    concert = _make_concert(capacity=100, tickets_sold=0)

    assert concert.is_almost_sold_out is False


def test_is_almost_sold_out_false_just_below_threshold():
    """89% sold leaves 11% remaining — still above the 10% threshold."""
    concert = _make_concert(capacity=100, tickets_sold=89)

    assert concert.is_almost_sold_out is False


def test_is_almost_sold_out_true_just_above_threshold():
    """91% sold leaves 9% remaining — below the 10% threshold."""
    concert = _make_concert(capacity=100, tickets_sold=91)

    assert concert.is_almost_sold_out is True


def test_is_almost_sold_out_false_at_exact_boundary():
    """Exactly 90% sold leaves exactly 10% remaining. The boundary is
    exclusive (< threshold, not <=), so this must NOT be almost sold out.
    """
    concert = _make_concert(capacity=100, tickets_sold=90)

    assert concert.is_almost_sold_out is False


def test_is_almost_sold_out_true_at_hundred_percent_sold():
    concert = _make_concert(capacity=100, tickets_sold=100)

    assert concert.is_almost_sold_out is True


def test_is_almost_sold_out_false_when_total_tickets_is_zero():
    """Zero total tickets must not raise ZeroDivisionError, and is treated
    as not almost sold out since the ratio can't be meaningfully computed.
    """
    concert = _make_concert(capacity=0, tickets_sold=0)

    assert concert.is_almost_sold_out is False


def test_tickets_remaining_partial_sales():
    concert = _make_concert(capacity=100, tickets_sold=40)

    assert concert.tickets_remaining == 60


def test_is_sold_out_true_when_no_tickets_remain():
    concert = _make_concert(capacity=100, tickets_sold=100)

    assert concert.tickets_remaining == 0
    assert concert.is_sold_out is True


def test_is_sold_out_false_when_tickets_remain():
    concert = _make_concert(capacity=100, tickets_sold=40)

    assert concert.is_sold_out is False


def test_tickets_remaining_never_negative_when_oversold():
    """A concert sold past its venue's capacity (e.g. the venue's capacity
    was reduced after tickets were already sold) must clamp to 0 rather
    than reporting a negative remaining count, and must still be sold out.
    """
    concert = _make_concert(capacity=100, tickets_sold=100)
    concert.venue.capacity = 80

    assert concert.tickets_remaining == 0
    assert concert.is_sold_out is True


def test_persisted_concert_created_without_notes_reads_back_none(db_session):
    concert = _make_persisted_concert(db_session)
    concert_id = concert.id
    db_session.expunge(concert)

    reloaded = db_session.query(Concert).filter_by(id=concert_id).one()

    assert reloaded.notes is None


def test_persisted_concert_with_500_char_notes_round_trips_unchanged(db_session):
    notes = "n" * 500
    concert = _make_persisted_concert(db_session, notes=notes)
    concert_id = concert.id
    db_session.expunge(concert)

    reloaded = db_session.query(Concert).filter_by(id=concert_id).one()

    assert reloaded.notes == notes
    assert len(reloaded.notes) == 500


# --- Concert.uncancel() ------------------------------------------------
#
# These build on `_make_persisted_concert` (above) but set `status`
# directly, mirroring `tests/models/test_concert_model.py`, rather than
# going through the unrelated boolean `is_cancelled`/`cancellation_reason`
# columns -- a separate, pre-existing cancellation mechanism (see
# `tests/test_concert_cancellation_model.py`) that `status` does not
# derive from or sync with.

def _make_concert_with_status(db_session, status, date_time):
    venue = create_venues(db_session, count=1)[0]
    tour = create_tour(
        db_session,
        name="Countdown Tour",
        artist="Test Artist",
        start_date=date_time.date(),
        end_date=date_time.date(),
        status="active",
    )
    concert = Concert(
        tour_id=tour.id,
        venue_id=venue.id,
        date_time=date_time,
        ticket_price=Decimal("50.00"),
        tickets_sold=3,
        notes="Keep me",
        status=status,
    )
    db_session.add(concert)
    db_session.commit()
    db_session.refresh(concert)
    return concert


def _tomorrow_datetime():
    return datetime.combine(date.today() + timedelta(days=1), datetime.min.time())


def _today_datetime():
    return datetime.combine(date.today(), datetime.min.time())


def _yesterday_datetime():
    return datetime.combine(date.today() - timedelta(days=1), datetime.min.time())


def test_uncancel_moves_cancelled_concert_to_scheduled(db_session):
    concert = _make_concert_with_status(db_session, ConcertStatus.cancelled, _tomorrow_datetime())

    concert.uncancel()

    assert concert.status is ConcertStatus.scheduled


def test_uncancel_leaves_other_fields_unchanged(db_session):
    concert = _make_concert_with_status(db_session, ConcertStatus.cancelled, _tomorrow_datetime())
    tour_id, venue_id, date_time = concert.tour_id, concert.venue_id, concert.date_time
    ticket_price, tickets_sold, notes = concert.ticket_price, concert.tickets_sold, concert.notes

    concert.uncancel()

    assert concert.tour_id == tour_id
    assert concert.venue_id == venue_id
    assert concert.date_time == date_time
    assert concert.ticket_price == ticket_price
    assert concert.tickets_sold == tickets_sold
    assert concert.notes == notes


def test_uncancel_cancelled_concert_dated_today_succeeds(db_session):
    """Today is not in the past, so uncancelling must succeed."""
    concert = _make_concert_with_status(db_session, ConcertStatus.cancelled, _today_datetime())

    concert.uncancel()

    assert concert.status is ConcertStatus.scheduled


def test_uncancel_scheduled_concert_raises_not_cancelled(db_session):
    concert = _make_concert_with_status(db_session, ConcertStatus.scheduled, _tomorrow_datetime())

    with pytest.raises(ConcertNotCancelledError) as exc_info:
        concert.uncancel()

    assert "scheduled" in exc_info.value.detail
    assert concert.status is ConcertStatus.scheduled


def test_uncancel_scheduled_concert_in_the_past_also_raises_not_cancelled(db_session):
    """Not-cancelled is checked before the date, so a concert that is both
    not cancelled and past-dated deterministically raises
    `ConcertNotCancelledError`, never `ConcertDateInPastError`.
    """
    concert = _make_concert_with_status(db_session, ConcertStatus.scheduled, _yesterday_datetime())

    with pytest.raises(ConcertNotCancelledError):
        concert.uncancel()


def test_uncancel_cancelled_concert_in_the_past_raises_date_in_past(db_session):
    concert = _make_concert_with_status(db_session, ConcertStatus.cancelled, _yesterday_datetime())

    with pytest.raises(ConcertDateInPastError) as exc_info:
        concert.uncancel()

    assert "past" in exc_info.value.detail
    assert concert.status is ConcertStatus.cancelled
