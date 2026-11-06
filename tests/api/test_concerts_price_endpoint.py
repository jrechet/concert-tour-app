"""Tests for `PATCH /api/v1/concerts/{id}/price` (issue #818)."""

from datetime import datetime
from decimal import Decimal

from tests.fixtures.dashboard_fixtures import create_concert, create_tour, create_venues

BASE_TIME = datetime(2024, 6, 15, 20, 0, 0)


def _create_concert(db_session, ticket_price="80.00", is_cancelled=False, cancellation_reason=None):
    venue = create_venues(db_session, count=1)[0]
    tour = create_tour(
        db_session, "Neon Skyline World Tour", "Aurora Belle",
        BASE_TIME.date(), BASE_TIME.date(), "active",
    )
    return create_concert(
        db_session, tour, venue, day_offset=0, ticket_price=ticket_price, base_time=BASE_TIME,
        is_cancelled=is_cancelled, cancellation_reason=cancellation_reason,
    )


class TestPatchConcertPriceEndpoint:
    """Coverage for `PATCH /api/v1/concerts/{id}/price` as a public HTTP route."""

    def test_patch_price_returns_200_and_updated_concert(self, client, db_session):
        concert = _create_concert(db_session, ticket_price="80.00")

        response = client.patch(f"/api/v1/concerts/{concert.id}/price", json={"ticket_price": "49.50"})

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == concert.id
        assert data["ticket_price"] == "49.50"

        db_session.expire_all()
        reloaded = db_session.query(type(concert)).filter(type(concert).id == concert.id).one()
        assert reloaded.ticket_price == Decimal("49.50")

    def test_patch_negative_price_returns_422(self, client, db_session):
        concert = _create_concert(db_session, ticket_price="80.00")

        response = client.patch(f"/api/v1/concerts/{concert.id}/price", json={"ticket_price": "-5.00"})

        assert response.status_code == 422

        db_session.expire_all()
        reloaded = db_session.query(type(concert)).filter(type(concert).id == concert.id).one()
        assert reloaded.ticket_price == Decimal("80.00")

    def test_patch_price_cancelled_concert_returns_409(self, client, db_session):
        concert = _create_concert(
            db_session, ticket_price="80.00", is_cancelled=True, cancellation_reason="Artist illness",
        )

        response = client.patch(f"/api/v1/concerts/{concert.id}/price", json={"ticket_price": "49.50"})

        assert response.status_code == 409

    def test_patch_price_unknown_concert_returns_404(self, client):
        response = client.patch("/api/v1/concerts/999999/price", json={"ticket_price": "49.50"})

        assert response.status_code == 404
        assert response.json() == {"detail": "Concert not found"}

    def test_patch_price_missing_field_returns_422(self, client, db_session):
        concert = _create_concert(db_session, ticket_price="80.00")

        response = client.patch(f"/api/v1/concerts/{concert.id}/price", json={})

        assert response.status_code == 422
