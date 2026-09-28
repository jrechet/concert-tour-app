"""Tests for `GET /api/v1/tours/{tour_id}/revenue`."""

from datetime import datetime

from tests.fixtures.dashboard_fixtures import create_concert, create_tour, create_venues

BASE_TIME = datetime(2024, 6, 15, 20, 0, 0)


class TestTourRevenueEndpoint:
    """Coverage for the tour revenue endpoint."""

    def test_revenue_for_tour_with_concerts(self, client, db_session):
        venues = create_venues(db_session, count=2)
        tour = create_tour(
            db_session, "Neon Skyline World Tour", "Aurora Belle",
            BASE_TIME.date(), BASE_TIME.date(), "active",
        )
        create_concert(
            db_session, tour, venues[0], day_offset=0, ticket_price="80.00",
            base_time=BASE_TIME, tickets_sold=100,
        )
        create_concert(
            db_session, tour, venues[1], day_offset=1, ticket_price="120.00",
            base_time=BASE_TIME, tickets_sold=50,
        )
        create_concert(
            db_session, tour, venues[0], day_offset=2, ticket_price="999.00",
            base_time=BASE_TIME, tickets_sold=200,
            is_cancelled=True, cancellation_reason="Artist illness",
        )

        response = client.get(f"/api/v1/tours/{tour.id}/revenue")
        assert response.status_code == 200
        data = response.json()
        # 3 concerts were created, but 1 is cancelled, so it must not count.
        assert data["concert_count"] == 2
        assert float(data["revenue"]) == 80.00 * 100 + 120.00 * 50

    def test_revenue_for_tour_with_no_concerts(self, client, empty_tour):
        tour = empty_tour["tour"]

        response = client.get(f"/api/v1/tours/{tour.id}/revenue")
        assert response.status_code == 200
        data = response.json()
        assert float(data["revenue"]) == 0
        assert data["concert_count"] == 0

    def test_revenue_not_found(self, client):
        response = client.get("/api/v1/tours/999999/revenue")
        assert response.status_code == 404
        assert response.json() == {"detail": "Tour not found"}
