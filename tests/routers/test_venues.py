"""Tests for `GET /api/v1/venues`."""

from datetime import datetime, timedelta

from tests.fixtures.dashboard_fixtures import create_concert, create_tour, create_venues

NOW = datetime.now()


class TestGetVenuesEndpoint:
    """Coverage for `GET /api/v1/venues`."""

    def test_no_params_returns_all_venues_sorted_by_name(self, client, db_session):
        create_venues(db_session, count=3)

        response = client.get("/api/v1/venues")

        assert response.status_code == 200
        data = response.json()
        assert [venue["name"] for venue in data] == [
            "Accor Arena", "Madison Square Garden", "The O2 Arena",
        ]
        assert data[0] == {
            "name": "Accor Arena",
            "city": "Paris",
            "country": "France",
            "capacity": 15000,
        }

    def test_no_venues_returns_empty_list(self, client):
        response = client.get("/api/v1/venues")

        assert response.status_code == 200
        assert response.json() == []

    def test_min_capacity_filters_out_smaller_venues(self, client, db_session):
        create_venues(db_session, count=3)
        # Madison Square Garden: 20000, The O2 Arena: 18000, Accor Arena: 15000.

        response = client.get("/api/v1/venues", params={"min_capacity": 18000})

        assert response.status_code == 200
        data = response.json()
        assert [venue["name"] for venue in data] == [
            "Madison Square Garden", "The O2 Arena",
        ]
        assert all(venue["capacity"] >= 18000 for venue in data)

    def test_negative_min_capacity_returns_422(self, client, db_session):
        create_venues(db_session, count=3)

        response = client.get("/api/v1/venues", params={"min_capacity": -5})

        assert response.status_code == 422


class TestGetVenueDetailEndpoint:
    """Coverage for `GET /api/v1/venues/{id}`."""

    def test_existing_venue_returns_details_and_ordered_upcoming_concerts(self, client, db_session):
        venue = create_venues(db_session, count=1)[0]
        tour = create_tour(
            db_session, "Reunion Tour", "Test Artist",
            (NOW - timedelta(days=60)).date(),
            (NOW + timedelta(days=60)).date(),
            "active",
        )
        past_concert = create_concert(
            db_session, tour, venue, day_offset=-10, ticket_price="50.00", base_time=NOW,
        )
        cancelled_future_concert = create_concert(
            db_session, tour, venue, day_offset=5, ticket_price="50.00", base_time=NOW,
            is_cancelled=True, cancellation_reason="Artist illness",
        )
        soonest_future_concert = create_concert(
            db_session, tour, venue, day_offset=10, ticket_price="50.00", base_time=NOW,
        )
        later_future_concert = create_concert(
            db_session, tour, venue, day_offset=30, ticket_price="50.00", base_time=NOW,
        )

        response = client.get(f"/api/v1/venues/{venue.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == venue.name
        assert data["city"] == venue.city
        assert data["country"] == venue.country
        assert data["capacity"] == venue.capacity
        returned_ids = [concert["id"] for concert in data["upcoming_concerts"]]
        assert returned_ids == [soonest_future_concert.id, later_future_concert.id]
        assert past_concert.id not in returned_ids
        assert cancelled_future_concert.id not in returned_ids

    def test_venue_with_no_upcoming_concerts_returns_empty_list(self, client, db_session):
        venue = create_venues(db_session, count=1)[0]

        response = client.get(f"/api/v1/venues/{venue.id}")

        assert response.status_code == 200
        assert response.json()["upcoming_concerts"] == []

    def test_unknown_venue_id_returns_404(self, client):
        response = client.get("/api/v1/venues/999999")

        assert response.status_code == 404
