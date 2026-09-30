"""Coverage for the nullable `Concert.notes` column and its exposure on
`ConcertResponse`.

Concerts are seeded through real `Tour`/`Venue` foreign keys (via
`tests/fixtures/dashboard_fixtures.py`) rather than hardcoded ids, matching
the convention used by `tests/test_concert_schema.py`.
"""

from datetime import datetime
from decimal import Decimal

from src.models import Concert
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


def _make_concert(db_session, notes=None):
    venue = create_venues(db_session, count=1)[0]
    tour = _make_tour(db_session)
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


def test_concert_created_without_notes_defaults_to_none(db_session):
    concert = _make_concert(db_session)

    assert concert.notes is None


def test_concert_created_without_notes_serializes_as_null(db_session):
    concert = _make_concert(db_session)

    response = ConcertResponse.model_validate(concert, from_attributes=True)

    assert response.notes is None
    assert response.model_dump()["notes"] is None


def test_concert_notes_round_trips_through_the_orm(db_session):
    concert = _make_concert(db_session, notes="VIP meet-and-greet before doors open")
    concert_id = concert.id
    db_session.expunge(concert)

    reloaded = db_session.query(Concert).filter_by(id=concert_id).one()

    assert reloaded.notes == "VIP meet-and-greet before doors open"


def test_concert_response_exposes_persisted_notes(db_session):
    concert = _make_concert(db_session, notes="Opening act TBD")

    response = ConcertResponse.model_validate(concert, from_attributes=True)

    assert response.notes == "Opening act TBD"


def test_notes_column_length_matches_the_migration():
    """The model's `String(500)` column must match the migration's
    `sa.String(length=500)` exactly, so a 500-char limit enforced by one is
    never silently different from the other.
    """
    column_length = Concert.__table__.columns["notes"].type.length

    assert column_length == 500
