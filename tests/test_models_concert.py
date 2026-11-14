"""Tests for the authoritative `Concert.is_sold_out` derivation.

Concerts are always created through real tour/venue foreign keys (never a
hardcoded `venue_id=1`), and only the public `is_sold_out` property is
exercised — never the private `remaining_tickets`/`sold_out` internals.
"""

from datetime import datetime, timedelta

from tests.fixtures.dashboard_fixtures import create_concert, create_tour, create_venues


def _make_tour(db_session):
    return create_tour(
        db_session,
        name="Is Sold Out Test Tour",
        artist="Test Artist",
        start_date=datetime.now().date(),
        end_date=(datetime.now() + timedelta(days=30)).date(),
        status="planned",
    )


def test_is_sold_out_true_when_zero_remaining(db_session):
    """Every ticket sold (tickets_sold == venue.capacity) is sold out."""
    venue = create_venues(db_session, count=1)[0]
    tour = _make_tour(db_session)
    concert = create_concert(
        db_session, tour, venue, day_offset=10, ticket_price="50.00",
        base_time=datetime.now(), tickets_sold=venue.capacity,
    )

    assert concert.is_sold_out is True


def test_is_sold_out_true_when_oversold(db_session):
    """More tickets sold than the venue's capacity is still sold out."""
    venue = create_venues(db_session, count=1)[0]
    tour = _make_tour(db_session)

    from src.models import Concert

    concert = Concert(
        tour_id=tour.id,
        venue_id=venue.id,
        date_time=datetime.now() + timedelta(days=10),
        ticket_price=50,
        tickets_sold=venue.capacity + 50,
    )
    db_session.add(concert)
    db_session.commit()
    db_session.refresh(concert)

    assert concert.is_sold_out is True


def test_is_sold_out_false_when_tickets_remain(db_session):
    """Tickets still available means not sold out."""
    venue = create_venues(db_session, count=1)[0]
    tour = _make_tour(db_session)
    concert = create_concert(
        db_session, tour, venue, day_offset=10, ticket_price="50.00",
        base_time=datetime.now(), tickets_sold=venue.capacity - 1,
    )

    assert concert.is_sold_out is False


def test_is_sold_out_false_when_inventory_unknown(db_session):
    """A venue with no known capacity means inventory is unknown, so the
    concert must never be reported as sold out."""
    venue = create_venues(db_session, count=1)[0]
    venue.capacity = None
    db_session.add(venue)
    db_session.commit()

    tour = _make_tour(db_session)
    concert = create_concert(
        db_session, tour, venue, day_offset=10, ticket_price="50.00",
        base_time=datetime.now(), tickets_sold=0,
    )

    assert concert.is_sold_out is False
