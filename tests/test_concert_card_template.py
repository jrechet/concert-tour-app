"""Tests for the sold-out badge rendered on the concert card template,
exercised through the public `GET /api/v1/dashboard/concerts` route rather
than any private template-rendering helper.
"""

from datetime import datetime

from src.models import Venue
from tests.fixtures.dashboard_fixtures import create_concert, create_tour, create_venues


def _make_tour(db_session, name="Badge Tour"):
    return create_tour(
        db_session,
        name=name,
        artist="Test Artist",
        start_date=datetime.now().date(),
        end_date=datetime.now().date(),
        status="active",
    )


def test_card_shows_sold_out_badge_when_no_tickets_remain(client, db_session):
    venue = create_venues(db_session, count=1)[0]
    tour = _make_tour(db_session, "Sold Out Tour")
    create_concert(
        db_session, tour, venue, day_offset=5, ticket_price="50.00",
        base_time=datetime.now(), tickets_sold=venue.capacity,
    )

    response = client.get("/api/v1/dashboard/concerts")

    assert response.status_code == 200
    assert "badge-sold-out" in response.text or "ticket-badge-sold-out" in response.text
    assert "tickets left" not in response.text


def test_card_hides_badge_when_tickets_remain(client, db_session):
    venue = create_venues(db_session, count=1)[0]
    tour = _make_tour(db_session, "Available Tour")
    create_concert(
        db_session, tour, venue, day_offset=5, ticket_price="50.00",
        base_time=datetime.now(), tickets_sold=venue.capacity - 7,
    )

    response = client.get("/api/v1/dashboard/concerts")

    assert response.status_code == 200
    assert "7 tickets left" in response.text
    assert "badge-sold-out" not in response.text and "ticket-badge-sold-out" not in response.text


def test_card_shows_almost_sold_out_badge_when_few_tickets_remain(client, db_session):
    venue = create_venues(db_session, count=1)[0]
    tour = _make_tour(db_session, "Almost Sold Out Tour")
    create_concert(
        db_session, tour, venue, day_offset=5, ticket_price="50.00",
        base_time=datetime.now(), tickets_sold=venue.capacity - 1,
    )

    response = client.get("/api/v1/dashboard/concerts")

    assert response.status_code == 200
    assert "ticket-badge-almost-sold-out" in response.text
    assert "Almost sold out!" in response.text


def test_card_hides_almost_sold_out_badge_when_plenty_of_tickets_remain(client, db_session):
    venue = create_venues(db_session, count=1)[0]
    tour = _make_tour(db_session, "Plenty Of Tickets Tour")
    create_concert(
        db_session, tour, venue, day_offset=5, ticket_price="50.00",
        base_time=datetime.now(), tickets_sold=0,
    )

    response = client.get("/api/v1/dashboard/concerts")

    assert response.status_code == 200
    assert "ticket-badge-almost-sold-out" not in response.text
    assert "Almost sold out!" not in response.text


def test_card_escapes_venue_name(client, db_session):
    venue = Venue(
        name="<script>alert('xss')</script>", city="Testville", country="USA", capacity=100,
    )
    db_session.add(venue)
    db_session.commit()
    db_session.refresh(venue)
    tour = _make_tour(db_session, "Escaping Tour")
    create_concert(db_session, tour, venue, day_offset=5, ticket_price="50.00", base_time=datetime.now())

    response = client.get("/api/v1/dashboard/concerts")

    assert response.status_code == 200
    assert "<script>alert" not in response.text
    assert "&lt;script&gt;" in response.text


def test_concert_list_page_returns_200(client, db_session):
    venue = create_venues(db_session, count=1)[0]
    tour = _make_tour(db_session, "Listing Tour")
    create_concert(db_session, tour, venue, day_offset=5, ticket_price="50.00", base_time=datetime.now())

    response = client.get("/api/v1/dashboard/concerts")

    assert response.status_code == 200
