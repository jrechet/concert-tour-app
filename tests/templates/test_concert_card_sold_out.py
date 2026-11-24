"""Tests for the sold-out badge rendered on the concert card
(`src/templates/_concert_card.html`), exercised through the public
`GET /api/v1/dashboard/concerts` route rather than any private
template-rendering helper.
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


def test_card_shows_badge_when_sold_out(client, db_session):
    venue = create_venues(db_session, count=1)[0]
    tour = _make_tour(db_session, "Sold Out Tour")
    create_concert(
        db_session, tour, venue, day_offset=5, ticket_price="50.00",
        base_time=datetime.now(), tickets_sold=venue.capacity,
    )

    response = client.get("/api/v1/dashboard/concerts")

    assert response.status_code == 200
    assert response.text.count('data-testid="sold-out-badge"') == 1
    assert "Sold Out" in response.text


def test_card_hides_badge_when_tickets_remain(client, db_session):
    venue = create_venues(db_session, count=1)[0]
    tour = _make_tour(db_session, "Available Tour")
    create_concert(
        db_session, tour, venue, day_offset=5, ticket_price="50.00",
        base_time=datetime.now(), tickets_sold=venue.capacity - 7,
    )

    response = client.get("/api/v1/dashboard/concerts")

    assert response.status_code == 200
    assert 'data-testid="sold-out-badge"' not in response.text


def test_list_page_badges_only_sold_out_concerts(client, db_session):
    venues = create_venues(db_session, count=2)
    tour = _make_tour(db_session, "Mixed Availability Tour")
    create_concert(
        db_session, tour, venues[0], day_offset=5, ticket_price="50.00",
        base_time=datetime.now(), tickets_sold=venues[0].capacity,
    )
    create_concert(
        db_session, tour, venues[1], day_offset=10, ticket_price="50.00",
        base_time=datetime.now(), tickets_sold=venues[1].capacity - 10,
    )

    response = client.get("/api/v1/dashboard/concerts")

    assert response.status_code == 200
    assert response.text.count('data-testid="sold-out-badge"') == 1


def test_concert_title_is_escaped_in_card(client, db_session):
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
