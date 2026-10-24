"""Tests for `GET /api/v1/tours/{tour_id}/span`."""

from datetime import datetime

from tests.fixtures.dashboard_fixtures import create_concert, create_tour, create_venues

BASE_TIME = datetime(2024, 6, 15, 20, 0, 0)


class TestTourSpanEndpoint:
    """Coverage for the tour span endpoint."""

    def test_span_for_multi_concert_tour(self, client, db_session):
        venues = create_venues(db_session, count=2)
        tour = create_tour(
            db_session, "Neon Skyline World Tour", "Aurora Belle",
            BASE_TIME.date(), BASE_TIME.date(), "active",
        )
        create_concert(db_session, tour, venues[0], day_offset=0, ticket_price="80.00", base_time=BASE_TIME)
        create_concert(db_session, tour, venues[1], day_offset=10, ticket_price="120.00", base_time=BASE_TIME)
        create_concert(
            db_session, tour, venues[0], day_offset=20, ticket_price="999.00", base_time=BASE_TIME,
            is_cancelled=True, cancellation_reason="Artist illness",
        )

        response = client.get(f"/api/v1/tours/{tour.id}/span")

        assert response.status_code == 200
        data = response.json()
        assert data["first_concert_date"] == "2024-06-15"
        assert data["last_concert_date"] == "2024-06-25"
        assert data["duration_days"] == 10

    def test_span_for_tour_with_all_concerts_cancelled(self, client, db_session):
        venues = create_venues(db_session, count=1)
        tour = create_tour(
            db_session, "Cancelled Tour", "Aurora Belle",
            BASE_TIME.date(), BASE_TIME.date(), "cancelled",
        )
        create_concert(
            db_session, tour, venues[0], day_offset=0, ticket_price="80.00", base_time=BASE_TIME,
            is_cancelled=True, cancellation_reason="Artist illness",
        )

        response = client.get(f"/api/v1/tours/{tour.id}/span")

        assert response.status_code == 200
        assert response.json() == {
            "first_concert_date": None,
            "last_concert_date": None,
            "duration_days": None,
        }

    def test_span_for_single_concert_tour(self, client, db_session):
        venues = create_venues(db_session, count=1)
        tour = create_tour(
            db_session, "Solo Night Tour", "Aurora Belle",
            BASE_TIME.date(), BASE_TIME.date(), "active",
        )
        create_concert(db_session, tour, venues[0], day_offset=0, ticket_price="80.00", base_time=BASE_TIME)

        response = client.get(f"/api/v1/tours/{tour.id}/span")

        assert response.status_code == 200
        data = response.json()
        assert data["first_concert_date"] == data["last_concert_date"] == "2024-06-15"
        assert data["duration_days"] == 0

    def test_span_for_unknown_tour_returns_404(self, client):
        response = client.get("/api/v1/tours/999999/span")

        assert response.status_code == 404
        assert response.json()["detail"]

    def test_span_for_non_numeric_id_returns_422(self, client):
        response = client.get("/api/v1/tours/not-an-id/span")

        assert response.status_code == 422
