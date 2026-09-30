"""Tests for `GET /api/v1/tours/{tour_id}/occupancy`."""

from datetime import datetime

from tests.fixtures.dashboard_fixtures import create_concert, create_tour, create_venues

BASE_TIME = datetime(2024, 6, 15, 20, 0, 0)


class TestTourOccupancyEndpoint:
    """Coverage for the tour occupancy endpoint."""

    def test_occupancy_for_tour_with_concerts(self, client, db_session):
        venues = create_venues(db_session, count=2)
        tour = create_tour(
            db_session, "Neon Skyline World Tour", "Aurora Belle",
            BASE_TIME.date(), BASE_TIME.date(), "active",
        )
        create_concert(
            db_session, tour, venues[0], day_offset=0, ticket_price="80.00",
            base_time=BASE_TIME, tickets_sold=15000,
        )
        create_concert(
            db_session, tour, venues[1], day_offset=1, ticket_price="120.00",
            base_time=BASE_TIME, tickets_sold=9000,
        )

        response = client.get(f"/api/v1/tours/{tour.id}/occupancy")

        assert response.status_code == 200
        data = response.json()
        expected_capacity = venues[0].capacity + venues[1].capacity
        assert data == {
            "tickets_sold": 24000,
            "total_capacity": expected_capacity,
            "percentage_sold": round(24000 / expected_capacity * 100, 2),
        }
        assert isinstance(data["tickets_sold"], int)
        assert isinstance(data["total_capacity"], int)
        assert isinstance(data["percentage_sold"], float)

    def test_occupancy_not_found(self, client):
        response = client.get("/api/v1/tours/999999/occupancy")
        assert response.status_code == 404
        assert response.json() == {"detail": "Tour not found"}

    def test_occupancy_for_tour_with_only_cancelled_concerts(self, client, db_session):
        venues = create_venues(db_session, count=1)
        tour = create_tour(
            db_session, "Cancelled Tour", "Aurora Belle",
            BASE_TIME.date(), BASE_TIME.date(), "cancelled",
        )
        create_concert(
            db_session, tour, venues[0], day_offset=0, ticket_price="80.00",
            base_time=BASE_TIME, tickets_sold=15000,
            is_cancelled=True, cancellation_reason="Artist illness",
        )

        response = client.get(f"/api/v1/tours/{tour.id}/occupancy")

        assert response.status_code == 200
        data = response.json()
        assert data == {
            "tickets_sold": 0,
            "total_capacity": 0,
            "percentage_sold": 0.0,
        }

    def test_cancelled_concerts_excluded_from_mixed_tour(self, client, db_session):
        venues = create_venues(db_session, count=2)
        tour = create_tour(
            db_session, "Mixed Tour", "Aurora Belle",
            BASE_TIME.date(), BASE_TIME.date(), "active",
        )
        create_concert(
            db_session, tour, venues[0], day_offset=0, ticket_price="80.00",
            base_time=BASE_TIME, tickets_sold=15000,
        )
        create_concert(
            db_session, tour, venues[1], day_offset=1, ticket_price="120.00",
            base_time=BASE_TIME, tickets_sold=9000,
            is_cancelled=True, cancellation_reason="Artist illness",
        )

        response = client.get(f"/api/v1/tours/{tour.id}/occupancy")

        assert response.status_code == 200
        data = response.json()
        assert data["tickets_sold"] == 15000
        assert data["total_capacity"] == venues[0].capacity
        assert data["percentage_sold"] == round(15000 / venues[0].capacity * 100, 2)
