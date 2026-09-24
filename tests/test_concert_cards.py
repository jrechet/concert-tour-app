"""Tests for Concert ticket-availability properties and the dashboard
concert-card endpoint/template (remaining count + sold-out badge)."""

from datetime import datetime, timedelta

from src.models import Concert, Venue
from tests.fixtures.dashboard_fixtures import create_concert, create_tour, create_venues


def _make_tour(db_session, name="Test Tour"):
    return create_tour(
        db_session,
        name=name,
        artist="Test Artist",
        start_date=datetime.now().date(),
        end_date=(datetime.now() + timedelta(days=30)).date(),
        status="planned",
    )


def test_remaining_tickets_subtracts_sold_from_venue_capacity(db_session):
    venue = Venue(name="Test Arena", city="Testville", country="USA", capacity=100)
    db_session.add(venue)
    db_session.commit()
    db_session.refresh(venue)
    tour = _make_tour(db_session)

    concert = create_concert(
        db_session, tour, venue, day_offset=10, ticket_price="50.00",
        base_time=datetime.now(), tickets_sold=40,
    )

    assert concert.remaining_tickets == 60
    assert concert.sold_out is False


def test_sold_out_when_tickets_sold_meets_capacity(db_session):
    venue = Venue(name="Small Club", city="Testville", country="USA", capacity=50)
    db_session.add(venue)
    db_session.commit()
    db_session.refresh(venue)
    tour = _make_tour(db_session, "Sellout Tour")

    concert = create_concert(
        db_session, tour, venue, day_offset=5, ticket_price="75.00",
        base_time=datetime.now(), tickets_sold=50,
    )

    assert concert.remaining_tickets == 0
    assert concert.sold_out is True


def test_remaining_tickets_is_none_without_venue_capacity(db_session):
    venue = Venue(name="Unknown Capacity Hall", city="Testville", country="USA", capacity=None)
    db_session.add(venue)
    db_session.commit()
    db_session.refresh(venue)
    tour = _make_tour(db_session, "Mystery Tour")

    concert = create_concert(
        db_session, tour, venue, day_offset=5, ticket_price="40.00", base_time=datetime.now(),
    )

    assert concert.remaining_tickets is None
    assert concert.sold_out is False


def test_tickets_sold_defaults_to_zero(db_session):
    venue = Venue(name="Default Hall", city="Testville", country="USA", capacity=200)
    db_session.add(venue)
    db_session.commit()
    db_session.refresh(venue)
    tour = _make_tour(db_session, "Default Tour")

    concert = Concert(tour_id=tour.id, venue_id=venue.id, date_time=datetime.now() + timedelta(days=5))
    db_session.add(concert)
    db_session.commit()
    db_session.refresh(concert)

    assert concert.tickets_sold == 0
    assert concert.remaining_tickets == 200


def test_dashboard_concerts_endpoint_shows_remaining_count(client, db_session):
    venue = create_venues(db_session, count=1)[0]
    tour = _make_tour(db_session, "Card Tour")
    create_concert(
        db_session, tour, venue, day_offset=5, ticket_price="50.00",
        base_time=datetime.now(), tickets_sold=venue.capacity - 12,
    )

    response = client.get("/api/v1/dashboard/concerts")

    assert response.status_code == 200
    assert "12 tickets left" in response.text
    assert "Sold Out" not in response.text


def test_dashboard_concerts_endpoint_shows_sold_out_badge_not_zero_left(client, db_session):
    venue = create_venues(db_session, count=1)[0]
    tour = _make_tour(db_session, "Sellout Card Tour")
    create_concert(
        db_session, tour, venue, day_offset=5, ticket_price="50.00",
        base_time=datetime.now(), tickets_sold=venue.capacity,
    )

    response = client.get("/api/v1/dashboard/concerts")

    assert response.status_code == 200
    assert "Sold Out" in response.text
    assert "0 tickets left" not in response.text


def test_dashboard_concerts_endpoint_shows_sold_out_badge_for_zero_capacity_venue(client, db_session):
    venue = Venue(name="Unbuilt Venue", city="Testville", country="USA", capacity=0)
    db_session.add(venue)
    db_session.commit()
    db_session.refresh(venue)
    tour = _make_tour(db_session, "Zero Capacity Tour")
    create_concert(
        db_session, tour, venue, day_offset=5, ticket_price="50.00",
        base_time=datetime.now(), tickets_sold=0,
    )

    response = client.get("/api/v1/dashboard/concerts")

    assert response.status_code == 200
    assert "Sold Out" in response.text


def test_dashboard_concerts_endpoint_escapes_venue_name(client, db_session):
    venue = Venue(name="<script>alert('xss')</script>", city="Testville", country="USA", capacity=100)
    db_session.add(venue)
    db_session.commit()
    db_session.refresh(venue)
    tour = _make_tour(db_session, "XSS Tour")
    create_concert(db_session, tour, venue, day_offset=5, ticket_price="50.00", base_time=datetime.now())

    response = client.get("/api/v1/dashboard/concerts")

    assert response.status_code == 200
    assert "<script>alert" not in response.text
    assert "&lt;script&gt;" in response.text


def test_dashboard_concerts_endpoint_handles_empty_state(client):
    response = client.get("/api/v1/dashboard/concerts")

    assert response.status_code == 200
    assert "No concerts scheduled" in response.text


def test_dashboard_calendar_grid_wired_to_concerts_endpoint(client):
    response = client.get("/dashboard")

    assert response.status_code == 200
    assert "/api/v1/dashboard/concerts" in response.text
