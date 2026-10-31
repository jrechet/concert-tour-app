"""Dedicated boundary-condition tests for Concert.is_almost_sold_out.

Complements tests/test_concert_sold_out_threshold.py (which covers the
ALMOST_SOLD_OUT_THRESHOLD config plumbing) with the specific percentage
boundaries called out for this feature: 0%, just below/above the 10%
threshold, exactly at the threshold, fully sold out, and zero-capacity.
"""

from datetime import datetime
from decimal import Decimal

from src.models import Concert, Venue
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
