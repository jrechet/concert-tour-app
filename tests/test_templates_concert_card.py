"""Tests for the sold-out badge on the concert card, exercised through the
public `GET /api/v1/dashboard/concerts` route that embeds `_concert_card.html`
rather than any private template-rendering helper.
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


def test_card_renders_sold_out_badge_when_no_tickets_remain(client, db_session):
    venue = create_venues(db_session, count=1)[0]
    tour = _make_tour(db_session, "Sold Out Tour")
    create_concert(
        db_session, tour, venue, day_offset=5, ticket_price="50.00",
        base_time=datetime.now(), tickets_sold=venue.capacity,
    )

    response = client.get("/api/v1/dashboard/concerts")

    assert response.status_code == 200
    assert response.text.count('data-testid="sold-out-badge"') == 1
    assert venue.name in response.text


def test_card_omits_badge_when_tickets_remain(client, db_session):
    venue = create_venues(db_session, count=1)[0]
    tour = _make_tour(db_session, "Available Tour")
    create_concert(
        db_session, tour, venue, day_offset=5, ticket_price="50.00",
        base_time=datetime.now(), tickets_sold=venue.capacity - 7,
    )

    response = client.get("/api/v1/dashboard/concerts")

    assert response.status_code == 200
    assert 'data-testid="sold-out-badge"' not in response.text
    assert venue.name in response.text


def test_card_omits_badge_when_inventory_unknown(client, db_session):
    venue = Venue(name="Unknown Capacity Hall", city="Testville", country="USA", capacity=None)
    db_session.add(venue)
    db_session.commit()
    db_session.refresh(venue)
    tour = _make_tour(db_session, "Mystery Tour")
    create_concert(db_session, tour, venue, day_offset=5, ticket_price="40.00", base_time=datetime.now())

    response = client.get("/api/v1/dashboard/concerts")

    assert response.status_code == 200
    assert 'data-testid="sold-out-badge"' not in response.text
    assert venue.name in response.text


def test_card_escapes_concert_title(client, db_session):
    venue = Venue(
        name="<script>alert('xss')</script>", city="Testville", country="USA", capacity=100,
    )
    db_session.add(venue)
    db_session.commit()
    db_session.refresh(venue)
    tour = _make_tour(db_session, "XSS Tour")
    create_concert(db_session, tour, venue, day_offset=5, ticket_price="50.00", base_time=datetime.now())

    response = client.get("/api/v1/dashboard/concerts")

    assert response.status_code == 200
    assert "<script>alert" not in response.text
    assert "&lt;script&gt;" in response.text
