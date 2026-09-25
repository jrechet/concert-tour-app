"""Unit tests for `get_upcoming_concerts`, independent of the HTTP layer.

`reference_time` is passed explicitly to a fixed moment so "upcoming vs.
past" assertions don't depend on the real wall clock, mirroring
`tests/test_concerts_upcoming.py`.
"""

from datetime import datetime, timedelta

from src.services.concerts_service import get_upcoming_concerts
from tests.fixtures.dashboard_fixtures import create_concert, create_tour, create_venues

REFERENCE_TIME = datetime(2024, 6, 15, 18, 0, 0)


class TestGetUpcomingConcerts:
    """Coverage for `get_upcoming_concerts`."""

    def test_no_concerts_returns_empty_list(self, db_session):
        assert get_upcoming_concerts(db_session, REFERENCE_TIME) == []

    def test_past_concerts_are_excluded(self, db_session):
        venues = create_venues(db_session, count=2)
        tour = create_tour(
            db_session, "Farewell Tour", "Test Artist",
            (REFERENCE_TIME - timedelta(days=60)).date(),
            (REFERENCE_TIME + timedelta(days=1)).date(),
            "active",
        )
        past_concert = create_concert(
            db_session, tour, venues[0], day_offset=-1, ticket_price="80.00", base_time=REFERENCE_TIME
        )
        create_concert(db_session, tour, venues[1], day_offset=-30, ticket_price="80.00", base_time=REFERENCE_TIME)

        results = get_upcoming_concerts(db_session, REFERENCE_TIME)

        assert results == []
        assert past_concert.id not in [c.id for c in results]

    def test_concert_dated_exactly_today_is_included(self, db_session):
        venues = create_venues(db_session, count=1)
        tour = create_tour(
            db_session, "Today Tour", "Test Artist",
            (REFERENCE_TIME - timedelta(days=5)).date(),
            (REFERENCE_TIME + timedelta(days=5)).date(),
            "active",
        )
        today_concert = create_concert(
            db_session, tour, venues[0], day_offset=0, ticket_price="80.00",
            base_time=REFERENCE_TIME.replace(hour=9, minute=0),
        )

        results = get_upcoming_concerts(db_session, REFERENCE_TIME)

        assert [c.id for c in results] == [today_concert.id]

    def test_mixed_past_and_future_are_ordered_soonest_first(self, db_session):
        venues = create_venues(db_session, count=3)
        tour = create_tour(
            db_session, "Scramble Tour", "Test Artist",
            (REFERENCE_TIME - timedelta(days=30)).date(),
            (REFERENCE_TIME + timedelta(days=30)).date(),
            "active",
        )
        # Inserted deliberately out of chronological order.
        later = create_concert(db_session, tour, venues[0], day_offset=20, ticket_price="80.00", base_time=REFERENCE_TIME)
        create_concert(db_session, tour, venues[1], day_offset=-10, ticket_price="80.00", base_time=REFERENCE_TIME)
        soonest = create_concert(db_session, tour, venues[2], day_offset=1, ticket_price="80.00", base_time=REFERENCE_TIME)

        results = get_upcoming_concerts(db_session, REFERENCE_TIME)

        assert [c.id for c in results] == [soonest.id, later.id]

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

        results = get_upcoming_concerts(db_session)

        assert [c.id for c in results] == [upcoming_concert.id]
