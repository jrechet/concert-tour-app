"""Unit tests for `get_concert_occupancy`, independent of the HTTP layer."""

from datetime import datetime

from src.services.concerts_service import get_concert_occupancy
from tests.fixtures.dashboard_fixtures import create_concert, create_tour, create_venues

BASE_TIME = datetime(2024, 6, 15, 20, 0, 0)


class TestGetConcertOccupancy:
    """Coverage for `get_concert_occupancy`."""

    def test_known_capacity_returns_correct_percentage(self, db_session):
        venues = create_venues(db_session, count=1)
        tour = create_tour(
            db_session, "Neon Skyline World Tour", "Aurora Belle",
            BASE_TIME.date(), BASE_TIME.date(), "active",
        )
        concert = create_concert(
            db_session, tour, venues[0], day_offset=0, ticket_price="80.00",
            base_time=BASE_TIME, tickets_sold=15000,
        )

        occupancy = get_concert_occupancy(db_session, concert.id)

        assert occupancy.concert_id == concert.id
        assert occupancy.tickets_sold == 15000
        assert occupancy.capacity == venues[0].capacity
        assert occupancy.percentage_sold == round(15000 / venues[0].capacity * 100, 1)

    def test_unknown_capacity_returns_null_percentage(self, db_session):
        venue = create_venues(db_session, count=1)[0]
        venue.capacity = None
        db_session.commit()
        tour = create_tour(
            db_session, "Solo Tour", "Test Artist",
            BASE_TIME.date(), BASE_TIME.date(), "active",
        )
        concert = create_concert(
            db_session, tour, venue, day_offset=0, ticket_price="80.00",
            base_time=BASE_TIME, tickets_sold=500,
        )

        occupancy = get_concert_occupancy(db_session, concert.id)

        assert occupancy.tickets_sold == 500
        assert occupancy.capacity is None
        assert occupancy.percentage_sold is None

    def test_unknown_concert_id_returns_none(self, db_session):
        assert get_concert_occupancy(db_session, 999999) is None
