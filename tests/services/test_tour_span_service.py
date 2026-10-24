"""Unit tests for `get_tour_span`, independent of the HTTP layer."""

from datetime import datetime, timedelta

import pytest

from src.services.tour_service import TourNotFoundError, get_tour_span
from tests.fixtures.dashboard_fixtures import create_concert, create_tour, create_venues

BASE_TIME = datetime(2024, 6, 15, 20, 0, 0)


class TestGetTourSpan:
    """Coverage for `get_tour_span`."""

    def test_spans_concerts_inserted_out_of_chronological_order(self, db_session):
        venues = create_venues(db_session, count=3)
        tour = create_tour(
            db_session, "Neon Skyline World Tour", "Aurora Belle",
            BASE_TIME.date(), BASE_TIME.date(), "active",
        )
        create_concert(db_session, tour, venues[1], day_offset=10, ticket_price="90.00", base_time=BASE_TIME)
        create_concert(db_session, tour, venues[0], day_offset=0, ticket_price="80.00", base_time=BASE_TIME)
        create_concert(db_session, tour, venues[2], day_offset=20, ticket_price="110.00", base_time=BASE_TIME)

        span = get_tour_span(tour.id, db_session)

        assert span.first_date == BASE_TIME.date()
        assert span.last_date == (BASE_TIME + timedelta(days=20)).date()
        assert span.days_between == 20

    def test_excludes_cancelled_concerts_at_either_end(self, db_session):
        venues = create_venues(db_session, count=3)
        tour = create_tour(
            db_session, "Solstice Echoes Tour", "Vela Ashford",
            BASE_TIME.date(), BASE_TIME.date(), "active",
        )
        create_concert(
            db_session, tour, venues[0], day_offset=0, ticket_price="80.00", base_time=BASE_TIME,
            is_cancelled=True, cancellation_reason="Venue unavailable",
        )
        create_concert(db_session, tour, venues[1], day_offset=5, ticket_price="90.00", base_time=BASE_TIME)
        create_concert(
            db_session, tour, venues[2], day_offset=10, ticket_price="100.00", base_time=BASE_TIME,
            is_cancelled=True, cancellation_reason="Artist illness",
        )

        span = get_tour_span(tour.id, db_session)

        assert span.first_date == span.last_date == (BASE_TIME + timedelta(days=5)).date()
        assert span.days_between == 0

    def test_tour_with_only_cancelled_concerts_returns_all_none(self, db_session):
        venues = create_venues(db_session, count=1)
        tour = create_tour(
            db_session, "Grounded Tour", "Vela Ashford",
            BASE_TIME.date(), BASE_TIME.date(), "cancelled",
        )
        create_concert(
            db_session, tour, venues[0], day_offset=0, ticket_price="80.00", base_time=BASE_TIME,
            is_cancelled=True, cancellation_reason="Artist illness",
        )

        span = get_tour_span(tour.id, db_session)

        assert span.first_date is None
        assert span.last_date is None
        assert span.days_between is None

    def test_tour_with_zero_concerts_returns_all_none(self, db_session):
        tour = create_tour(
            db_session, "Unannounced Tour", "TBD Collective",
            BASE_TIME.date(), BASE_TIME.date(), "planned",
        )

        span = get_tour_span(tour.id, db_session)

        assert span.first_date is None
        assert span.last_date is None
        assert span.days_between is None

    def test_single_non_cancelled_concert_yields_zero_duration(self, db_session):
        venues = create_venues(db_session, count=1)
        tour = create_tour(
            db_session, "Solo Night Tour", "Aurora Belle",
            BASE_TIME.date(), BASE_TIME.date(), "active",
        )
        create_concert(db_session, tour, venues[0], day_offset=0, ticket_price="80.00", base_time=BASE_TIME)

        span = get_tour_span(tour.id, db_session)

        assert span.first_date == span.last_date == BASE_TIME.date()
        assert span.days_between == 0

    def test_unknown_tour_raises_tour_not_found_error(self, db_session):
        with pytest.raises(TourNotFoundError):
            get_tour_span(999999, db_session)
