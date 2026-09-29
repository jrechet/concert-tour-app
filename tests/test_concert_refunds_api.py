"""Integration tests for `POST /api/v1/concerts/{id}/refunds`."""

from datetime import datetime

from tests.fixtures.dashboard_fixtures import create_concert, create_tour, create_venues

BASE_TIME = datetime(2024, 6, 15, 20, 0, 0)


def _make_tour(db_session, name="Refund Tour"):
    return create_tour(
        db_session, name, "Test Artist", BASE_TIME.date(), BASE_TIME.date(), "active",
    )


def test_refund_tickets_returns_updated_concert(client, db_session):
    venue = create_venues(db_session, count=1)[0]
    tour = _make_tour(db_session)
    concert = create_concert(
        db_session, tour, venue, day_offset=0, ticket_price="80.00",
        base_time=BASE_TIME, tickets_sold=10,
    )

    response = client.post(f"/api/v1/concerts/{concert.id}/refunds", json={"quantity": 4})

    assert response.status_code == 200
    body = response.json()
    assert body["tickets_sold"] == 6
    assert body["remaining_tickets"] == venue.capacity - 6


def test_refund_tickets_on_nonexistent_concert_returns_404(client, db_session):
    response = client.post("/api/v1/concerts/999999/refunds", json={"quantity": 1})

    assert response.status_code == 404


def test_refund_tickets_beyond_sold_returns_409(client, db_session):
    venue = create_venues(db_session, count=1)[0]
    tour = _make_tour(db_session, "Over Refund Tour")
    concert = create_concert(
        db_session, tour, venue, day_offset=0, ticket_price="80.00",
        base_time=BASE_TIME, tickets_sold=5,
    )

    response = client.post(f"/api/v1/concerts/{concert.id}/refunds", json={"quantity": 6})

    assert response.status_code == 409


def test_refund_tickets_with_zero_quantity_returns_422(client, db_session):
    venue = create_venues(db_session, count=1)[0]
    tour = _make_tour(db_session, "Invalid Refund Quantity Tour")
    concert = create_concert(
        db_session, tour, venue, day_offset=0, ticket_price="80.00",
        base_time=BASE_TIME, tickets_sold=5,
    )

    response = client.post(f"/api/v1/concerts/{concert.id}/refunds", json={"quantity": 0})

    assert response.status_code == 422


def test_refund_tickets_with_negative_quantity_returns_422(client, db_session):
    venue = create_venues(db_session, count=1)[0]
    tour = _make_tour(db_session, "Negative Refund Quantity Tour")
    concert = create_concert(
        db_session, tour, venue, day_offset=0, ticket_price="80.00",
        base_time=BASE_TIME, tickets_sold=5,
    )

    response = client.post(f"/api/v1/concerts/{concert.id}/refunds", json={"quantity": -1})

    assert response.status_code == 422


def test_refund_tickets_endpoint_rejects_get(client, db_session):
    venue = create_venues(db_session, count=1)[0]
    tour = _make_tour(db_session, "Method Not Allowed Tour")
    concert = create_concert(
        db_session, tour, venue, day_offset=0, ticket_price="80.00",
        base_time=BASE_TIME, tickets_sold=5,
    )

    response = client.get(f"/api/v1/concerts/{concert.id}/refunds")

    assert response.status_code == 405
