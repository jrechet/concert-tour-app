"""Integration tests for `POST /api/v1/concerts/{id}/tickets`."""

from datetime import datetime

from tests.fixtures.dashboard_fixtures import create_concert, create_tour, create_venues

BASE_TIME = datetime(2024, 6, 15, 20, 0, 0)


def _make_tour(db_session, name="Ticket Sale Tour"):
    return create_tour(
        db_session, name, "Test Artist", BASE_TIME.date(), BASE_TIME.date(), "active",
    )


def test_buy_tickets_returns_updated_concert(client, db_session):
    venue = create_venues(db_session, count=1)[0]
    tour = _make_tour(db_session)
    concert = create_concert(
        db_session, tour, venue, day_offset=0, ticket_price="80.00",
        base_time=BASE_TIME, tickets_sold=10,
    )

    response = client.post(f"/api/v1/concerts/{concert.id}/tickets", json={"quantity": 5})

    assert response.status_code == 200
    body = response.json()
    assert body["tickets_sold"] == 15
    assert body["remaining_tickets"] == venue.capacity - 15


def test_buy_tickets_on_nonexistent_concert_returns_404(client, db_session):
    response = client.post("/api/v1/concerts/999999/tickets", json={"quantity": 1})

    assert response.status_code == 404


def test_buy_tickets_on_cancelled_concert_returns_409(client, db_session):
    venue = create_venues(db_session, count=1)[0]
    tour = _make_tour(db_session, "Cancelled Ticket Tour")
    concert = create_concert(
        db_session, tour, venue, day_offset=0, ticket_price="80.00",
        base_time=BASE_TIME, tickets_sold=10,
        is_cancelled=True, cancellation_reason="Weather",
    )

    response = client.post(f"/api/v1/concerts/{concert.id}/tickets", json={"quantity": 1})

    assert response.status_code == 409


def test_buy_tickets_beyond_capacity_returns_409(client, db_session):
    venue = create_venues(db_session, count=1)[0]
    tour = _make_tour(db_session, "Over Capacity Ticket Tour")
    concert = create_concert(
        db_session, tour, venue, day_offset=0, ticket_price="80.00",
        base_time=BASE_TIME, tickets_sold=venue.capacity - 5,
    )

    response = client.post(f"/api/v1/concerts/{concert.id}/tickets", json={"quantity": 6})

    assert response.status_code == 409


def test_buy_tickets_with_zero_quantity_returns_422(client, db_session):
    venue = create_venues(db_session, count=1)[0]
    tour = _make_tour(db_session, "Invalid Quantity Tour")
    concert = create_concert(
        db_session, tour, venue, day_offset=0, ticket_price="80.00",
        base_time=BASE_TIME, tickets_sold=0,
    )

    response = client.post(f"/api/v1/concerts/{concert.id}/tickets", json={"quantity": 0})

    assert response.status_code == 422
