"""Tests for the remaining-ticket count rendered on the concert list page
(`GET /concerts`): the numeric count, the sold-out and low-stock badges,
venue-name escaping, and the existing empty-state message.
"""

from datetime import datetime, timedelta

from src.config import LOW_STOCK_THRESHOLD
from src.models import Venue
from tests.fixtures.dashboard_fixtures import create_concert, create_tour, create_venues


def _make_tour(db_session, name="Template Tour"):
    return create_tour(
        db_session,
        name=name,
        artist="Test Artist",
        start_date=(datetime.now() - timedelta(days=1)).date(),
        end_date=(datetime.now() + timedelta(days=90)).date(),
        status="active",
    )


def test_page_shows_remaining_count_for_partially_sold_concert(client, db_session):
    venue = create_venues(db_session, count=1)[0]
    tour = _make_tour(db_session, "Partially Sold Tour")
    create_concert(
        db_session, tour, venue, day_offset=5, ticket_price="50.00",
        base_time=datetime.now(), tickets_sold=venue.capacity - 500,
    )

    response = client.get("/concerts")

    assert response.status_code == 200
    assert "500 tickets left" in response.text


def test_sold_out_concert_shows_indicator_not_zero_left(client, db_session):
    venue = create_venues(db_session, count=1)[0]
    tour = _make_tour(db_session, "Sold Out Tour")
    create_concert(
        db_session, tour, venue, day_offset=5, ticket_price="50.00",
        base_time=datetime.now(), tickets_sold=venue.capacity,
    )

    response = client.get("/concerts")

    assert response.status_code == 200
    assert "Sold out" in response.text
    assert "0 tickets left" not in response.text


def test_low_stock_concert_renders_low_stock_class(client, db_session):
    venue = create_venues(db_session, count=1)[0]
    tour = _make_tour(db_session, "Low Stock Tour")
    create_concert(
        db_session, tour, venue, day_offset=5, ticket_price="50.00",
        base_time=datetime.now(), tickets_sold=venue.capacity - LOW_STOCK_THRESHOLD,
    )

    response = client.get("/concerts")

    assert response.status_code == 200
    assert "ticket-badge-low-stock" in response.text


def test_concert_above_low_stock_threshold_renders_normal_badge(client, db_session):
    venue = create_venues(db_session, count=1)[0]
    tour = _make_tour(db_session, "Plenty Left Tour")
    create_concert(
        db_session, tour, venue, day_offset=5, ticket_price="50.00",
        base_time=datetime.now(), tickets_sold=venue.capacity - (LOW_STOCK_THRESHOLD + 1),
    )

    response = client.get("/concerts")

    assert response.status_code == 200
    assert "ticket-badge-low-stock" not in response.text
    assert f"{LOW_STOCK_THRESHOLD + 1} tickets left" in response.text


def test_concert_name_with_script_tag_is_escaped(client, db_session):
    venue = Venue(
        name="<script>alert('xss')</script>", city="Testville", country="USA", capacity=100,
    )
    db_session.add(venue)
    db_session.commit()
    db_session.refresh(venue)
    tour = _make_tour(db_session, "Escaping Tour")
    create_concert(db_session, tour, venue, day_offset=5, ticket_price="50.00", base_time=datetime.now())

    response = client.get("/concerts")

    assert response.status_code == 200
    assert "<script>alert" not in response.text
    assert "&lt;script&gt;" in response.text


def test_empty_concert_list_shows_existing_empty_state_message(client):
    response = client.get("/concerts")

    assert response.status_code == 200
    assert "No concerts scheduled yet." in response.text
