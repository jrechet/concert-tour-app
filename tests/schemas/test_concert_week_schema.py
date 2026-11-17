"""Unit tests for `ConcertWeekItem`, the read schema used by
`GET /api/v1/concerts/week`.

Concerts are seeded through real `Tour`/`Venue` foreign keys (via
`tests/fixtures/dashboard_fixtures.py`) rather than hardcoded ids, matching
the convention used by `tests/test_schemas_sold_out_concert.py`.
"""

from datetime import date, datetime

import pytest
from pydantic import ValidationError

from src.models import Concert, ConcertStatus
from src.schemas.concert import ConcertWeekItem
from tests.fixtures.dashboard_fixtures import create_concert, create_tour, create_venues


def _make_week_concert(db_session):
    venue = create_venues(db_session, count=1)[0]
    tour = create_tour(
        db_session,
        name="Neon Skyline World Tour",
        artist="Aurora Belle",
        start_date=date(2024, 1, 1),
        end_date=date(2024, 12, 31),
        status="active",
    )
    return create_concert(
        db_session, tour, venue, day_offset=0, ticket_price="75.00",
        base_time=datetime(2024, 6, 15, 20, 0),
    )


class TestConcertWeekItem:
    """Coverage for `ConcertWeekItem.model_validate`."""

    def test_happy_path_maps_orm_concert_with_venue(self, db_session):
        concert = _make_week_concert(db_session)

        item = ConcertWeekItem.model_validate(concert)

        assert item.id == concert.id
        assert item.title == concert.tour.name
        assert item.start_date == concert.date_time
        assert item.status == ConcertStatus.scheduled
        assert item.venue_name == concert.venue.name
        assert item.venue_city == concert.venue.city

    def test_start_date_serialises_as_iso_8601_datetime(self, db_session):
        concert = _make_week_concert(db_session)

        item = ConcertWeekItem.model_validate(concert)
        dumped = item.model_dump(mode="json")

        assert dumped["start_date"] == concert.date_time.isoformat()

    def test_venue_name_and_city_are_flattened_not_nested(self, db_session):
        concert = _make_week_concert(db_session)

        item = ConcertWeekItem.model_validate(concert)
        dumped = item.model_dump()

        assert dumped["venue_name"] == concert.venue.name
        assert dumped["venue_city"] == concert.venue.city
        assert "venue" not in dumped

    def test_rejects_concert_without_venue(self, db_session):
        tour = create_tour(
            db_session,
            name="Solo Acoustic Tour",
            artist="Aurora Belle",
            start_date=date(2024, 1, 1),
            end_date=date(2024, 12, 31),
            status="active",
        )
        concert = Concert(
            tour=tour, venue=None, date_time=datetime(2024, 6, 15, 20, 0),
            status=ConcertStatus.scheduled,
        )

        with pytest.raises(ValidationError):
            ConcertWeekItem.model_validate(concert)
