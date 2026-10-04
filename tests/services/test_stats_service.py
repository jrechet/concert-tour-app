"""Unit tests for `get_concerts_per_weekday` and `get_revenue_by_city`."""

from datetime import datetime

from src.services.stats_service import CityRevenue, get_concerts_per_weekday, get_revenue_by_city
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


class TestGetRevenueByCity:
    """Coverage for `get_revenue_by_city`."""

    def test_multiple_cities_sorted_by_revenue_descending(self, db_session):
        venues = create_venues(db_session, count=3)  # New York, London, Paris
        tour = create_tour(
            db_session, "Neon Skyline World Tour", "Aurora Belle",
            BASE_TIME.date(), BASE_TIME.date(), "active",
        )
        # New York: 100 * 50.00 = 5000 (highest)
        create_concert(
            db_session, tour, venues[0], day_offset=0, ticket_price="50.00",
            base_time=BASE_TIME, tickets_sold=100,
        )
        # London: 10 * 20.00 = 200 (lowest)
        create_concert(
            db_session, tour, venues[1], day_offset=1, ticket_price="20.00",
            base_time=BASE_TIME, tickets_sold=10,
        )
        # Paris: 50 * 30.00 = 1500 (middle)
        create_concert(
            db_session, tour, venues[2], day_offset=2, ticket_price="30.00",
            base_time=BASE_TIME, tickets_sold=50,
        )

        result = get_revenue_by_city(db_session)

        assert [entry.city_name for entry in result] == ["New York", "Paris", "London"]
        assert [entry.revenue for entry in result] == [5000.0, 1500.0, 200.0]

    def test_ties_broken_by_city_name_ascending(self, db_session):
        venues = create_venues(db_session, count=2)  # New York, London
        tour = create_tour(
            db_session, "Neon Skyline World Tour", "Aurora Belle",
            BASE_TIME.date(), BASE_TIME.date(), "active",
        )
        create_concert(
            db_session, tour, venues[0], day_offset=0, ticket_price="10.00",
            base_time=BASE_TIME, tickets_sold=100,
        )
        create_concert(
            db_session, tour, venues[1], day_offset=1, ticket_price="10.00",
            base_time=BASE_TIME, tickets_sold=100,
        )

        result = get_revenue_by_city(db_session)

        assert [entry.city_name for entry in result] == ["London", "New York"]
        assert [entry.revenue for entry in result] == [1000.0, 1000.0]

    def test_cancelled_concert_excluded_from_city_revenue(self, db_session):
        venues = create_venues(db_session, count=1)
        tour = create_tour(
            db_session, "Neon Skyline World Tour", "Aurora Belle",
            BASE_TIME.date(), BASE_TIME.date(), "active",
        )
        create_concert(
            db_session, tour, venues[0], day_offset=0, ticket_price="40.00",
            base_time=BASE_TIME, tickets_sold=20,
        )
        create_concert(
            db_session, tour, venues[0], day_offset=1, ticket_price="9999.00",
            base_time=BASE_TIME, tickets_sold=9999, is_cancelled=True,
            cancellation_reason="Artist illness",
        )

        result = get_revenue_by_city(db_session)

        assert len(result) == 1
        assert result[0].city_name == venues[0].city
        assert result[0].revenue == 800.0

    def test_concert_with_null_price_counted_as_zero_not_excluded(self, db_session):
        venues = create_venues(db_session, count=1)
        tour = create_tour(
            db_session, "Neon Skyline World Tour", "Aurora Belle",
            BASE_TIME.date(), BASE_TIME.date(), "active",
        )
        create_concert(
            db_session, tour, venues[0], day_offset=0, ticket_price=None,
            base_time=BASE_TIME, tickets_sold=500,
        )
        create_concert(
            db_session, tour, venues[0], day_offset=1, ticket_price="25.00",
            base_time=BASE_TIME, tickets_sold=10,
        )

        result = get_revenue_by_city(db_session)

        assert len(result) == 1
        assert result[0].city_name == venues[0].city
        assert result[0].revenue == 250.0

    def test_city_with_only_cancelled_concerts_is_omitted(self, db_session):
        venues = create_venues(db_session, count=1)
        tour = create_tour(
            db_session, "Neon Skyline World Tour", "Aurora Belle",
            BASE_TIME.date(), BASE_TIME.date(), "active",
        )
        create_concert(
            db_session, tour, venues[0], day_offset=0, ticket_price="100.00",
            base_time=BASE_TIME, tickets_sold=50, is_cancelled=True,
            cancellation_reason="Venue unavailable",
        )

        result = get_revenue_by_city(db_session)

        assert result == []

    def test_city_with_zero_tickets_sold_is_included_with_zero_revenue(self, db_session):
        venues = create_venues(db_session, count=1)
        tour = create_tour(
            db_session, "Neon Skyline World Tour", "Aurora Belle",
            BASE_TIME.date(), BASE_TIME.date(), "active",
        )
        create_concert(
            db_session, tour, venues[0], day_offset=0, ticket_price="100.00",
            base_time=BASE_TIME, tickets_sold=0,
        )

        result = get_revenue_by_city(db_session)

        assert len(result) == 1
        assert result[0].city_name == venues[0].city
        assert result[0].revenue == 0.0

    def test_result_items_are_city_revenue_instances(self, db_session):
        venues = create_venues(db_session, count=1)
        tour = create_tour(
            db_session, "Neon Skyline World Tour", "Aurora Belle",
            BASE_TIME.date(), BASE_TIME.date(), "active",
        )
        create_concert(
            db_session, tour, venues[0], day_offset=0, ticket_price="10.00",
            base_time=BASE_TIME, tickets_sold=1,
        )

        result = get_revenue_by_city(db_session)

        assert len(result) == 1
        assert isinstance(result[0], CityRevenue)
        assert result[0].city_id == venues[0].city
