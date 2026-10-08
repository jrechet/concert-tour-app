"""Tests for `PATCH /api/v1/concerts/{id}/price`."""

from datetime import datetime

from tests.fixtures.dashboard_fixtures import create_concert, create_tour, create_venues

BASE_TIME = datetime(2024, 6, 15, 20, 0, 0)


class TestUpdateConcertTicketPrice:
    """Coverage for the update-ticket-price endpoint."""

    def test_update_price_on_active_concert(self, client, db_session):
        venues = create_venues(db_session, count=1)
        tour = create_tour(
            db_session, "Neon Skyline World Tour", "Aurora Belle",
            BASE_TIME.date(), BASE_TIME.date(), "active",
        )
        concert = create_concert(
            db_session, tour, venues[0], day_offset=0, ticket_price="80.00", base_time=BASE_TIME,
        )

        response = client.patch(f"/api/v1/concerts/{concert.id}/price", json={"ticket_price": "120.00"})

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == concert.id
        assert data["ticket_price"] == "120.00"

    def test_negative_price_returns_422(self, client, db_session):
        venues = create_venues(db_session, count=1)
        tour = create_tour(
            db_session, "Neon Skyline World Tour", "Aurora Belle",
            BASE_TIME.date(), BASE_TIME.date(), "active",
        )
        concert = create_concert(
            db_session, tour, venues[0], day_offset=0, ticket_price="80.00", base_time=BASE_TIME,
        )

        response = client.patch(f"/api/v1/concerts/{concert.id}/price", json={"ticket_price": "-10.00"})

        assert response.status_code == 422

    def test_unknown_concert_returns_404(self, client):
        response = client.patch("/api/v1/concerts/999999/price", json={"ticket_price": "50.00"})

        assert response.status_code == 404
        assert response.json() == {"detail": "Concert not found"}

    def test_cancelled_concert_returns_409(self, client, db_session):
        venues = create_venues(db_session, count=1)
        tour = create_tour(
            db_session, "Neon Skyline World Tour", "Aurora Belle",
            BASE_TIME.date(), BASE_TIME.date(), "active",
        )
        concert = create_concert(
            db_session, tour, venues[0], day_offset=0, ticket_price="80.00", base_time=BASE_TIME,
            is_cancelled=True, cancellation_reason="Artist illness",
        )

        response = client.patch(f"/api/v1/concerts/{concert.id}/price", json={"ticket_price": "50.00"})

        assert response.status_code == 409
