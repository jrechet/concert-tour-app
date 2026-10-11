"""Unit tests for `uncancel_tour`, independent of the HTTP layer."""

from datetime import datetime

import pytest

from src.schemas.tour import TourStatus
from src.services.tour_service import TourConflictError, TourNotFoundError, uncancel_tour
from tests.fixtures.dashboard_fixtures import create_concert, create_tour, create_venues

BASE_TIME = datetime(2024, 6, 15, 20, 0, 0)


class TestUncancelTour:
    """Coverage for `uncancel_tour`."""

    def test_restores_cancelled_tour_to_planned(self, db_session):
        tour = create_tour(
            db_session, "Reunion Tour", "Aurora Belle",
            BASE_TIME.date(), BASE_TIME.date(), "cancelled",
        )

        result = uncancel_tour(db_session, tour.id)

        assert result.id == tour.id
        assert result.status == TourStatus.PLANNED.value

    def test_restores_concerts_cancelled_with_tour_and_resets_flag(self, db_session):
        venues = create_venues(db_session, count=1)
        tour = create_tour(
            db_session, "Reunion Tour", "Aurora Belle",
            BASE_TIME.date(), BASE_TIME.date(), "cancelled",
        )
        concert = create_concert(
            db_session, tour, venues[0], day_offset=1, ticket_price="80.00",
            base_time=BASE_TIME, is_cancelled=True, cancellation_reason="Tour cancelled",
        )
        concert.cancelled_with_tour = True
        db_session.commit()

        uncancel_tour(db_session, tour.id)

        db_session.refresh(concert)
        assert concert.is_cancelled is False
        assert concert.cancellation_reason is None
        assert concert.cancelled_with_tour is False

    def test_leaves_independently_cancelled_concerts_cancelled(self, db_session):
        venues = create_venues(db_session, count=2)
        tour = create_tour(
            db_session, "Reunion Tour", "Aurora Belle",
            BASE_TIME.date(), BASE_TIME.date(), "cancelled",
        )
        cascaded = create_concert(
            db_session, tour, venues[0], day_offset=1, ticket_price="80.00",
            base_time=BASE_TIME, is_cancelled=True, cancellation_reason="Tour cancelled",
        )
        cascaded.cancelled_with_tour = True
        independently_cancelled = create_concert(
            db_session, tour, venues[1], day_offset=2, ticket_price="80.00",
            base_time=BASE_TIME, is_cancelled=True, cancellation_reason="Venue closed",
        )
        db_session.commit()

        uncancel_tour(db_session, tour.id)

        db_session.refresh(cascaded)
        db_session.refresh(independently_cancelled)
        assert cascaded.is_cancelled is False
        assert independently_cancelled.is_cancelled is True
        assert independently_cancelled.cancellation_reason == "Venue closed"
        assert independently_cancelled.cancelled_with_tour is False

    def test_unknown_tour_id_raises_not_found(self, db_session):
        with pytest.raises(TourNotFoundError):
            uncancel_tour(db_session, 999)

    @pytest.mark.parametrize("status", ["planned", "completed"])
    def test_non_cancelled_tour_raises_conflict(self, db_session, status):
        tour = create_tour(
            db_session, "Active Tour", "Aurora Belle",
            BASE_TIME.date(), BASE_TIME.date(), status,
        )

        with pytest.raises(TourConflictError, match=status):
            uncancel_tour(db_session, tour.id)

    def test_conflict_leaves_tour_and_concerts_unchanged(self, db_session):
        venues = create_venues(db_session, count=1)
        tour = create_tour(
            db_session, "Active Tour", "Aurora Belle",
            BASE_TIME.date(), BASE_TIME.date(), "planned",
        )
        concert = create_concert(
            db_session, tour, venues[0], day_offset=1, ticket_price="80.00",
            base_time=BASE_TIME,
        )

        with pytest.raises(TourConflictError):
            uncancel_tour(db_session, tour.id)

        db_session.refresh(tour)
        db_session.refresh(concert)
        assert tour.status == "planned"
        assert concert.is_cancelled is False
        assert concert.cancelled_with_tour is False
