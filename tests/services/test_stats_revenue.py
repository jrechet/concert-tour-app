"""Unit tests for `get_revenue_by_month`."""

from datetime import datetime

from src.services.stats import get_revenue_by_month
from tests.fixtures.dashboard_fixtures import create_concert, create_tour, create_venues

BASE_TIME = datetime(2026, 1, 15, 20, 0, 0)


def _make_tour(db_session):
    return create_tour(
        db_session, "Neon Skyline World Tour", "Aurora Belle",
        BASE_TIME.date(), BASE_TIME.date(), "active",
    )


class TestGetRevenueByMonth:
    """Coverage for `get_revenue_by_month`."""

    def test_returns_empty_list_when_no_concerts(self, db_session):
        result = get_revenue_by_month(db_session)

        assert result == []

    def test_groups_concerts_of_same_month(self, db_session):
        venues = create_venues(db_session, count=2)
        tour = _make_tour(db_session)
        create_concert(
            db_session, tour, venues[0], day_offset=0, ticket_price="80.00",
            base_time=BASE_TIME, tickets_sold=100,
        )
        create_concert(
            db_session, tour, venues[1], day_offset=5, ticket_price="50.00",
            base_time=BASE_TIME, tickets_sold=40,
        )

        result = get_revenue_by_month(db_session)

        assert len(result) == 1
        assert result[0].month == "2026-01"
        assert result[0].tickets_sold == 140
        assert result[0].revenue == 100 * 80.0 + 40 * 50.0

    def test_excludes_cancelled_concerts(self, db_session):
        venues = create_venues(db_session, count=2)
        tour = _make_tour(db_session)
        create_concert(
            db_session, tour, venues[0], day_offset=0, ticket_price="80.00",
            base_time=BASE_TIME, tickets_sold=100,
        )
        create_concert(
            db_session, tour, venues[1], day_offset=5, ticket_price="200.00",
            base_time=BASE_TIME, tickets_sold=999,
            is_cancelled=True, cancellation_reason="Venue closed",
        )

        result = get_revenue_by_month(db_session)

        assert len(result) == 1
        assert result[0].month == "2026-01"
        assert result[0].tickets_sold == 100
        assert result[0].revenue == 100 * 80.0

    def test_excludes_cancelled_concerts_omits_month_when_all_cancelled(self, db_session):
        venues = create_venues(db_session, count=1)
        tour = _make_tour(db_session)
        create_concert(
            db_session, tour, venues[0], day_offset=0, ticket_price="80.00",
            base_time=BASE_TIME, tickets_sold=100,
            is_cancelled=True, cancellation_reason="Artist illness",
        )

        result = get_revenue_by_month(db_session)

        assert result == []

    def test_concert_without_price_counts_as_zero_revenue(self, db_session):
        venues = create_venues(db_session, count=1)
        tour = _make_tour(db_session)
        create_concert(
            db_session, tour, venues[0], day_offset=0, ticket_price=None,
            base_time=BASE_TIME, tickets_sold=75,
        )

        result = get_revenue_by_month(db_session)

        assert len(result) == 1
        assert result[0].tickets_sold == 75
        assert result[0].revenue == 0

    def test_months_returned_in_chronological_order(self, db_session):
        venues = create_venues(db_session, count=3)
        tour = _make_tour(db_session)
        create_concert(
            db_session, tour, venues[0], day_offset=0, ticket_price="80.00",
            base_time=datetime(2026, 11, 1), tickets_sold=10,
        )
        create_concert(
            db_session, tour, venues[1], day_offset=0, ticket_price="80.00",
            base_time=datetime(2026, 1, 1), tickets_sold=10,
        )
        create_concert(
            db_session, tour, venues[2], day_offset=0, ticket_price="80.00",
            base_time=datetime(2026, 2, 1), tickets_sold=10,
        )

        result = get_revenue_by_month(db_session)

        assert [row.month for row in result] == ["2026-01", "2026-02", "2026-11"]

    def test_month_is_zero_padded(self, db_session):
        venues = create_venues(db_session, count=1)
        tour = _make_tour(db_session)
        create_concert(
            db_session, tour, venues[0], day_offset=0, ticket_price="80.00",
            base_time=datetime(2026, 3, 10), tickets_sold=10,
        )

        result = get_revenue_by_month(db_session)

        assert result[0].month == "2026-03"
