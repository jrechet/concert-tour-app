"""Tests for `GET /api/v1/stats/artists`."""

from datetime import datetime

from tests.fixtures.dashboard_fixtures import create_concert, create_tour, create_venues

BASE_TIME = datetime(2024, 6, 17, 20, 0, 0)


class TestArtistsStatsEndpoint:
    """Coverage for `GET /api/v1/stats/artists`."""

    def test_returns_200_empty_array_when_no_lineup(self, client):
        response = client.get("/api/v1/stats/artists")

        assert response.status_code == 200
        assert response.json() == []

    def test_seeded_data_returns_expected_ordered_payload(self, client, db_session):
        venues = create_venues(db_session, count=4)
        busy_tour = create_tour(
            db_session, "Neon Skyline World Tour", "Aurora Belle",
            BASE_TIME.date(), BASE_TIME.date(), "active",
        )
        quiet_tour = create_tour(
            db_session, "Homecoming Revival Tour", "The Midnight Collective",
            BASE_TIME.date(), BASE_TIME.date(), "active",
        )
        for i in range(3):
            create_concert(
                db_session, busy_tour, venues[i], day_offset=i, ticket_price="80.00",
                base_time=BASE_TIME,
            )
        create_concert(
            db_session, quiet_tour, venues[3], day_offset=0, ticket_price="90.00",
            base_time=BASE_TIME,
        )

        response = client.get("/api/v1/stats/artists")

        assert response.status_code == 200
        assert response.json() == [
            {"artist_id": "Aurora Belle", "name": "Aurora Belle", "concert_count": 3},
            {
                "artist_id": "The Midnight Collective",
                "name": "The Midnight Collective",
                "concert_count": 1,
            },
        ]

    def test_tie_is_broken_alphabetically_by_name(self, client, db_session):
        venues = create_venues(db_session, count=2)
        zebra_tour = create_tour(
            db_session, "Zebra Tour", "Zebra Band",
            BASE_TIME.date(), BASE_TIME.date(), "active",
        )
        aardvark_tour = create_tour(
            db_session, "Aardvark Tour", "Aardvark Band",
            BASE_TIME.date(), BASE_TIME.date(), "active",
        )
        create_concert(
            db_session, zebra_tour, venues[0], day_offset=0, ticket_price="50.00",
            base_time=BASE_TIME,
        )
        create_concert(
            db_session, aardvark_tour, venues[1], day_offset=0, ticket_price="50.00",
            base_time=BASE_TIME,
        )

        response = client.get("/api/v1/stats/artists")

        assert response.status_code == 200
        assert response.json() == [
            {"artist_id": "Aardvark Band", "name": "Aardvark Band", "concert_count": 1},
            {"artist_id": "Zebra Band", "name": "Zebra Band", "concert_count": 1},
        ]

    def test_post_not_allowed(self, client):
        response = client.post("/api/v1/stats/artists")

        assert response.status_code == 405

    def test_endpoint_appears_in_openapi_schema(self, client):
        response = client.get("/openapi.json")

        assert response.status_code == 200
        assert "/api/v1/stats/artists" in response.json()["paths"]
