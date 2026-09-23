"""Integration tests asserting is_almost_sold_out is exposed through the
concerts JSON API (list and detail endpoints).

Uses real venue/tour/concert fixtures persisted via the ORM so every
foreign key is a genuine committed id, not a hardcoded literal like
venue_id=1.
"""

from datetime import datetime, timedelta

from tests.fixtures.dashboard_fixtures import create_concert, create_tour, create_venues


def _seed_tour_and_venue(db_session):
    tour = create_tour(
        db_session,
        name="Almost Sold Out Tour",
        artist="Test Artist",
        start_date=(datetime.now() - timedelta(days=1)).date(),
        end_date=(datetime.now() + timedelta(days=90)).date(),
        status="active",
    )
    venue = create_venues(db_session, count=1)[0]
    return tour, venue


def test_get_concerts_includes_is_almost_sold_out_true(client, db_session):
    """A concert within the threshold reports is_almost_sold_out True in
    the list endpoint."""
    tour, venue = _seed_tour_and_venue(db_session)
    tickets_sold = int(venue.capacity * 0.95)
    create_concert(
        db_session, tour, venue, day_offset=10, ticket_price="50.00",
        base_time=datetime.now(), tickets_sold=tickets_sold,
    )

    response = client.get("/api/v1/concerts/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["is_almost_sold_out"] is True


def test_get_concerts_includes_is_almost_sold_out_false(client, db_session):
    """A concert far from the threshold reports is_almost_sold_out False
    in the list endpoint."""
    tour, venue = _seed_tour_and_venue(db_session)
    create_concert(
        db_session, tour, venue, day_offset=10, ticket_price="50.00",
        base_time=datetime.now(), tickets_sold=0,
    )

    response = client.get("/api/v1/concerts/")
    assert response.status_code == 200
    data = response.json()
    assert data[0]["is_almost_sold_out"] is False


def test_get_concert_by_id_includes_is_almost_sold_out_true(client, db_session):
    """A fully sold-out concert reports is_almost_sold_out True in the
    detail endpoint."""
    tour, venue = _seed_tour_and_venue(db_session)
    concert = create_concert(
        db_session, tour, venue, day_offset=10, ticket_price="50.00",
        base_time=datetime.now(), tickets_sold=venue.capacity,
    )

    response = client.get(f"/api/v1/concerts/{concert.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == concert.id
    assert data["is_almost_sold_out"] is True


def test_get_concert_by_id_includes_is_almost_sold_out_false(client, db_session):
    """A concert with minimal sales reports is_almost_sold_out False in
    the detail endpoint."""
    tour, venue = _seed_tour_and_venue(db_session)
    concert = create_concert(
        db_session, tour, venue, day_offset=10, ticket_price="50.00",
        base_time=datetime.now(), tickets_sold=1,
    )

    response = client.get(f"/api/v1/concerts/{concert.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["is_almost_sold_out"] is False


class TestRemainingTicketsOnGetEndpoints:
    """`remaining_tickets` is derived from each concert's real venue
    relationship (capacity - tickets_sold), never a hardcoded value."""

    def test_get_concerts_list_includes_remaining_tickets_for_every_concert(self, client, db_session):
        """The list endpoint reports the correct remaining_tickets for
        multiple concerts, each linked to a distinct fixture-created venue."""
        tour = create_tour(
            db_session,
            name="Remaining Tickets Tour",
            artist="Test Artist",
            start_date=(datetime.now() - timedelta(days=1)).date(),
            end_date=(datetime.now() + timedelta(days=90)).date(),
            status="active",
        )
        venues = create_venues(db_session, count=2)
        create_concert(
            db_session, tour, venues[0], day_offset=10, ticket_price="50.00",
            base_time=datetime.now(), tickets_sold=100,
        )
        create_concert(
            db_session, tour, venues[1], day_offset=20, ticket_price="60.00",
            base_time=datetime.now(), tickets_sold=250,
        )

        response = client.get("/api/v1/concerts/")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        by_venue = {row["venue_id"]: row for row in data}
        assert by_venue[venues[0].id]["remaining_tickets"] == venues[0].capacity - 100
        assert by_venue[venues[1].id]["remaining_tickets"] == venues[1].capacity - 250

    def test_get_concert_by_id_returns_correct_remaining_tickets(self, client, db_session):
        """The detail endpoint reports the correct remaining_tickets for a
        single concert."""
        tour, venue = _seed_tour_and_venue(db_session)
        concert = create_concert(
            db_session, tour, venue, day_offset=10, ticket_price="50.00",
            base_time=datetime.now(), tickets_sold=42,
        )

        response = client.get(f"/api/v1/concerts/{concert.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == concert.id
        assert data["remaining_tickets"] == venue.capacity - 42

    def test_sold_out_concert_returns_zero_remaining_tickets(self, client, db_session):
        """A concert where tickets_sold == capacity reports
        remaining_tickets 0 (and sold_out True) via the detail endpoint."""
        tour, venue = _seed_tour_and_venue(db_session)
        concert = create_concert(
            db_session, tour, venue, day_offset=10, ticket_price="50.00",
            base_time=datetime.now(), tickets_sold=venue.capacity,
        )

        response = client.get(f"/api/v1/concerts/{concert.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["remaining_tickets"] == 0
        assert data["sold_out"] is True

    def test_sold_out_concert_in_list_returns_zero_remaining_tickets(self, client, db_session):
        """A sold-out concert also reports remaining_tickets 0 via the list
        endpoint."""
        tour, venue = _seed_tour_and_venue(db_session)
        create_concert(
            db_session, tour, venue, day_offset=10, ticket_price="50.00",
            base_time=datetime.now(), tickets_sold=venue.capacity,
        )

        response = client.get("/api/v1/concerts/")
        assert response.status_code == 200
        data = response.json()
        assert data[0]["remaining_tickets"] == 0
        assert data[0]["sold_out"] is True
