"""Unit tests for `get_next_concert`, independent of the HTTP layer.

`reference_time` is passed explicitly to a fixed moment so "soonest
upcoming" assertions don't depend on the real wall clock, mirroring
`tests/test_concerts_service_upcoming.py`.
"""

from datetime import datetime, timedelta

from src.services.concerts_service import get_next_concert
from tests.fixtures.dashboard_fixtures import create_concert, create_tour, create_venues

REFERENCE_TIME = datetime(2024, 6, 15, 18, 0, 0)


class TestGetNextConcert:
    """Coverage for `get_next_concert`."""

    def test_no_concerts_returns_none(self, db_session):
        assert get_next_concert(db_session, REFERENCE_TIME) is None

    def test_all_past_concerts_returns_none(self, db_session):
        venues = create_venues(db_session, count=2)
        tour = create_tour(
            db_session, "Farewell Tour", "Test Artist",
            (REFERENCE_TIME - timedelta(days=60)).date(),
            (REFERENCE_TIME - timedelta(days=1)).date(),
            "completed",
        )
        create_concert(db_session, tour, venues[0], day_offset=-1, ticket_price="80.00", base_time=REFERENCE_TIME)
        create_concert(db_session, tour, venues[1], day_offset=-30, ticket_price="80.00", base_time=REFERENCE_TIME)

        assert get_next_concert(db_session, REFERENCE_TIME) is None

    def test_all_cancelled_concerts_returns_none(self, db_session):
        venues = create_venues(db_session, count=2)
        tour = create_tour(
            db_session, "Cancelled Tour", "Test Artist",
            REFERENCE_TIME.date(),
            (REFERENCE_TIME + timedelta(days=30)).date(),
            "active",
        )
        create_concert(
            db_session, tour, venues[0], day_offset=1, ticket_price="80.00", base_time=REFERENCE_TIME,
            is_cancelled=True, cancellation_reason="Venue closed",
        )
        create_concert(
            db_session, tour, venues[1], day_offset=5, ticket_price="80.00", base_time=REFERENCE_TIME,
            is_cancelled=True, cancellation_reason="Artist illness",
        )

        assert get_next_concert(db_session, REFERENCE_TIME) is None

    def test_returns_soonest_future_non_cancelled_concert(self, db_session):
        venues = create_venues(db_session, count=3)
        tour = create_tour(
            db_session, "Scramble Tour", "Test Artist",
            (REFERENCE_TIME - timedelta(days=30)).date(),
            (REFERENCE_TIME + timedelta(days=30)).date(),
            "active",
        )
        # Inserted deliberately out of chronological order, with a
        # cancelled show that would otherwise be soonest.
        later = create_concert(db_session, tour, venues[0], day_offset=20, ticket_price="80.00", base_time=REFERENCE_TIME)
        create_concert(db_session, tour, venues[1], day_offset=-10, ticket_price="80.00", base_time=REFERENCE_TIME)
        create_concert(
            db_session, tour, venues[2], day_offset=1, ticket_price="80.00", base_time=REFERENCE_TIME,
            is_cancelled=True, cancellation_reason="Weather",
        )
        soonest = create_concert(db_session, tour, venues[0], day_offset=5, ticket_price="80.00", base_time=REFERENCE_TIME)

        result = get_next_concert(db_session, REFERENCE_TIME)

        assert result is not None
        assert result.id == soonest.id
        assert later.id != result.id

    def test_venue_is_eagerly_loaded(self, db_session):
        venues = create_venues(db_session, count=1)
        tour = create_tour(
            db_session, "Loaded Tour", "Test Artist",
            REFERENCE_TIME.date(),
            (REFERENCE_TIME + timedelta(days=10)).date(),
            "active",
        )
        create_concert(db_session, tour, venues[0], day_offset=1, ticket_price="80.00", base_time=REFERENCE_TIME)

        result = get_next_concert(db_session, REFERENCE_TIME)

        assert result is not None
        assert result.venue.name == venues[0].name
        assert result.venue.city == venues[0].city
        assert result.venue.country == venues[0].country

    def test_concert_at_exact_reference_time_is_included(self, db_session):
        venues = create_venues(db_session, count=1)
        tour = create_tour(
            db_session, "Exact Time Tour", "Test Artist",
            (REFERENCE_TIME - timedelta(days=5)).date(),
            (REFERENCE_TIME + timedelta(days=5)).date(),
            "active",
        )
        concert = create_concert(
            db_session, tour, venues[0], day_offset=0, ticket_price="80.00", base_time=REFERENCE_TIME,
        )

        result = get_next_concert(db_session, REFERENCE_TIME)

        assert result is not None
        assert result.id == concert.id

    def test_defaults_to_the_app_reference_time_when_omitted(self, db_session, monkeypatch):
        venues = create_venues(db_session, count=1)
        tour = create_tour(
            db_session, "Default Time Tour", "Test Artist",
            (REFERENCE_TIME - timedelta(days=5)).date(),
            (REFERENCE_TIME + timedelta(days=5)).date(),
            "active",
        )
        upcoming_concert = create_concert(
            db_session, tour, venues[0], day_offset=1, ticket_price="80.00", base_time=REFERENCE_TIME
        )
        monkeypatch.setattr(
            "src.services.concerts_service.get_reference_time", lambda: REFERENCE_TIME
        )

        result = get_next_concert(db_session)

        assert result is not None
        assert result.id == upcoming_concert.id
