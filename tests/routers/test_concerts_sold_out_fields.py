"""Tests for the `tickets_remaining`/`is_sold_out` fields on the concert
read schema, surfaced by `GET /api/v1/concerts` and
`GET /api/v1/concerts/{id}`.

Uses real venue/tour fixtures persisted via the ORM so every foreign key is
a genuine committed id, not a hardcoded literal like venue_id=1.
"""

from datetime import datetime, timedelta

from tests.fixtures.dashboard_fixtures import create_concert, create_tour, create_venues


def _seed_concert(db_session, tickets_sold=0):
    tour = create_tour(
        db_session,
        name="Sold Out Fields Tour",
        artist="Test Artist",
        start_date=(datetime.now() - timedelta(days=1)).date(),
        end_date=(datetime.now() + timedelta(days=90)).date(),
        status="active",
    )
    venue = create_venues(db_session, count=1)[0]
    concert = create_concert(
        db_session, tour, venue, day_offset=5, ticket_price="50.00",
        base_time=datetime.now(), tickets_sold=tickets_sold,
    )
    return concert, venue


def test_get_concert_returns_sold_out_false_with_tickets(client, db_session):
    concert, venue = _seed_concert(db_session, tickets_sold=10)

    response = client.get(f"/api/v1/concerts/{concert.id}")

    assert response.status_code == 200
    data = response.json()
    assert data["tickets_remaining"] == venue.capacity - 10
    assert data["is_sold_out"] is False


def test_get_concert_returns_sold_out_true_when_none_remain(client, db_session):
    concert, venue = _seed_concert(db_session, tickets_sold=0)
    concert.tickets_sold = venue.capacity
    db_session.commit()
    db_session.refresh(concert)

    response = client.get(f"/api/v1/concerts/{concert.id}")

    assert response.status_code == 200
    data = response.json()
    assert data["tickets_remaining"] == 0
    assert data["is_sold_out"] is True


def test_list_concerts_includes_sold_out_fields(client, db_session):
    _seed_concert(db_session, tickets_sold=5)

    response = client.get("/api/v1/concerts")

    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    for item in data:
        assert "tickets_remaining" in item
        assert "is_sold_out" in item


def test_get_unknown_concert_returns_404(client, db_session):
    response = client.get("/api/v1/concerts/999999")

    assert response.status_code == 404


def test_sold_out_field_is_read_only(client, db_session):
    concert, venue = _seed_concert(db_session, tickets_sold=10)

    response = client.patch(
        f"/api/v1/concerts/{concert.id}",
        json={
            "date_time": (datetime.now() + timedelta(days=20)).isoformat(),
            "is_sold_out": True,
            "tickets_remaining": 0,
        },
    )

    assert response.status_code == 422

    db_session.refresh(concert)
    assert concert.tickets_sold == 10
