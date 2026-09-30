"""Unit tests for `get_tour_occupancy`, independent of the HTTP layer."""

from datetime import datetime

import pytest

from src.models import Venue
from src.services.occupancy import TourNotFoundError, get_tour_occupancy
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

        assert result.tickets_sold == 15000 + 9000
        assert result.total_capacity == venues[0].capacity + venues[1].capacity
        expected_percentage = round((15000 + 9000) / (venues[0].capacity + venues[1].capacity) * 100, 2)
        assert result.percentage_sold == expected_percentage

    def test_cancelled_concert_excluded(self, db_session):
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
        assert result.percentage_sold == round(15000 / venues[0].capacity * 100, 2)

    def test_unknown_tour_id_raises_tour_not_found_error(self, db_session):
        with pytest.raises(TourNotFoundError):
            get_tour_occupancy(db_session, 999999)

    def test_zero_total_capacity_returns_zero_percentage(self, db_session):
        zero_capacity_venue = Venue(name="Pop-Up Stage", city="Berlin", country="Germany", capacity=0)
        db_session.add(zero_capacity_venue)
        db_session.commit()
        db_session.refresh(zero_capacity_venue)

        tour = create_tour(
            db_session, "Unannounced Tour", "TBD Collective",
            BASE_TIME.date(), BASE_TIME.date(), "planned",
        )
        create_concert(
            db_session, tour, zero_capacity_venue, day_offset=0, ticket_price="80.00",
            base_time=BASE_TIME, tickets_sold=0,
        )

        result = get_tour_occupancy(db_session, tour.id)

        assert result.tickets_sold == 0
        assert result.total_capacity == 0
        assert result.percentage_sold == 0.0

    def test_tour_with_no_concerts_returns_zero_percentage(self, db_session):
        tour = create_tour(
            db_session, "Unannounced Tour", "TBD Collective",
            BASE_TIME.date(), BASE_TIME.date(), "planned",
        )

        result = get_tour_occupancy(db_session, tour.id)

        assert result.tickets_sold == 0
        assert result.total_capacity == 0
        assert result.percentage_sold == 0.0
