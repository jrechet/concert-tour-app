"""Tests for `POST /api/v1/tours/{tour_id}/cancel`.

`reference_time` is overridden to a fixed moment so "upcoming vs. past"
assertions don't depend on the real wall clock, mirroring
`tests/test_tour_date_ordering.py`.
"""

from datetime import datetime, timedelta

import pytest

from src.database import get_reference_time
from src.main import app
from tests.fixtures.dashboard_fixtures import create_concert, create_tour, create_venues

REFERENCE_TIME = datetime(2024, 6, 15, 18, 0, 0)


@pytest.fixture(autouse=True)
def frozen_reference_time():
    """Pin `get_reference_time` to `REFERENCE_TIME` for every test in this
    module, restoring whatever override (if any) was in place before."""
    previous_override = app.dependency_overrides.get(get_reference_time)
    app.dependency_overrides[get_reference_time] = lambda: REFERENCE_TIME
    yield
    if previous_override is None:
        app.dependency_overrides.pop(get_reference_time, None)
    else:
        app.dependency_overrides[get_reference_time] = previous_override


class TestCancelTourEndpoint:
    """Coverage for the bulk tour-cancellation endpoint."""

    def test_cancels_only_upcoming_uncancelled_concerts(self, client, db_session):
        base_time = REFERENCE_TIME
        venues = create_venues(db_session, count=4)
        tour = create_tour(
            db_session, "Farewell Tour", "Test Artist",
            (base_time - timedelta(days=30)).date(), (base_time + timedelta(days=30)).date(), "active",
        )
        past = create_concert(db_session, tour, venues[0], day_offset=-5, ticket_price="80.00", base_time=base_time)
        upcoming_1 = create_concert(db_session, tour, venues[1], day_offset=1, ticket_price="80.00", base_time=base_time)
        upcoming_2 = create_concert(db_session, tour, venues[2], day_offset=10, ticket_price="80.00", base_time=base_time)
        already_cancelled = create_concert(
            db_session, tour, venues[3], day_offset=5, ticket_price="80.00", base_time=base_time,
            is_cancelled=True, cancellation_reason="Prior reason",
        )

        response = client.post(
            f"/api/v1/tours/{tour.id}/cancel",
            json={"reason": "Artist illness"},
        )
        assert response.status_code == 200
        assert response.json() == {"cancelled_count": 2}

        db_session.refresh(past)
        db_session.refresh(upcoming_1)
        db_session.refresh(upcoming_2)
        db_session.refresh(already_cancelled)

        assert past.is_cancelled is False
        assert past.cancellation_reason is None

        assert upcoming_1.is_cancelled is True
        assert upcoming_1.cancellation_reason == "Artist illness"
        assert upcoming_2.is_cancelled is True
        assert upcoming_2.cancellation_reason == "Artist illness"

        assert already_cancelled.is_cancelled is True
        assert already_cancelled.cancellation_reason == "Prior reason"

    def test_cancel_tour_not_found(self, client):
        response = client.post("/api/v1/tours/999/cancel", json={"reason": "Artist illness"})
        assert response.status_code == 404

    def test_cancel_tour_missing_reason_returns_422(self, client, db_session):
        tour = create_tour(
            db_session, "No Reason Tour", "Test Artist",
            datetime(2024, 6, 1).date(), datetime(2024, 7, 1).date(), "active",
        )
        response = client.post(f"/api/v1/tours/{tour.id}/cancel", json={})
        assert response.status_code == 422

    def test_cancel_tour_blank_reason_returns_422(self, client, db_session):
        tour = create_tour(
            db_session, "Blank Reason Tour", "Test Artist",
            datetime(2024, 6, 1).date(), datetime(2024, 7, 1).date(), "active",
        )
        response = client.post(f"/api/v1/tours/{tour.id}/cancel", json={"reason": "   "})
        assert response.status_code == 422

    def test_cancel_tour_empty_string_reason_returns_422(self, client, db_session):
        tour = create_tour(
            db_session, "Empty Reason Tour", "Test Artist",
            datetime(2024, 6, 1).date(), datetime(2024, 7, 1).date(), "active",
        )
        response = client.post(f"/api/v1/tours/{tour.id}/cancel", json={"reason": ""})
        assert response.status_code == 422

    def test_cancels_concert_on_same_calendar_day_as_reference_time(self, client, db_session):
        """A concert dated the same calendar day as `reference_time` counts as
        upcoming, confirming the `>=` boundary in the date comparison."""
        base_time = REFERENCE_TIME
        venues = create_venues(db_session, count=1)
        tour = create_tour(
            db_session, "Boundary Tour", "Test Artist",
            (base_time - timedelta(days=10)).date(), (base_time + timedelta(days=10)).date(), "active",
        )
        same_day = create_concert(db_session, tour, venues[0], day_offset=0, ticket_price="80.00", base_time=base_time)

        response = client.post(
            f"/api/v1/tours/{tour.id}/cancel",
            json={"reason": "Artist illness"},
        )
        assert response.status_code == 200
        assert response.json() == {"cancelled_count": 1}

        db_session.refresh(same_day)
        assert same_day.is_cancelled is True
        assert same_day.cancellation_reason == "Artist illness"

    def test_cancel_tour_with_no_upcoming_concerts_returns_zero(self, client, db_session):
        base_time = REFERENCE_TIME
        venues = create_venues(db_session, count=1)
        tour = create_tour(
            db_session, "Already Over Tour", "Test Artist",
            (base_time - timedelta(days=60)).date(), (base_time - timedelta(days=30)).date(), "completed",
        )
        create_concert(db_session, tour, venues[0], day_offset=-40, ticket_price="80.00", base_time=base_time)

        response = client.post(f"/api/v1/tours/{tour.id}/cancel", json={"reason": "Tour ended"})
        assert response.status_code == 200
        assert response.json() == {"cancelled_count": 0}
