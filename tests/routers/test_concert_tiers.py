"""Tests for `GET /api/v1/concerts/{concert_id}/tiers`: ordering, the
empty-list and unknown-concert cases, cross-concert isolation, and
tie-break stability for equal prices."""

from datetime import datetime
from decimal import Decimal

from src.models import TicketTier
from tests.fixtures.dashboard_fixtures import create_concert, create_tour, create_venues


def _build_concert(db_session, name="Test Tour", artist="Test Artist"):
    base_time = datetime(2026, 11, 1, 20, 0, 0)
    venue = create_venues(db_session, count=1)[0]
    tour = create_tour(
        db_session,
        name=name,
        artist=artist,
        start_date=base_time.date(),
        end_date=base_time.date(),
        status="planned",
    )
    return create_concert(
        db_session, tour, venue, day_offset=0, ticket_price="50.00", base_time=base_time
    )


def test_tiers_are_returned_cheapest_first(client, db_session):
    concert = _build_concert(db_session)
    db_session.add_all(
        [
            TicketTier(concert_id=concert.id, name="VIP", price=Decimal("120.00")),
            TicketTier(concert_id=concert.id, name="General Admission", price=Decimal("45.00")),
            TicketTier(concert_id=concert.id, name="Premium", price=Decimal("80.00")),
        ]
    )
    db_session.commit()

    response = client.get(f"/api/v1/concerts/{concert.id}/tiers")

    assert response.status_code == 200
    body = response.json()
    assert [tier["name"] for tier in body] == ["General Admission", "Premium", "VIP"]
    assert [tier["price"] for tier in body] == ["45.00", "80.00", "120.00"]


def test_concert_with_no_tiers_returns_empty_list(client, db_session):
    concert = _build_concert(db_session)

    response = client.get(f"/api/v1/concerts/{concert.id}/tiers")

    assert response.status_code == 200
    assert response.json() == []


def test_unknown_concert_returns_404(client):
    response = client.get("/api/v1/concerts/999999/tiers")

    assert response.status_code == 404
    assert response.json()["detail"] == "Concert not found"


def test_tiers_from_another_concert_do_not_leak(client, db_session):
    concert_a = _build_concert(db_session, name="Tour A", artist="Artist A")
    concert_b = _build_concert(db_session, name="Tour B", artist="Artist B")
    db_session.add_all(
        [
            TicketTier(concert_id=concert_a.id, name="GA", price=Decimal("30.00")),
            TicketTier(concert_id=concert_b.id, name="VIP", price=Decimal("200.00")),
        ]
    )
    db_session.commit()

    response = client.get(f"/api/v1/concerts/{concert_a.id}/tiers")

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["name"] == "GA"


def test_equal_prices_break_ties_by_id(client, db_session):
    concert = _build_concert(db_session)
    first = TicketTier(concert_id=concert.id, name="Early Bird", price=Decimal("60.00"))
    second = TicketTier(concert_id=concert.id, name="Standard", price=Decimal("60.00"))
    db_session.add(first)
    db_session.commit()
    db_session.add(second)
    db_session.commit()

    response = client.get(f"/api/v1/concerts/{concert.id}/tiers")

    assert response.status_code == 200
    body = response.json()
    assert [tier["name"] for tier in body] == ["Early Bird", "Standard"]
    assert body[0]["id"] < body[1]["id"]
