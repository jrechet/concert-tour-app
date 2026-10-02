"""Unit tests for `get_concerts_between_dates`, independent of the HTTP layer."""

from datetime import datetime, timedelta

from src.services.concerts_service import get_concerts_between_dates
from tests.fixtures.dashboard_fixtures import create_concert, create_tour, create_venues

BASE_TIME = datetime(2024, 6, 15, 18, 0, 0)


class TestGetConcertsBetweenDates:
    """Coverage for `get_concerts_between_dates`."""

    def test_no_concerts_returns_empty_list(self, db_session):
        start = BASE_TIME.date()
        end = (BASE_TIME + timedelta(days=10)).date()

        assert get_concerts_between_dates(db_session, start, end) == []

    def test_concert_exactly_on_start_date_is_included(self, db_session):
        venues = create_venues(db_session, count=1)
        tour = create_tour(
            db_session, "Start Date Tour", "Test Artist",
            (BASE_TIME - timedelta(days=5)).date(),
            (BASE_TIME + timedelta(days=5)).date(),
            "active",
        )
        start_concert = create_concert(
            db_session, tour, venues[0], day_offset=0, ticket_price="80.00", base_time=BASE_TIME
        )
        start = BASE_TIME.date()
        end = (BASE_TIME + timedelta(days=5)).date()

        results = get_concerts_between_dates(db_session, start, end)

        assert [c.id for c in results] == [start_concert.id]

    def test_concert_exactly_on_end_date_is_included(self, db_session):
        venues = create_venues(db_session, count=1)
        tour = create_tour(
            db_session, "End Date Tour", "Test Artist",
            (BASE_TIME - timedelta(days=5)).date(),
            (BASE_TIME + timedelta(days=5)).date(),
            "active",
        )
        end_concert = create_concert(
            db_session, tour, venues[0], day_offset=5, ticket_price="80.00", base_time=BASE_TIME
        )
        start = BASE_TIME.date()
        end = (BASE_TIME + timedelta(days=5)).date()

        results = get_concerts_between_dates(db_session, start, end)

        assert [c.id for c in results] == [end_concert.id]

    def test_concerts_outside_range_are_excluded(self, db_session):
        venues = create_venues(db_session, count=2)
        tour = create_tour(
            db_session, "Out Of Range Tour", "Test Artist",
            (BASE_TIME - timedelta(days=30)).date(),
            (BASE_TIME + timedelta(days=30)).date(),
            "active",
        )
        create_concert(db_session, tour, venues[0], day_offset=-10, ticket_price="80.00", base_time=BASE_TIME)
        create_concert(db_session, tour, venues[1], day_offset=20, ticket_price="80.00", base_time=BASE_TIME)
        start = BASE_TIME.date()
        end = (BASE_TIME + timedelta(days=5)).date()

        results = get_concerts_between_dates(db_session, start, end)

        assert results == []

    def test_results_are_ordered_ascending_by_date(self, db_session):
        venues = create_venues(db_session, count=3)
        tour = create_tour(
            db_session, "Scramble Tour", "Test Artist",
            (BASE_TIME - timedelta(days=5)).date(),
            (BASE_TIME + timedelta(days=10)).date(),
            "active",
        )
        # Inserted deliberately out of chronological order.
        later = create_concert(db_session, tour, venues[0], day_offset=8, ticket_price="80.00", base_time=BASE_TIME)
        earliest = create_concert(db_session, tour, venues[1], day_offset=1, ticket_price="80.00", base_time=BASE_TIME)
        middle = create_concert(db_session, tour, venues[2], day_offset=4, ticket_price="80.00", base_time=BASE_TIME)
        start = BASE_TIME.date()
        end = (BASE_TIME + timedelta(days=10)).date()

        results = get_concerts_between_dates(db_session, start, end)

        assert [c.id for c in results] == [earliest.id, middle.id, later.id]
