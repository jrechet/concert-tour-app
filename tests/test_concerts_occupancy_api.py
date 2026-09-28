"""Tests for GET /api/v1/concerts/{concert_id}/occupancy: known capacity,
unknown/null capacity, and the 404-for-missing-concert case.

Uses real venue/tour/concert fixtures persisted via the ORM so every foreign
key (concert_id) is a genuine committed id, not a hardcoded literal.
"""

from datetime import datetime

from tests.fixtures.dashboard_fixtures import create_concert, create_tour, create_venues

BASE_TIME = datetime(2026, 11, 1, 20, 0, 0)


def _build_concert(db_session, tickets_sold, capacity):
    venue = create_venues(db_session, count=1)[0]
    venue.capacity = capacity
    db_session.commit()
    tour = create_tour(
        db_session,
        name="Test Tour",
        artist="Test Artist",
        start_date=BASE_TIME.date(),
        end_date=BASE_TIME.date(),
        status="planned",
    )
    return create_concert(
        db_session, tour, venue, day_offset=0, ticket_price="50.00",
        base_time=BASE_TIME, tickets_sold=tickets_sold,
    )


def test_occupancy_endpoint_returns_correct_percentage_for_known_capacity(client, db_session):
    concert = _build_concert(db_session, tickets_sold=15000, capacity=20000)

    response = client.get(f"/api/v1/concerts/{concert.id}/occupancy")

    assert response.status_code == 200
    data = response.json()
    assert data["concert_id"] == concert.id
    assert data["tickets_sold"] == 15000
    assert data["capacity"] == 20000
    assert data["percentage_sold"] == 75.0


def test_occupancy_endpoint_returns_null_fields_for_unknown_capacity(client, db_session):
    concert = _build_concert(db_session, tickets_sold=500, capacity=None)

    response = client.get(f"/api/v1/concerts/{concert.id}/occupancy")

    assert response.status_code == 200
    data = response.json()
    assert data["concert_id"] == concert.id
    assert data["tickets_sold"] == 500
    assert data["capacity"] is None
    assert data["percentage_sold"] is None


def test_occupancy_endpoint_returns_404_for_nonexistent_concert(client, db_session):
    _build_concert(db_session, tickets_sold=100, capacity=1000)
    nonexistent_id = 999999

    response = client.get(f"/api/v1/concerts/{nonexistent_id}/occupancy")

    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()
