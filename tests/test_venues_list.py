"""Tests for the `min_capacity` query filter on `GET /api/v1/venues`."""

from tests.fixtures.dashboard_fixtures import create_venues


class TestMinCapacityFilter:
    """Coverage for `GET /api/v1/venues?min_capacity=N`."""

    def test_min_capacity_filters_to_matching_venues_sorted_by_name(self, client, db_session):
        create_venues(db_session, count=3)
        # Madison Square Garden: 20000, The O2 Arena: 18000, Accor Arena: 15000.

        response = client.get("/api/v1/venues", params={"min_capacity": 18000})

        assert response.status_code == 200
        data = response.json()
        assert [venue["name"] for venue in data] == [
            "Madison Square Garden", "The O2 Arena",
        ]
        assert all(venue["capacity"] >= 18000 for venue in data)

    def test_boundary_capacity_equal_to_min_is_included(self, client, db_session):
        create_venues(db_session, count=3)
        # The O2 Arena has capacity exactly 18000.

        response = client.get("/api/v1/venues", params={"min_capacity": 18000})

        assert response.status_code == 200
        data = response.json()
        assert "The O2 Arena" in [venue["name"] for venue in data]
        o2_arena = next(venue for venue in data if venue["name"] == "The O2 Arena")
        assert o2_arena["capacity"] == 18000

    def test_omitting_min_capacity_returns_every_venue(self, client, db_session):
        create_venues(db_session, count=3)

        response = client.get("/api/v1/venues")

        assert response.status_code == 200
        data = response.json()
        assert [venue["name"] for venue in data] == [
            "Accor Arena", "Madison Square Garden", "The O2 Arena",
        ]

    def test_negative_min_capacity_returns_422(self, client, db_session):
        create_venues(db_session, count=3)

        response = client.get("/api/v1/venues", params={"min_capacity": -1})

        assert response.status_code == 422

    def test_non_integer_min_capacity_returns_422(self, client, db_session):
        create_venues(db_session, count=3)

        response = client.get("/api/v1/venues", params={"min_capacity": "abc"})

        assert response.status_code == 422

    def test_min_capacity_matching_nothing_returns_empty_list(self, client, db_session):
        create_venues(db_session, count=3)
        # The largest seeded venue (Madison Square Garden) has capacity 20000.

        response = client.get("/api/v1/venues", params={"min_capacity": 1_000_000})

        assert response.status_code == 200
        assert response.json() == []
