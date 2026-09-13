"""Dedicated boundary-condition tests for Concert.is_almost_sold_out.

Complements tests/test_concert_sold_out_threshold.py (which covers the
ALMOST_SOLD_OUT_THRESHOLD config plumbing) with the specific percentage
boundaries called out for this feature: 0%, just below/above the 10%
threshold, exactly at the threshold, fully sold out, and zero-capacity.
"""

from src.models import Concert, Venue


def _make_concert(capacity, tickets_sold):
    venue = Venue(name="Test Arena", city="Testville", country="USA", capacity=capacity)
    return Concert(venue=venue, tickets_sold=tickets_sold)


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
