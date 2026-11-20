"""Unit tests for `get_next_concert`, independent of the HTTP layer."""

from datetime import datetime

import pytest

from src.models import ConcertStatus
from src.services.exceptions import NoUpcomingConcert, TourNotFound
from src.services.tour_service import get_next_concert
from tests.fixtures.dashboard_fixtures import create_concert, create_tour, create_venues

BASE_TIME = datetime(2024, 6, 15, 20, 0, 0)


def _patch_now(monkeypatch, now=BASE_TIME):
    monkeypatch.setattr("src.services.tour_service.get_reference_time", lambda: now)


class TestGetNextConcert:
    """Coverage for `get_next_concert`."""

    def test_returns_earliest_upcoming_concert_with_venue_details(self, db_session, monkeypatch):
        _patch_now(monkeypatch)
        venues = create_venues(db_session, count=2)
        tour = create_tour(
            db_session, "Neon Skyline World Tour", "Aurora Belle",
            BASE_TIME.date(), BASE_TIME.date(), "active",
        )
        later = create_concert(
            db_session, tour, venues[0], day_offset=10, ticket_price="80.00",
            base_time=BASE_TIME, tickets_sold=100,
        )
        earliest = create_concert(
            db_session, tour, venues[1], day_offset=1, ticket_price="80.00",
            base_time=BASE_TIME, tickets_sold=18000,
        )

        result = get_next_concert(db_session, tour.id)

        assert result.concert_id == earliest.id
        assert result.date == earliest.date_time
        assert result.venue_name == venues[1].name
        assert result.venue_city == venues[1].city
        assert result.tickets_remaining == venues[1].capacity - 18000

    def test_skips_cancelled_concert_that_is_chronologically_earliest(self, db_session, monkeypatch):
        _patch_now(monkeypatch)
        venues = create_venues(db_session, count=2)
        tour = create_tour(
            db_session, "Neon Skyline World Tour", "Aurora Belle",
            BASE_TIME.date(), BASE_TIME.date(), "active",
        )
        cancelled_earliest = create_concert(
            db_session, tour, venues[0], day_offset=1, ticket_price="80.00",
            base_time=BASE_TIME, is_cancelled=True, cancellation_reason="Venue issue",
        )
        cancelled_earliest.status = ConcertStatus.cancelled
        db_session.commit()
        next_valid = create_concert(
            db_session, tour, venues[1], day_offset=5, ticket_price="80.00", base_time=BASE_TIME,
        )

        result = get_next_concert(db_session, tour.id)

        assert result.concert_id == next_valid.id

    def test_concert_exactly_at_now_counts_as_upcoming(self, db_session, monkeypatch):
        _patch_now(monkeypatch)
        venue = create_venues(db_session, count=1)[0]
        tour = create_tour(
            db_session, "Neon Skyline World Tour", "Aurora Belle",
            BASE_TIME.date(), BASE_TIME.date(), "active",
        )
        concert = create_concert(
            db_session, tour, venue, day_offset=0, ticket_price="80.00", base_time=BASE_TIME,
        )

        result = get_next_concert(db_session, tour.id)

        assert result.concert_id == concert.id

    def test_past_concert_is_never_returned(self, db_session, monkeypatch):
        _patch_now(monkeypatch)
        venue = create_venues(db_session, count=1)[0]
        tour = create_tour(
            db_session, "River Stone Farewell Tour", "River Stone",
            BASE_TIME.date(), BASE_TIME.date(), "completed",
        )
        create_concert(
            db_session, tour, venue, day_offset=-1, ticket_price="65.00", base_time=BASE_TIME,
        )

        with pytest.raises(NoUpcomingConcert):
            get_next_concert(db_session, tour.id)

    def test_no_concerts_at_all_raises_no_upcoming_concert(self, db_session, monkeypatch):
        _patch_now(monkeypatch)
        tour = create_tour(
            db_session, "Unannounced Tour", "TBD Collective",
            BASE_TIME.date(), BASE_TIME.date(), "planned",
        )

        with pytest.raises(NoUpcomingConcert):
            get_next_concert(db_session, tour.id)

    def test_unknown_tour_raises_tour_not_found(self, db_session, monkeypatch):
        _patch_now(monkeypatch)

        with pytest.raises(TourNotFound):
            get_next_concert(db_session, 999999)

    def test_other_tours_concert_is_excluded(self, db_session, monkeypatch):
        _patch_now(monkeypatch)
        venues = create_venues(db_session, count=2)
        tour = create_tour(
            db_session, "Neon Skyline World Tour", "Aurora Belle",
            BASE_TIME.date(), BASE_TIME.date(), "active",
        )
        other_tour = create_tour(
            db_session, "Other Tour", "Someone Else",
            BASE_TIME.date(), BASE_TIME.date(), "active",
        )
        create_concert(
            db_session, other_tour, venues[0], day_offset=1, ticket_price="80.00", base_time=BASE_TIME,
        )

        with pytest.raises(NoUpcomingConcert):
            get_next_concert(db_session, tour.id)

    def test_tickets_remaining_is_clamped_at_zero_when_sold_out(self, db_session, monkeypatch):
        _patch_now(monkeypatch)
        venue = create_venues(db_session, count=1)[0]
        tour = create_tour(
            db_session, "Neon Skyline World Tour", "Aurora Belle",
            BASE_TIME.date(), BASE_TIME.date(), "active",
        )
        concert = create_concert(
            db_session, tour, venue, day_offset=1, ticket_price="80.00",
            base_time=BASE_TIME, tickets_sold=venue.capacity,
        )

        result = get_next_concert(db_session, tour.id)

        assert result.concert_id == concert.id
        assert result.tickets_remaining == 0
