"""Unit tests for `get_sold_out_tours`, independent of the HTTP layer."""

from datetime import datetime

from src.services.tour_service import get_sold_out_tours
from tests.fixtures.dashboard_fixtures import create_concert, create_tour, create_venues

BASE_TIME = datetime(2024, 6, 15, 20, 0, 0)


class TestGetSoldOutTours:
    """Coverage for `get_sold_out_tours`."""

    def test_includes_tour_whose_only_concerts_are_sold_out(self, db_session):
        venues = create_venues(db_session, count=2)
        tour = create_tour(
            db_session, "Neon Skyline World Tour", "Aurora Belle",
            BASE_TIME.date(), BASE_TIME.date(), "active",
        )
        create_concert(
            db_session, tour, venues[0], day_offset=0, ticket_price="80.00",
            base_time=BASE_TIME, tickets_sold=venues[0].capacity,
        )
        create_concert(
            db_session, tour, venues[1], day_offset=1, ticket_price="120.00",
            base_time=BASE_TIME, tickets_sold=venues[1].capacity,
        )

        result = get_sold_out_tours(db_session)

        assert [t.id for t in result] == [tour.id]

    def test_excludes_tour_with_one_sold_out_and_one_scheduled_concert(self, db_session):
        venues = create_venues(db_session, count=2)
        tour = create_tour(
            db_session, "Neon Skyline World Tour", "Aurora Belle",
            BASE_TIME.date(), BASE_TIME.date(), "active",
        )
        create_concert(
            db_session, tour, venues[0], day_offset=0, ticket_price="80.00",
            base_time=BASE_TIME, tickets_sold=venues[0].capacity,
        )
        create_concert(
            db_session, tour, venues[1], day_offset=1, ticket_price="120.00",
            base_time=BASE_TIME, tickets_sold=1,
        )

        result = get_sold_out_tours(db_session)

        assert result == []

    def test_excludes_tour_whose_only_concerts_are_cancelled(self, db_session):
        venues = create_venues(db_session, count=1)
        tour = create_tour(
            db_session, "Cancelled Tour", "Aurora Belle",
            BASE_TIME.date(), BASE_TIME.date(), "cancelled",
        )
        create_concert(
            db_session, tour, venues[0], day_offset=0, ticket_price="80.00",
            base_time=BASE_TIME, tickets_sold=venues[0].capacity,
            is_cancelled=True, cancellation_reason="Artist illness",
        )

        result = get_sold_out_tours(db_session)

        assert result == []

    def test_excludes_tour_with_zero_concerts(self, db_session):
        create_tour(
            db_session, "Unannounced Tour", "TBD Collective",
            BASE_TIME.date(), BASE_TIME.date(), "planned",
        )

        result = get_sold_out_tours(db_session)

        assert result == []

    def test_includes_tour_with_one_cancelled_and_one_sold_out_concert(self, db_session):
        venues = create_venues(db_session, count=2)
        tour = create_tour(
            db_session, "Neon Skyline World Tour", "Aurora Belle",
            BASE_TIME.date(), BASE_TIME.date(), "active",
        )
        create_concert(
            db_session, tour, venues[0], day_offset=0, ticket_price="80.00",
            base_time=BASE_TIME, tickets_sold=venues[0].capacity,
        )
        create_concert(
            db_session, tour, venues[1], day_offset=1, ticket_price="120.00",
            base_time=BASE_TIME, tickets_sold=1,
            is_cancelled=True, cancellation_reason="Venue flooded",
        )

        result = get_sold_out_tours(db_session)

        assert [t.id for t in result] == [tour.id]

    def test_no_qualifying_tour_returns_empty_list(self, db_session):
        venues = create_venues(db_session, count=1)
        tour = create_tour(
            db_session, "Homecoming Revival Tour", "The Midnight Collective",
            BASE_TIME.date(), BASE_TIME.date(), "planned",
        )
        create_concert(
            db_session, tour, venues[0], day_offset=0, ticket_price="95.00",
            base_time=BASE_TIME, tickets_sold=1,
        )

        result = get_sold_out_tours(db_session)

        assert result == []
