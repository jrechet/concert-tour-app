"""Unit tests for `get_concerts_per_weekday`."""

from datetime import datetime

from src.services.stats_service import get_concerts_per_weekday
from tests.fixtures.dashboard_fixtures import create_concert, create_tour, create_venues

BASE_TIME = datetime(2024, 6, 17, 20, 0, 0)  # a Monday
WEEKDAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


class TestGetConcertsPerWeekday:
    """Coverage for `get_concerts_per_weekday`."""

    def test_monday_and_wednesday_concerts_counted_correctly(self, db_session):
        venues = create_venues(db_session, count=2)
        tour = create_tour(
            db_session, "Neon Skyline World Tour", "Aurora Belle",
            BASE_TIME.date(), BASE_TIME.date(), "active",
        )
        create_concert(
            db_session, tour, venues[0], day_offset=0, ticket_price="80.00",
            base_time=BASE_TIME,
        )
        create_concert(
            db_session, tour, venues[1], day_offset=2, ticket_price="90.00",
            base_time=BASE_TIME,
        )

        result = get_concerts_per_weekday(db_session)

        assert result["Monday"] == 1
        assert result["Wednesday"] == 1

    def test_cancelled_friday_concert_excluded(self, db_session):
        venues = create_venues(db_session, count=1)
        tour = create_tour(
            db_session, "Neon Skyline World Tour", "Aurora Belle",
            BASE_TIME.date(), BASE_TIME.date(), "active",
        )
        create_concert(
            db_session, tour, venues[0], day_offset=4, ticket_price="80.00",
            base_time=BASE_TIME, is_cancelled=True, cancellation_reason="Artist illness",
        )

        result = get_concerts_per_weekday(db_session)

        assert result["Friday"] == 0

    def test_days_with_no_concerts_are_zero(self, db_session):
        venues = create_venues(db_session, count=1)
        tour = create_tour(
            db_session, "Neon Skyline World Tour", "Aurora Belle",
            BASE_TIME.date(), BASE_TIME.date(), "active",
        )
        create_concert(
            db_session, tour, venues[0], day_offset=0, ticket_price="80.00",
            base_time=BASE_TIME,
        )

        result = get_concerts_per_weekday(db_session)

        assert result["Tuesday"] == 0
        assert result["Thursday"] == 0
        assert result["Saturday"] == 0
        assert result["Sunday"] == 0

    def test_result_has_exactly_seven_weekday_keys_in_order(self, db_session):
        result = get_concerts_per_weekday(db_session)

        assert list(result.keys()) == WEEKDAYS
