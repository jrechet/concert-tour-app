"""Unit tests for `ConcertNotesUpdate` and the `notes` field on
`ConcertResponse`, covering the length boundary enforced by
`MAX_NOTES_LENGTH`.

Concerts are seeded through real `Tour`/`Venue` foreign keys (via
`tests/fixtures/dashboard_fixtures.py`) rather than a hardcoded
`venue_id=1`, matching the convention used by `tests/test_concert_schema.py`.
"""

from datetime import datetime
from decimal import Decimal

import pytest
from pydantic import ValidationError

from src.models import Concert
from src.schemas.concert import MAX_NOTES_LENGTH, ConcertNotesUpdate, ConcertResponse
from tests.fixtures.dashboard_fixtures import create_tour, create_venues

REFERENCE_TIME = datetime(2024, 6, 15, 9, 0, 0)


def _make_concert(db_session):
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
        tour_id=tour.id, venue_id=venue.id, date_time=REFERENCE_TIME, ticket_price=Decimal("50.00"),
    )
    db_session.add(concert)
    db_session.commit()
    db_session.refresh(concert)
    return concert


def test_concert_notes_update_accepts_exactly_max_notes_length():
    payload = ConcertNotesUpdate(notes="x" * MAX_NOTES_LENGTH)

    assert len(payload.notes) == MAX_NOTES_LENGTH


def test_concert_notes_update_rejects_notes_over_max_notes_length():
    with pytest.raises(ValidationError):
        ConcertNotesUpdate(notes="x" * (MAX_NOTES_LENGTH + 1))


def test_concert_notes_update_accepts_empty_string_since_no_min_length_is_enforced():
    """`notes` is required (`...`) but has no `min_length`, so an empty
    string is a valid way to explicitly clear/represent "no notes" via the
    update endpoint, distinct from omitting the field entirely.
    """
    payload = ConcertNotesUpdate(notes="")

    assert payload.notes == ""


def test_concert_notes_update_requires_the_notes_field():
    with pytest.raises(ValidationError):
        ConcertNotesUpdate()


def test_concert_response_dumps_notes_as_null_when_unset(db_session):
    concert = _make_concert(db_session)

    response = ConcertResponse.model_validate(concert, from_attributes=True)

    assert response.model_dump()["notes"] is None
