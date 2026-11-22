"""Tests for `GET /api/v1/venues/search`."""

from tests.fixtures.dashboard_fixtures import create_venues


class TestSearchVenuesEndpoint:
    """Coverage for `GET /api/v1/venues/search`."""

    def test_matching_query_returns_venues_ordered_by_name(self, client, db_session):
        create_venues(db_session, count=4)
        # Madison Square Garden, The O2 Arena, Accor Arena, Tokyo Dome.

        response = client.get("/api/v1/venues/search", params={"q": "arena"})

        assert response.status_code == 200
        data = response.json()
        assert [venue["name"] for venue in data] == ["Accor Arena", "The O2 Arena"]

    def test_query_is_case_insensitive(self, client, db_session):
        create_venues(db_session, count=4)

        response = client.get("/api/v1/venues/search", params={"q": "ARENA"})

        assert response.status_code == 200
        data = response.json()
        assert [venue["name"] for venue in data] == ["Accor Arena", "The O2 Arena"]

    def test_no_match_returns_empty_list(self, client, db_session):
        create_venues(db_session, count=4)

        response = client.get("/api/v1/venues/search", params={"q": "zzzznothing"})

        assert response.status_code == 200
        assert response.json() == []

    def test_query_below_minimum_length_returns_422(self, client, db_session):
        create_venues(db_session, count=4)

        response = client.get("/api/v1/venues/search", params={"q": "a"})

        assert response.status_code == 422

    def test_missing_query_returns_422(self, client, db_session):
        create_venues(db_session, count=4)

        response = client.get("/api/v1/venues/search")

        assert response.status_code == 422

    def test_route_is_not_shadowed_by_venue_detail_route(self, client, db_session):
        create_venues(db_session, count=4)

        response = client.get("/api/v1/venues/search", params={"q": "arena"})

        assert response.status_code == 200
        assert response.json() != []
