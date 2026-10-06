"""Unit tests for `get_venue_with_upcoming_concerts`.

Concerts are created with `day_offset`s relative to the real wall clock
(`datetime.now()`), mirroring `tests/services/test_venue_service.py`'s use
of real FK-backed fixtures, since `get_venue_with_upcoming_concerts` takes
no `reference_time` override and always compares against
`get_reference_time()`.
"""

from datetime import datetime, timedelta

from src.crud.venue import get_venue_with_upcoming_concerts
from tests.fixtures.dashboard_fixtures import create_concert, create_tour, create_venues

NOW = datetime.now()


class TestGetVenueWithUpcomingConcerts:
    """Coverage for `get_venue_with_upcoming_concerts`."""

    def test_unknown_venue_id_returns_none(self, db_session):
        assert get_venue_with_upcoming_concerts(db_session, 99999) is None

    def test_venue_with_no_concerts_returns_venue_with_empty_list(self, db_session):
        venue = create_venues(db_session, count=1)[0]

        result = get_venue_with_upcoming_concerts(db_session, venue.id)

        assert result is not None
        assert result.id == venue.id
        assert result.concerts == []

    def test_filters_past_and_cancelled_and_orders_soonest_first(self, db_session):
        venue = create_venues(db_session, count=1)[0]
        tour = create_tour(
            db_session, "Reunion Tour", "Test Artist",
            (NOW - timedelta(days=60)).date(),
            (NOW + timedelta(days=60)).date(),
            "active",
        )

        past_concert = create_concert(
            db_session, tour, venue, day_offset=-10, ticket_price="50.00", base_time=NOW,
        )
        cancelled_future_concert = create_concert(
            db_session, tour, venue, day_offset=5, ticket_price="50.00", base_time=NOW,
            is_cancelled=True, cancellation_reason="Artist illness",
        )
        soonest_future_concert = create_concert(
            db_session, tour, venue, day_offset=10, ticket_price="50.00", base_time=NOW,
        )
        later_future_concert = create_concert(
            db_session, tour, venue, day_offset=30, ticket_price="50.00", base_time=NOW,
        )

        result = get_venue_with_upcoming_concerts(db_session, venue.id)

        assert result is not None
        assert [concert.id for concert in result.concerts] == [
            soonest_future_concert.id, later_future_concert.id,
        ]
        returned_ids = {concert.id for concert in result.concerts}
        assert past_concert.id not in returned_ids
        assert cancelled_future_concert.id not in returned_ids
