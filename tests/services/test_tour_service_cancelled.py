"""Unit tests for `list_cancelled_tours`, independent of the HTTP layer."""

from datetime import date, datetime

from src.services.tour_service import list_cancelled_tours
from tests.fixtures.dashboard_fixtures import create_concert, create_tour, create_venues

BASE_TIME = datetime(2024, 6, 15, 20, 0, 0)


class TestListCancelledTours:
    """Coverage for `list_cancelled_tours`."""

    def test_returns_only_cancelled_tours(self, db_session):
        venues = create_venues(db_session, count=2)
        cancelled = create_tour(
            db_session, "Farewell Tour", "Aurora Belle",
            date(2024, 3, 1), date(2024, 3, 10), "cancelled",
        )
        active = create_tour(
            db_session, "Active Tour", "Someone Else",
            date(2024, 4, 1), date(2024, 4, 10), "active",
        )
        create_concert(db_session, cancelled, venues[0], day_offset=0, ticket_price="80.00", base_time=BASE_TIME)
        create_concert(db_session, active, venues[1], day_offset=0, ticket_price="80.00", base_time=BASE_TIME)

        results = list_cancelled_tours(db_session)

        assert [r.id for r in results] == [cancelled.id]
        assert results[0].name == "Farewell Tour"

    def test_concert_count_excludes_other_tours_concerts(self, db_session):
        venues = create_venues(db_session, count=3)
        tour = create_tour(
            db_session, "Farewell Tour", "Aurora Belle",
            date(2024, 3, 1), date(2024, 3, 10), "cancelled",
        )
        other_tour = create_tour(
            db_session, "Other Tour", "Someone Else",
            date(2024, 2, 1), date(2024, 2, 10), "cancelled",
        )
        create_concert(db_session, tour, venues[0], day_offset=0, ticket_price="80.00", base_time=BASE_TIME)
        create_concert(db_session, tour, venues[1], day_offset=1, ticket_price="80.00", base_time=BASE_TIME)
        create_concert(db_session, other_tour, venues[2], day_offset=0, ticket_price="80.00", base_time=BASE_TIME)

        results = list_cancelled_tours(db_session)
        by_id = {r.id: r for r in results}

        assert by_id[tour.id].concert_count == 2
        assert by_id[other_tour.id].concert_count == 1

    def test_cancelled_tour_with_no_concerts_has_zero_count(self, db_session):
        tour = create_tour(
            db_session, "Unannounced Cancellation", "Aurora Belle",
            date(2024, 3, 1), date(2024, 3, 10), "cancelled",
        )

        results = list_cancelled_tours(db_session)

        assert len(results) == 1
        assert results[0].id == tour.id
        assert results[0].concert_count == 0

    def test_ordered_by_start_date_descending(self, db_session):
        earliest = create_tour(
            db_session, "Earliest Tour", "Aurora Belle",
            date(2024, 1, 1), date(2024, 1, 10), "cancelled",
        )
        latest = create_tour(
            db_session, "Latest Tour", "Aurora Belle",
            date(2024, 6, 1), date(2024, 6, 10), "cancelled",
        )
        middle = create_tour(
            db_session, "Middle Tour", "Aurora Belle",
            date(2024, 3, 1), date(2024, 3, 10), "cancelled",
        )

        results = list_cancelled_tours(db_session)

        assert [r.id for r in results] == [latest.id, middle.id, earliest.id]

    def test_returns_empty_list_when_no_tour_is_cancelled(self, db_session):
        create_tour(
            db_session, "Active Tour", "Aurora Belle",
            date(2024, 1, 1), date(2024, 1, 10), "active",
        )

        results = list_cancelled_tours(db_session)

        assert results == []
