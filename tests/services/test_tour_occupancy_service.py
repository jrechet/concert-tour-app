"""Unit tests for `get_tour_occupancy`, independent of the HTTP layer."""

from datetime import datetime

from src.schemas.tour import OCCUPANCY_PERCENTAGE_PRECISION, TourOccupancySchema
from src.services.tour_service import get_tour_occupancy
from tests.fixtures.dashboard_fixtures import create_concert, create_tour, create_venues

BASE_TIME = datetime(2024, 6, 15, 20, 0, 0)


class TestGetTourOccupancy:
    """Coverage for `get_tour_occupancy`."""

    def test_multiple_non_cancelled_concerts_aggregate_correctly(self, db_session):
        venues = create_venues(db_session, count=2)
        tour = create_tour(
            db_session, "Neon Skyline World Tour", "Aurora Belle",
            BASE_TIME.date(), BASE_TIME.date(), "active",
        )
        create_concert(
            db_session, tour, venues[0], day_offset=0, ticket_price="80.00",
            base_time=BASE_TIME, tickets_sold=15000,
        )
        create_concert(
            db_session, tour, venues[1], day_offset=1, ticket_price="120.00",
            base_time=BASE_TIME, tickets_sold=9000,
        )

        result = get_tour_occupancy(db_session, tour.id)

        assert isinstance(result, TourOccupancySchema)
        assert result.tour_id == tour.id
        assert result.tickets_sold == 15000 + 9000
        assert result.total_capacity == venues[0].capacity + venues[1].capacity
        expected_percentage = round(
            (15000 + 9000) / (venues[0].capacity + venues[1].capacity) * 100,
            OCCUPANCY_PERCENTAGE_PRECISION,
        )
        assert result.percentage_sold == expected_percentage

    def test_cancelled_concert_excluded_from_sums_and_percentage(self, db_session):
        venues = create_venues(db_session, count=2)
        tour = create_tour(
            db_session, "Neon Skyline World Tour", "Aurora Belle",
            BASE_TIME.date(), BASE_TIME.date(), "active",
        )
        create_concert(
            db_session, tour, venues[0], day_offset=0, ticket_price="80.00",
            base_time=BASE_TIME, tickets_sold=15000,
        )
        create_concert(
            db_session, tour, venues[1], day_offset=1, ticket_price="120.00",
            base_time=BASE_TIME, tickets_sold=9000,
            is_cancelled=True, cancellation_reason="Artist illness",
        )

        result = get_tour_occupancy(db_session, tour.id)

        assert result.tickets_sold == 15000
        assert result.total_capacity == venues[0].capacity
        assert result.percentage_sold == round(
            15000 / venues[0].capacity * 100, OCCUPANCY_PERCENTAGE_PRECISION
        )

    def test_only_cancelled_concert_returns_zeros(self, db_session):
        venues = create_venues(db_session, count=1)
        tour = create_tour(
            db_session, "Grounded Tour", "Vela Ashford",
            BASE_TIME.date(), BASE_TIME.date(), "cancelled",
        )
        create_concert(
            db_session, tour, venues[0], day_offset=0, ticket_price="80.00",
            base_time=BASE_TIME, tickets_sold=5000,
            is_cancelled=True, cancellation_reason="Artist illness",
        )

        result = get_tour_occupancy(db_session, tour.id)

        assert result.tickets_sold == 0
        assert result.total_capacity == 0
        assert result.percentage_sold == 0.0

    def test_tour_with_no_concerts_returns_zeros_not_none(self, db_session):
        tour = create_tour(
            db_session, "Unannounced Tour", "TBD Collective",
            BASE_TIME.date(), BASE_TIME.date(), "planned",
        )

        result = get_tour_occupancy(db_session, tour.id)

        assert result is not None
        assert result.tickets_sold == 0
        assert result.total_capacity == 0
        assert result.percentage_sold == 0.0

    def test_unknown_tour_id_returns_none(self, db_session):
        assert get_tour_occupancy(db_session, 999999) is None

    def test_percentage_rounded_to_configured_precision(self, db_session):
        venues = create_venues(db_session, count=1)
        tour = create_tour(
            db_session, "Fractional Sales Tour", "Vela Ashford",
            BASE_TIME.date(), BASE_TIME.date(), "active",
        )
        venue = venues[0]
        venue.capacity = 3
        db_session.commit()
        create_concert(
            db_session, tour, venue, day_offset=0, ticket_price="80.00",
            base_time=BASE_TIME, tickets_sold=1,
        )

        result = get_tour_occupancy(db_session, tour.id)

        assert result.tickets_sold == 1
        assert result.total_capacity == 3
        assert result.percentage_sold == round(1 / 3 * 100, OCCUPANCY_PERCENTAGE_PRECISION)
        assert result.percentage_sold == 33.33
