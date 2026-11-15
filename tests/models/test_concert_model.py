"""Coverage for the `Concert.status` column (`ConcertStatus`) and its
exposure on `ConcertResponse`.

Concerts are seeded through real `Tour`/`Venue` foreign keys (via
`tests/fixtures/dashboard_fixtures.py`) rather than hardcoded ids, matching
the convention used by `tests/test_concert_notes.py`.
"""

from datetime import datetime
from decimal import Decimal

import pytest

from src.models import Concert
from src.models.concert import ConcertStatus
from src.schemas.concert import ConcertResponse
from tests.fixtures.dashboard_fixtures import create_tour, create_venues

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


def _make_concert(db_session, **kwargs):
    venue = create_venues(db_session, count=1)[0]
    tour = _make_tour(db_session)
    concert = Concert(
        tour_id=tour.id,
        venue_id=venue.id,
        date_time=REFERENCE_TIME,
        ticket_price=Decimal("50.00"),
        **kwargs,
    )
    db_session.add(concert)
    db_session.commit()
    db_session.refresh(concert)
    return concert


def test_default_status_is_scheduled(db_session):
    concert = _make_concert(db_session)

    assert concert.status is ConcertStatus.scheduled


def test_status_can_be_set_to_cancelled_and_round_trips_through_the_session(db_session):
    concert = _make_concert(db_session, status=ConcertStatus.cancelled)

    db_session.expire_all()
    persisted = db_session.query(Concert).filter(Concert.id == concert.id).first()

    assert persisted.status is ConcertStatus.cancelled


def test_unknown_status_string_raises():
    concert = Concert()

    with pytest.raises(ValueError):
        concert.status = "bogus"


def test_read_schema_serialises_status_as_lowercase_string(db_session):
    concert = _make_concert(db_session, status=ConcertStatus.cancelled)

    response = ConcertResponse.model_validate(concert, from_attributes=True)

    assert response.model_dump()["status"] == "cancelled"
