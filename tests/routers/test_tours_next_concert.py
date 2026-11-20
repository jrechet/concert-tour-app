"""Tests for `GET /api/v1/tours/{tour_id}/next`."""

from datetime import datetime

from src.models import ConcertStatus
from tests.fixtures.dashboard_fixtures import create_concert, create_tour, create_venues

BASE_TIME = datetime(2024, 6, 15, 20, 0, 0)


def _patch_now(monkeypatch, now=BASE_TIME):
    monkeypatch.setattr("src.services.tour_service.get_reference_time", lambda: now)


class TestTourNextConcertEndpoint:
    """Coverage for `GET /api/v1/tours/{tour_id}/next`."""

    def test_returns_next_concert_with_venue_details(self, client, db_session, monkeypatch):
        _patch_now(monkeypatch)
        venues = create_venues(db_session, count=2)
        tour = create_tour(
            db_session, "Neon Skyline World Tour", "Aurora Belle",
            BASE_TIME.date(), BASE_TIME.date(), "active",
        )
        create_concert(
            db_session, tour, venues[0], day_offset=10, ticket_price="80.00",
            base_time=BASE_TIME, tickets_sold=100,
        )
        earliest = create_concert(
            db_session, tour, venues[1], day_offset=1, ticket_price="80.00",
            base_time=BASE_TIME, tickets_sold=18000,
        )

        response = client.get(f"/api/v1/tours/{tour.id}/next")

        assert response.status_code == 200
        assert response.json() == {
            "concert_id": earliest.id,
            "date": earliest.date_time.isoformat(),
            "venue_name": venues[1].name,
            "venue_city": venues[1].city,
            "tickets_remaining": venues[1].capacity - 18000,
        }

    def test_cancelled_earliest_concert_is_skipped(self, client, db_session, monkeypatch):
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

        response = client.get(f"/api/v1/tours/{tour.id}/next")

        assert response.status_code == 200
        data = response.json()
        assert data["concert_id"] == next_valid.id
        assert data["date"] == next_valid.date_time.isoformat()

    def test_unknown_tour_returns_404_with_detail(self, client):
        response = client.get("/api/v1/tours/999999/next")

        assert response.status_code == 404
        assert response.json() == {"detail": "Tour 999999 not found"}

    def test_past_and_cancelled_only_returns_404_with_detail(self, client, db_session, monkeypatch):
        _patch_now(monkeypatch)
        venues = create_venues(db_session, count=2)
        tour = create_tour(
            db_session, "River Stone Farewell Tour", "River Stone",
            BASE_TIME.date(), BASE_TIME.date(), "completed",
        )
        create_concert(
            db_session, tour, venues[0], day_offset=-1, ticket_price="65.00", base_time=BASE_TIME,
        )
        upcoming_cancelled = create_concert(
            db_session, tour, venues[1], day_offset=1, ticket_price="65.00",
            base_time=BASE_TIME, is_cancelled=True, cancellation_reason="Artist illness",
        )
        upcoming_cancelled.status = ConcertStatus.cancelled
        db_session.commit()

        response = client.get(f"/api/v1/tours/{tour.id}/next")

        assert response.status_code == 404
        assert response.json() == {"detail": f"Tour {tour.id} has no upcoming concert"}

    def test_tour_with_no_concerts_returns_404_with_detail(self, client, db_session, monkeypatch):
        _patch_now(monkeypatch)
        tour = create_tour(
            db_session, "Unannounced Tour", "TBD Collective",
            BASE_TIME.date(), BASE_TIME.date(), "planned",
        )

        response = client.get(f"/api/v1/tours/{tour.id}/next")

        assert response.status_code == 404
        assert response.json() == {"detail": f"Tour {tour.id} has no upcoming concert"}

    def test_non_integer_tour_id_returns_422(self, client):
        response = client.get("/api/v1/tours/abc/next")

        assert response.status_code == 422

    def test_route_appears_in_openapi_schema_with_both_404_cases(self, client):
        schema = client.get("/openapi.json").json()
        next_route = schema["paths"]["/api/v1/tours/{tour_id}/next"]["get"]

        assert "404" in next_route["responses"]
        examples = next_route["responses"]["404"]["content"]["application/json"]["examples"]
        assert examples["tour_not_found"]["value"]["detail"] == "Tour 999 not found"
        assert examples["no_upcoming_concert"]["value"]["detail"] == "Tour 999 has no upcoming concert"
