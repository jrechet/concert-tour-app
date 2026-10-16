"""Unit tests for `cancel_tour`, independent of the HTTP layer."""

from datetime import datetime

import pytest

from src.services.tour_service import TourNotFoundError, cancel_tour
from tests.fixtures.dashboard_fixtures import create_concert, create_tour, create_venues

BASE_TIME = datetime(2024, 6, 15, 20, 0, 0)


class TestCancelTour:
    """Coverage for `cancel_tour`."""

    def test_cancels_only_upcoming_uncancelled_concerts_of_the_tour(self, db_session):
        venues = create_venues(db_session, count=5)
        tour = create_tour(
            db_session, "Farewell Tour", "Aurora Belle",
            BASE_TIME.date(), BASE_TIME.date(), "active",
        )
        other_tour = create_tour(
            db_session, "Other Tour", "Someone Else",
            BASE_TIME.date(), BASE_TIME.date(), "active",
        )
        past = create_concert(db_session, tour, venues[0], day_offset=-5, ticket_price="80.00", base_time=BASE_TIME)
        upcoming_1 = create_concert(db_session, tour, venues[1], day_offset=1, ticket_price="80.00", base_time=BASE_TIME)
        upcoming_2 = create_concert(db_session, tour, venues[2], day_offset=10, ticket_price="80.00", base_time=BASE_TIME)
        already_cancelled = create_concert(
            db_session, tour, venues[3], day_offset=5, ticket_price="80.00", base_time=BASE_TIME,
            is_cancelled=True, cancellation_reason="Prior reason",
        )
        other_tour_upcoming = create_concert(
            db_session, other_tour, venues[4], day_offset=1, ticket_price="80.00", base_time=BASE_TIME,
        )

        count = cancel_tour(db_session, tour.id, "Artist illness", reference_time=BASE_TIME)

        assert count == 2

        db_session.refresh(past)
        db_session.refresh(upcoming_1)
        db_session.refresh(upcoming_2)
        db_session.refresh(already_cancelled)
        db_session.refresh(other_tour_upcoming)

        assert past.is_cancelled is False
        assert past.cancellation_reason is None

        assert upcoming_1.is_cancelled is True
        assert upcoming_1.cancellation_reason == "Artist illness"
        assert upcoming_2.is_cancelled is True
        assert upcoming_2.cancellation_reason == "Artist illness"

        assert already_cancelled.is_cancelled is True
        assert already_cancelled.cancellation_reason == "Prior reason"

        assert other_tour_upcoming.is_cancelled is False
        assert other_tour_upcoming.cancellation_reason is None

    def test_tour_with_only_past_concerts_returns_zero(self, db_session):
        venues = create_venues(db_session, count=1)
        tour = create_tour(
            db_session, "Already Over Tour", "Aurora Belle",
            BASE_TIME.date(), BASE_TIME.date(), "completed",
        )
        past = create_concert(db_session, tour, venues[0], day_offset=-40, ticket_price="80.00", base_time=BASE_TIME)

        count = cancel_tour(db_session, tour.id, "Tour ended", reference_time=BASE_TIME)

        assert count == 0
        db_session.refresh(past)
        assert past.is_cancelled is False
        assert past.cancellation_reason is None

    def test_unknown_tour_id_raises_not_found(self, db_session):
        with pytest.raises(TourNotFoundError):
            cancel_tour(db_session, 999, "Artist illness", reference_time=BASE_TIME)

    def test_same_calendar_day_concert_counts_as_upcoming(self, db_session):
        venues = create_venues(db_session, count=1)
        tour = create_tour(
            db_session, "Boundary Tour", "Aurora Belle",
            BASE_TIME.date(), BASE_TIME.date(), "active",
        )
        same_day = create_concert(db_session, tour, venues[0], day_offset=0, ticket_price="80.00", base_time=BASE_TIME)

        count = cancel_tour(db_session, tour.id, "Artist illness", reference_time=BASE_TIME)

        assert count == 1
        db_session.refresh(same_day)
        assert same_day.is_cancelled is True
        assert same_day.cancellation_reason == "Artist illness"

    def test_defaults_reference_time_to_get_reference_time(self, db_session, monkeypatch):
        venues = create_venues(db_session, count=1)
        tour = create_tour(
            db_session, "Default Reference Tour", "Aurora Belle",
            BASE_TIME.date(), BASE_TIME.date(), "active",
        )
        upcoming = create_concert(db_session, tour, venues[0], day_offset=1, ticket_price="80.00", base_time=BASE_TIME)

        monkeypatch.setattr("src.services.tour_service.get_reference_time", lambda: BASE_TIME)
        count = cancel_tour(db_session, tour.id, "Artist illness")

        assert count == 1
        db_session.refresh(upcoming)
        assert upcoming.is_cancelled is True
