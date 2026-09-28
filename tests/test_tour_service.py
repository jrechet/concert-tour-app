"""Unit tests for `get_tour_revenue`, independent of the HTTP layer."""

from datetime import datetime
from decimal import Decimal

from src.services.tour_service import get_tour_revenue
from tests.fixtures.dashboard_fixtures import create_concert, create_tour, create_venues

BASE_TIME = datetime(2024, 6, 15, 20, 0, 0)


class TestGetTourRevenue:
    """Coverage for `get_tour_revenue`."""

    def test_mixed_cancelled_and_active_concerts_excludes_cancelled(self, db_session):
        venues = create_venues(db_session, count=2)
        tour = create_tour(
            db_session, "Neon Skyline World Tour", "Aurora Belle",
            BASE_TIME.date(), BASE_TIME.date(), "active",
        )
        create_concert(
            db_session, tour, venues[0], day_offset=0, ticket_price="80.00",
            base_time=BASE_TIME, tickets_sold=100,
        )
        create_concert(
            db_session, tour, venues[1], day_offset=1, ticket_price="120.00",
            base_time=BASE_TIME, tickets_sold=50,
        )
        create_concert(
            db_session, tour, venues[0], day_offset=2, ticket_price="999.00",
            base_time=BASE_TIME, tickets_sold=200,
            is_cancelled=True, cancellation_reason="Artist illness",
        )

        result = get_tour_revenue(db_session, tour.id)

        assert result.revenue == Decimal("80.00") * 100 + Decimal("120.00") * 50
        assert result.concert_count == 2

    def test_tour_with_zero_concerts_returns_zero_revenue_and_count(self, db_session):
        tour = create_tour(
            db_session, "Unannounced Tour", "TBD Collective",
            BASE_TIME.date(), BASE_TIME.date(), "planned",
        )

        result = get_tour_revenue(db_session, tour.id)

        assert result.revenue == Decimal("0")
        assert result.concert_count == 0

    def test_unknown_tour_id_returns_none(self, db_session):
        assert get_tour_revenue(db_session, 999999) is None
