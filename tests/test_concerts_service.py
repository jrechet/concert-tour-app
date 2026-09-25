"""Unit tests for `get_concerts_for_export`, independent of the HTTP layer."""

from datetime import datetime

from src.services.concerts_service import get_concerts_for_export
from tests.fixtures.dashboard_fixtures import create_concert, create_tour, create_venues

BASE_TIME = datetime(2024, 6, 15, 20, 0, 0)


class TestGetConcertsForExport:
    """Coverage for `get_concerts_for_export`."""

    def test_no_concerts_returns_empty_list(self, db_session):
        assert get_concerts_for_export(db_session) == []

    def test_returns_rows_ordered_by_date_ascending(self, db_session):
        venues = create_venues(db_session, count=2)
        tour = create_tour(
            db_session, "Neon Skyline World Tour", "Aurora Belle",
            BASE_TIME.date(), BASE_TIME.date(), "active",
        )
        second = create_concert(db_session, tour, venues[1], day_offset=5, ticket_price="90.00", base_time=BASE_TIME)
        first = create_concert(db_session, tour, venues[0], day_offset=0, ticket_price="80.00", base_time=BASE_TIME)

        rows = get_concerts_for_export(db_session)

        assert rows == [
            {
                "date": first.date_time.date().isoformat(),
                "city": venues[0].city,
                "venue": venues[0].name,
                "tour": tour.name,
            },
            {
                "date": second.date_time.date().isoformat(),
                "city": venues[1].city,
                "venue": venues[1].name,
                "tour": tour.name,
            },
        ]

    def test_resolves_venue_and_tour_names_via_relationships(self, db_session):
        venues = create_venues(db_session, count=1)
        tour = create_tour(
            db_session, "Solo Tour", "Test Artist",
            BASE_TIME.date(), BASE_TIME.date(), "active",
        )
        create_concert(db_session, tour, venues[0], day_offset=0, ticket_price="80.00", base_time=BASE_TIME)

        rows = get_concerts_for_export(db_session)

        assert len(rows) == 1
        assert rows[0]["city"] == venues[0].city
        assert rows[0]["venue"] == venues[0].name
        assert rows[0]["tour"] == tour.name
