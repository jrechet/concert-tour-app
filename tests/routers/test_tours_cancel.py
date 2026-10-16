"""Tests for `POST /api/v1/tours/{tour_id}/cancel`, using the `TourCancelRequest`/
`TourCancelResponse` schemas.

`reference_time` is overridden to a fixed moment so "upcoming vs. past"
assertions don't depend on the real wall clock.
"""

from datetime import datetime, timedelta

import pytest

from src.database import get_reference_time
from src.main import app
from tests.fixtures.dashboard_fixtures import create_concert, create_tour, create_venues

REFERENCE_TIME = datetime(2024, 6, 15, 18, 0, 0)


@pytest.fixture(autouse=True)
def frozen_reference_time():
    """Pin `get_reference_time` to `REFERENCE_TIME` for every test in this module."""
    previous_override = app.dependency_overrides.get(get_reference_time)
    app.dependency_overrides[get_reference_time] = lambda: REFERENCE_TIME
    yield
    if previous_override is None:
        app.dependency_overrides.pop(get_reference_time, None)
    else:
        app.dependency_overrides[get_reference_time] = previous_override


class TestCancelTourEndpoint:
    """Coverage for `POST /api/v1/tours/{tour_id}/cancel`."""

    def test_valid_reason_cancels_upcoming_concerts_and_returns_count(self, client, db_session):
        base_time = REFERENCE_TIME
        venues = create_venues(db_session, count=2)
        tour = create_tour(
            db_session, "Farewell Tour", "Test Artist",
            (base_time - timedelta(days=10)).date(), (base_time + timedelta(days=30)).date(), "active",
        )
        upcoming_1 = create_concert(db_session, tour, venues[0], day_offset=1, ticket_price="80.00", base_time=base_time)
        upcoming_2 = create_concert(db_session, tour, venues[1], day_offset=5, ticket_price="80.00", base_time=base_time)

        response = client.post(
            f"/api/v1/tours/{tour.id}/cancel",
            json={"reason": "Artist illness"},
        )

        assert response.status_code == 200
        assert response.json() == {"tour_id": tour.id, "cancelled_count": 2}

        db_session.refresh(upcoming_1)
        db_session.refresh(upcoming_2)
        assert upcoming_1.is_cancelled is True
        assert upcoming_1.cancellation_reason == "Artist illness"
        assert upcoming_2.is_cancelled is True
        assert upcoming_2.cancellation_reason == "Artist illness"

    def test_only_expected_concerts_change_status(self, client, db_session):
        base_time = REFERENCE_TIME
        venues = create_venues(db_session, count=3)
        tour = create_tour(
            db_session, "Mixed Tour", "Test Artist",
            (base_time - timedelta(days=30)).date(), (base_time + timedelta(days=30)).date(), "active",
        )
        past = create_concert(db_session, tour, venues[0], day_offset=-5, ticket_price="80.00", base_time=base_time)
        upcoming = create_concert(db_session, tour, venues[1], day_offset=1, ticket_price="80.00", base_time=base_time)
        already_cancelled = create_concert(
            db_session, tour, venues[2], day_offset=10, ticket_price="80.00", base_time=base_time,
            is_cancelled=True, cancellation_reason="Prior reason",
        )

        response = client.post(
            f"/api/v1/tours/{tour.id}/cancel",
            json={"reason": "Venue unavailable"},
        )
        assert response.status_code == 200
        assert response.json() == {"tour_id": tour.id, "cancelled_count": 1}

        db_session.refresh(past)
        db_session.refresh(upcoming)
        db_session.refresh(already_cancelled)

        assert past.is_cancelled is False
        assert past.cancellation_reason is None

        assert upcoming.is_cancelled is True
        assert upcoming.cancellation_reason == "Venue unavailable"

        assert already_cancelled.is_cancelled is True
        assert already_cancelled.cancellation_reason == "Prior reason"

    def test_unknown_tour_id_returns_404(self, client):
        response = client.post("/api/v1/tours/999999/cancel", json={"reason": "Artist illness"})
        assert response.status_code == 404
        assert response.json()["detail"] == "Tour not found"

    def test_missing_reason_returns_422(self, client, db_session):
        tour = create_tour(
            db_session, "No Reason Tour", "Test Artist",
            REFERENCE_TIME.date(), (REFERENCE_TIME + timedelta(days=30)).date(), "active",
        )
        response = client.post(f"/api/v1/tours/{tour.id}/cancel", json={})
        assert response.status_code == 422

    def test_empty_reason_returns_422(self, client, db_session):
        tour = create_tour(
            db_session, "Empty Reason Tour", "Test Artist",
            REFERENCE_TIME.date(), (REFERENCE_TIME + timedelta(days=30)).date(), "active",
        )
        response = client.post(f"/api/v1/tours/{tour.id}/cancel", json={"reason": ""})
        assert response.status_code == 422

    def test_whitespace_only_reason_returns_422(self, client, db_session):
        tour = create_tour(
            db_session, "Blank Reason Tour", "Test Artist",
            REFERENCE_TIME.date(), (REFERENCE_TIME + timedelta(days=30)).date(), "active",
        )
        response = client.post(f"/api/v1/tours/{tour.id}/cancel", json={"reason": "   "})
        assert response.status_code == 422

    def test_second_call_is_idempotent_with_zero_cancelled(self, client, db_session):
        base_time = REFERENCE_TIME
        venues = create_venues(db_session, count=1)
        tour = create_tour(
            db_session, "Repeat Cancel Tour", "Test Artist",
            (base_time - timedelta(days=10)).date(), (base_time + timedelta(days=30)).date(), "active",
        )
        concert = create_concert(db_session, tour, venues[0], day_offset=1, ticket_price="80.00", base_time=base_time)

        first = client.post(f"/api/v1/tours/{tour.id}/cancel", json={"reason": "Artist illness"})
        assert first.status_code == 200
        assert first.json() == {"tour_id": tour.id, "cancelled_count": 1}

        second = client.post(f"/api/v1/tours/{tour.id}/cancel", json={"reason": "Artist illness"})
        assert second.status_code == 200
        assert second.json() == {"tour_id": tour.id, "cancelled_count": 0}

        db_session.refresh(concert)
        assert concert.is_cancelled is True
        assert concert.cancellation_reason == "Artist illness"
