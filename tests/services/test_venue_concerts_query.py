"""Unit tests for `list_venue_concerts` and `get_venue_or_none`."""

from datetime import datetime, timedelta

from src.models import Venue
from src.services.venue_service import get_venue_or_none, list_venue_concerts
from tests.fixtures.dashboard_fixtures import create_concert, create_tour, create_venues

REFERENCE_TIME = datetime(2026, 6, 1, 12, 0, 0)


def _make_tour(db_session):
    """Persist and return a `Tour` row spanning `REFERENCE_TIME`."""
    return create_tour(
        db_session, "Reunion Tour", "Test Artist",
        (REFERENCE_TIME - timedelta(days=60)).date(),
        (REFERENCE_TIME + timedelta(days=60)).date(),
        "active",
    )


class TestListVenueConcerts:
    """Coverage for `list_venue_concerts`."""

    def test_returns_concerts_soonest_first(self, db_session):
        venue = create_venues(db_session, count=1)[0]
        tour = _make_tour(db_session)

        later_concert = create_concert(
            db_session, tour, venue, day_offset=30, ticket_price="50.00", base_time=REFERENCE_TIME,
        )
        soonest_concert = create_concert(
            db_session, tour, venue, day_offset=5, ticket_price="50.00", base_time=REFERENCE_TIME,
        )
        middle_concert = create_concert(
            db_session, tour, venue, day_offset=10, ticket_price="50.00", base_time=REFERENCE_TIME,
        )

        result = list_venue_concerts(db_session, venue.id)

        assert [concert.id for concert in result] == [
            soonest_concert.id, middle_concert.id, later_concert.id,
        ]

    def test_excludes_cancelled_concerts(self, db_session):
        venue = create_venues(db_session, count=1)[0]
        tour = _make_tour(db_session)

        cancelled_concert = create_concert(
            db_session, tour, venue, day_offset=5, ticket_price="50.00", base_time=REFERENCE_TIME,
            is_cancelled=True, cancellation_reason="Artist illness",
        )
        active_concert = create_concert(
            db_session, tour, venue, day_offset=10, ticket_price="50.00", base_time=REFERENCE_TIME,
        )

        result = list_venue_concerts(db_session, venue.id)

        returned_ids = [concert.id for concert in result]
        assert returned_ids == [active_concert.id]
        assert cancelled_concert.id not in returned_ids

    def test_excludes_concerts_of_other_venues(self, db_session):
        venue, other_venue = create_venues(db_session, count=2)
        tour = _make_tour(db_session)

        own_concert = create_concert(
            db_session, tour, venue, day_offset=10, ticket_price="50.00", base_time=REFERENCE_TIME,
        )
        other_venue_concert = create_concert(
            db_session, tour, other_venue, day_offset=5, ticket_price="50.00", base_time=REFERENCE_TIME,
        )

        result = list_venue_concerts(db_session, venue.id)

        returned_ids = [concert.id for concert in result]
        assert returned_ids == [own_concert.id]
        assert other_venue_concert.id not in returned_ids

    def test_returns_empty_list_for_venue_with_no_concerts(self, db_session):
        venue = create_venues(db_session, count=1)[0]

        result = list_venue_concerts(db_session, venue.id)

        assert result == []


class TestGetVenueOrNone:
    """Coverage for `get_venue_or_none`."""

    def test_returns_venue_when_it_exists(self, db_session):
        venue = create_venues(db_session, count=1)[0]

        result = get_venue_or_none(db_session, venue.id)

        assert result is not None
        assert result.id == venue.id

    def test_returns_none_for_unknown_venue_id(self, db_session):
        venue = create_venues(db_session, count=1)[0]
        unknown_venue_id = venue.id + 1

        while db_session.query(Venue).filter(Venue.id == unknown_venue_id).first() is not None:
            unknown_venue_id += 1

        result = get_venue_or_none(db_session, unknown_venue_id)

        assert result is None
