"""Unit tests for `get_tour_cities`, independent of the HTTP layer."""

from datetime import datetime, timedelta

from src.services.tour_service import get_tour_cities
from tests.fixtures.dashboard_fixtures import create_concert, create_tour, create_venues

BASE_TIME = datetime(2024, 6, 15, 20, 0, 0)


class TestGetTourCities:
    """Coverage for `get_tour_cities`."""

    def test_returns_cities_in_date_order(self, db_session):
        venues = create_venues(db_session, count=3)
        tour = create_tour(
            db_session, "Neon Skyline World Tour", "Aurora Belle",
            BASE_TIME.date(), BASE_TIME.date(), "active",
        )
        create_concert(db_session, tour, venues[2], day_offset=3, ticket_price="110.00", base_time=BASE_TIME)
        create_concert(db_session, tour, venues[0], day_offset=0, ticket_price="80.00", base_time=BASE_TIME)
        create_concert(db_session, tour, venues[1], day_offset=1, ticket_price="90.00", base_time=BASE_TIME)

        cities = get_tour_cities(db_session, tour.id)

        assert [c.city for c in cities] == ["New York", "London", "Paris"]
        assert [c.first_concert_date for c in cities] == [
            BASE_TIME.date(),
            (BASE_TIME + timedelta(days=1)).date(),
            (BASE_TIME + timedelta(days=3)).date(),
        ]

    def test_deduplicates_repeated_city_to_earliest_date(self, db_session):
        venues = create_venues(db_session, count=1)
        tour = create_tour(
            db_session, "Repeat Visit Tour", "Aurora Belle",
            BASE_TIME.date(), BASE_TIME.date(), "active",
        )
        create_concert(db_session, tour, venues[0], day_offset=5, ticket_price="80.00", base_time=BASE_TIME)
        create_concert(db_session, tour, venues[0], day_offset=0, ticket_price="90.00", base_time=BASE_TIME)
        create_concert(db_session, tour, venues[0], day_offset=2, ticket_price="100.00", base_time=BASE_TIME)

        cities = get_tour_cities(db_session, tour.id)

        assert len(cities) == 1
        assert cities[0].city == "New York"
        assert cities[0].first_concert_date == BASE_TIME.date()

    def test_excludes_cancelled_concerts(self, db_session):
        venues = create_venues(db_session, count=2)
        tour = create_tour(
            db_session, "Solstice Echoes Tour", "Vela Ashford",
            BASE_TIME.date(), BASE_TIME.date(), "active",
        )
        create_concert(db_session, tour, venues[0], day_offset=0, ticket_price="80.00", base_time=BASE_TIME)
        create_concert(
            db_session, tour, venues[1], day_offset=1, ticket_price="120.00", base_time=BASE_TIME,
            is_cancelled=True, cancellation_reason="Venue unavailable",
        )

        cities = get_tour_cities(db_session, tour.id)

        assert [c.city for c in cities] == ["New York"]

    def test_city_with_only_cancelled_concerts_is_omitted(self, db_session):
        venues = create_venues(db_session, count=1)
        tour = create_tour(
            db_session, "Grounded Tour", "Vela Ashford",
            BASE_TIME.date(), BASE_TIME.date(), "active",
        )
        create_concert(
            db_session, tour, venues[0], day_offset=0, ticket_price="80.00", base_time=BASE_TIME,
            is_cancelled=True, cancellation_reason="Artist illness",
        )

        cities = get_tour_cities(db_session, tour.id)

        assert cities == []

    def test_tour_without_concerts_returns_empty_list(self, db_session):
        tour = create_tour(
            db_session, "Unannounced Tour", "TBD Collective",
            BASE_TIME.date(), BASE_TIME.date(), "planned",
        )

        cities = get_tour_cities(db_session, tour.id)

        assert cities == []

    def test_unknown_tour_returns_none(self, db_session):
        cities = get_tour_cities(db_session, 999999)

        assert cities is None
