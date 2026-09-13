"""Tests for the Concert.is_almost_sold_out threshold logic and the
ALMOST_SOLD_OUT_THRESHOLD config value it reads from."""

import importlib
from datetime import datetime, timedelta

import pytest

from src import config
from src.models import Concert, Venue
from tests.fixtures.dashboard_fixtures import create_concert, create_tour


def _make_tour(db_session, name="Threshold Test Tour"):
    return create_tour(
        db_session,
        name=name,
        artist="Test Artist",
        start_date=datetime.now().date(),
        end_date=(datetime.now() + timedelta(days=30)).date(),
        status="planned",
    )


def _make_venue(db_session, capacity):
    venue = Venue(name="Test Arena", city="Testville", country="USA", capacity=capacity)
    db_session.add(venue)
    db_session.commit()
    db_session.refresh(venue)
    return venue


def test_default_threshold_is_ten_percent():
    """Absent an env override, the documented 10% default applies."""
    assert config.ALMOST_SOLD_OUT_THRESHOLD == 0.10


def test_threshold_is_configurable_via_env_var(monkeypatch):
    """The threshold is read from the environment, not hardcoded."""
    monkeypatch.setenv("ALMOST_SOLD_OUT_THRESHOLD", "0.25")
    reloaded = importlib.reload(config)
    try:
        assert reloaded.ALMOST_SOLD_OUT_THRESHOLD == 0.25
    finally:
        monkeypatch.delenv("ALMOST_SOLD_OUT_THRESHOLD", raising=False)
        importlib.reload(config)


def test_is_almost_sold_out_true_below_threshold(db_session):
    """9 remaining out of 100 (9%) is below the 10% threshold."""
    venue = _make_venue(db_session, capacity=100)
    tour = _make_tour(db_session)
    concert = create_concert(
        db_session, tour, venue, day_offset=10, ticket_price="50.00",
        base_time=datetime.now(), tickets_sold=91,
    )

    assert concert.is_almost_sold_out is True


def test_is_almost_sold_out_false_at_exact_boundary(db_session):
    """Exactly 10% remaining is NOT almost sold out — the boundary is exclusive."""
    venue = _make_venue(db_session, capacity=100)
    tour = _make_tour(db_session)
    concert = create_concert(
        db_session, tour, venue, day_offset=10, ticket_price="50.00",
        base_time=datetime.now(), tickets_sold=90,
    )

    assert concert.is_almost_sold_out is False


def test_is_almost_sold_out_false_well_above_threshold(db_session):
    venue = _make_venue(db_session, capacity=100)
    tour = _make_tour(db_session)
    concert = create_concert(
        db_session, tour, venue, day_offset=10, ticket_price="50.00",
        base_time=datetime.now(), tickets_sold=50,
    )

    assert concert.is_almost_sold_out is False


def test_is_almost_sold_out_false_when_capacity_zero(db_session):
    """Zero total tickets must not raise ZeroDivisionError."""
    venue = _make_venue(db_session, capacity=0)
    tour = _make_tour(db_session)
    concert = create_concert(
        db_session, tour, venue, day_offset=10, ticket_price="50.00",
        base_time=datetime.now(), tickets_sold=0,
    )

    assert concert.is_almost_sold_out is False


def test_is_almost_sold_out_false_when_venue_unknown():
    """No venue attached means capacity can't be computed."""
    concert = Concert(tickets_sold=0)

    assert concert.is_almost_sold_out is False


def test_tickets_sold_cannot_be_negative():
    with pytest.raises(ValueError):
        Concert(tickets_sold=-1)


def test_tickets_sold_cannot_exceed_venue_capacity():
    venue = Venue(name="Small Club", city="Testville", country="USA", capacity=50)
    with pytest.raises(ValueError):
        Concert(venue=venue, tickets_sold=51)


def test_tickets_sold_at_capacity_is_allowed():
    venue = Venue(name="Small Club", city="Testville", country="USA", capacity=50)
    concert = Concert(venue=venue, tickets_sold=50)

    assert concert.tickets_sold == 50
