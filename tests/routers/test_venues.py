"""Tests for `GET /api/v1/venues`."""

from tests.fixtures.dashboard_fixtures import create_venues


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
