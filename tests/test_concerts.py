"""Tests for the concert list/detail JSON API endpoints."""

from datetime import datetime, timedelta
from decimal import Decimal

from tests.fixtures.dashboard_fixtures import create_concert, create_tour, create_venues


def _seed_tour_and_venue(db_session):
    tour = create_tour(
        db_session,
        name="Test Tour",
        artist="Test Artist",
        start_date=(datetime.now() - timedelta(days=1)).date(),
        end_date=(datetime.now() + timedelta(days=90)).date(),
        status="active",
    )
    venue = create_venues(db_session, count=1)[0]
    return tour, venue


def test_get_concerts_includes_remaining_tickets_and_sold_out(client, db_session):
    """Every concert in the list response carries the derived fields."""
    tour, venue = _seed_tour_and_venue(db_session)
    create_concert(
        db_session, tour, venue, day_offset=10, ticket_price="50.00",
        base_time=datetime.now(), tickets_sold=100,
    )

    response = client.get("/api/v1/concerts/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["remaining_tickets"] == venue.capacity - 100
    assert data[0]["sold_out"] is False
    assert data[0]["tickets_sold"] == 100


def test_get_concerts_sold_out_when_zero_remaining(client, db_session):
    """A concert with tickets_sold == venue capacity reports sold_out."""
    tour, venue = _seed_tour_and_venue(db_session)
    create_concert(
        db_session, tour, venue, day_offset=10, ticket_price="50.00",
        base_time=datetime.now(), tickets_sold=venue.capacity,
    )

    response = client.get("/api/v1/concerts/")
    data = response.json()[0]
    assert data["remaining_tickets"] == 0
    assert data["sold_out"] is True


def test_get_concerts_pagination(client, db_session):
    """skip/limit continue to page results with the added fields present."""
    tour, venue = _seed_tour_and_venue(db_session)
    base_time = datetime.now()
    for i in range(5):
        create_concert(
            db_session, tour, venue, day_offset=i, ticket_price="50.00",
            base_time=base_time, tickets_sold=i,
        )

    response = client.get("/api/v1/concerts/?skip=2&limit=2")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    for concert in data:
        assert "remaining_tickets" in concert
        assert "sold_out" in concert


def test_get_concerts_empty(client):
    """An empty database returns an empty list, not an error."""
    response = client.get("/api/v1/concerts/")
    assert response.status_code == 200
    assert response.json() == []


def test_get_concert_by_id(client, db_session):
    """Fetching a single concert includes the derived fields too."""
    tour, venue = _seed_tour_and_venue(db_session)
    concert = create_concert(
        db_session, tour, venue, day_offset=10, ticket_price="50.00",
        base_time=datetime.now(), tickets_sold=venue.capacity,
    )

    response = client.get(f"/api/v1/concerts/{concert.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == concert.id
    assert data["sold_out"] is True
    assert data["remaining_tickets"] == 0


def test_get_concert_not_found(client):
    """Requesting a nonexistent concert returns 404."""
    response = client.get("/api/v1/concerts/999")
    assert response.status_code == 404
