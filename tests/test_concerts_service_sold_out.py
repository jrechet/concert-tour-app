"""Unit tests for `get_sold_out_concerts`, independent of the HTTP layer.

`reference_time` is passed explicitly to a fixed moment so "upcoming"
assertions don't depend on the real wall clock, mirroring
`tests/test_concerts_service_next.py`.
"""

from datetime import datetime, timedelta

from src.services.concerts_service import get_sold_out_concerts
from tests.fixtures.dashboard_fixtures import create_concert, create_tour, create_venues

REFERENCE_TIME = datetime(2024, 6, 15, 18, 0, 0)


class TestGetSoldOutConcerts:
    """Coverage for `get_sold_out_concerts`."""

    def test_no_concerts_returns_empty_list(self, db_session):
        assert get_sold_out_concerts(db_session, REFERENCE_TIME) == []

    def test_sold_out_upcoming_concert_is_included(self, db_session):
        venues = create_venues(db_session, count=1)
        tour = create_tour(
            db_session, "Farewell Tour", "Test Artist",
            REFERENCE_TIME.date(),
            (REFERENCE_TIME + timedelta(days=30)).date(),
            "active",
        )
        sold_out = create_concert(
            db_session, tour, venues[0], day_offset=5, ticket_price="80.00", base_time=REFERENCE_TIME,
            tickets_sold=venues[0].capacity,
        )

        results = get_sold_out_concerts(db_session, REFERENCE_TIME)

        assert [c.id for c in results] == [sold_out.id]

    def test_sold_out_but_cancelled_concert_is_excluded(self, db_session):
        venues = create_venues(db_session, count=1)
        tour = create_tour(
            db_session, "Cancelled Tour", "Test Artist",
            REFERENCE_TIME.date(),
            (REFERENCE_TIME + timedelta(days=30)).date(),
            "active",
        )
        create_concert(
            db_session, tour, venues[0], day_offset=5, ticket_price="80.00", base_time=REFERENCE_TIME,
            tickets_sold=venues[0].capacity, is_cancelled=True, cancellation_reason="Venue closed",
        )

        assert get_sold_out_concerts(db_session, REFERENCE_TIME) == []

    def test_sold_out_but_past_concert_is_excluded(self, db_session):
        venues = create_venues(db_session, count=1)
        tour = create_tour(
            db_session, "Farewell Tour", "Test Artist",
            (REFERENCE_TIME - timedelta(days=30)).date(),
            (REFERENCE_TIME + timedelta(days=1)).date(),
            "active",
        )
        create_concert(
            db_session, tour, venues[0], day_offset=-1, ticket_price="80.00", base_time=REFERENCE_TIME,
            tickets_sold=venues[0].capacity,
        )

        assert get_sold_out_concerts(db_session, REFERENCE_TIME) == []

    def test_upcoming_concert_with_tickets_left_is_excluded(self, db_session):
        venues = create_venues(db_session, count=1)
        tour = create_tour(
            db_session, "Farewell Tour", "Test Artist",
            REFERENCE_TIME.date(),
            (REFERENCE_TIME + timedelta(days=30)).date(),
            "active",
        )
        create_concert(
            db_session, tour, venues[0], day_offset=5, ticket_price="80.00", base_time=REFERENCE_TIME,
            tickets_sold=venues[0].capacity - 1,
        )

        assert get_sold_out_concerts(db_session, REFERENCE_TIME) == []

    def test_concert_with_no_venue_capacity_is_excluded(self, db_session):
        venues = create_venues(db_session, count=1)
        venues[0].capacity = None
        db_session.commit()
        tour = create_tour(
            db_session, "Unknown Capacity Tour", "Test Artist",
            REFERENCE_TIME.date(),
            (REFERENCE_TIME + timedelta(days=30)).date(),
            "active",
        )
        create_concert(
            db_session, tour, venues[0], day_offset=5, ticket_price="80.00", base_time=REFERENCE_TIME,
            tickets_sold=0,
        )

        assert get_sold_out_concerts(db_session, REFERENCE_TIME) == []

    def test_results_are_ordered_soonest_first(self, db_session):
        venues = create_venues(db_session, count=2)
        tour = create_tour(
            db_session, "Scramble Tour", "Test Artist",
            REFERENCE_TIME.date(),
            (REFERENCE_TIME + timedelta(days=30)).date(),
            "active",
        )
        later = create_concert(
            db_session, tour, venues[0], day_offset=20, ticket_price="80.00", base_time=REFERENCE_TIME,
            tickets_sold=venues[0].capacity,
        )
        soonest = create_concert(
            db_session, tour, venues[1], day_offset=1, ticket_price="80.00", base_time=REFERENCE_TIME,
            tickets_sold=venues[1].capacity,
        )

        results = get_sold_out_concerts(db_session, REFERENCE_TIME)

        assert [c.id for c in results] == [soonest.id, later.id]

    def test_concert_at_exact_reference_time_is_included(self, db_session):
        venues = create_venues(db_session, count=1)
        tour = create_tour(
            db_session, "Exact Time Tour", "Test Artist",
            (REFERENCE_TIME - timedelta(days=5)).date(),
            (REFERENCE_TIME + timedelta(days=5)).date(),
            "active",
        )
        concert = create_concert(
            db_session, tour, venues[0], day_offset=0, ticket_price="80.00", base_time=REFERENCE_TIME,
            tickets_sold=venues[0].capacity,
        )

        results = get_sold_out_concerts(db_session, REFERENCE_TIME)

        assert [c.id for c in results] == [concert.id]

    def test_venue_is_eagerly_loaded(self, db_session):
        venues = create_venues(db_session, count=1)
        tour = create_tour(
            db_session, "Loaded Tour", "Test Artist",
            REFERENCE_TIME.date(),
            (REFERENCE_TIME + timedelta(days=10)).date(),
            "active",
        )
        create_concert(
            db_session, tour, venues[0], day_offset=1, ticket_price="80.00", base_time=REFERENCE_TIME,
            tickets_sold=venues[0].capacity,
        )

        results = get_sold_out_concerts(db_session, REFERENCE_TIME)

        assert results[0].venue.name == venues[0].name

    def test_defaults_to_the_app_reference_time_when_omitted(self, db_session, monkeypatch):
        venues = create_venues(db_session, count=1)
        tour = create_tour(
            db_session, "Default Time Tour", "Test Artist",
            (REFERENCE_TIME - timedelta(days=5)).date(),
            (REFERENCE_TIME + timedelta(days=5)).date(),
            "active",
        )
        sold_out = create_concert(
            db_session, tour, venues[0], day_offset=1, ticket_price="80.00", base_time=REFERENCE_TIME,
            tickets_sold=venues[0].capacity,
        )
        monkeypatch.setattr(
            "src.services.concerts_service.get_reference_time", lambda: REFERENCE_TIME
        )

        results = get_sold_out_concerts(db_session)

        assert [c.id for c in results] == [sold_out.id]
