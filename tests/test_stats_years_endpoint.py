"""Tests for `GET /api/v1/stats/years`."""

from datetime import datetime

from tests.fixtures.dashboard_fixtures import create_concert, create_tour, create_venues


def _seed_tour(db_session, name="Years Stats Tour"):
    now = datetime.now()
    return create_tour(
        db_session,
        name=name,
        artist="Test Artist",
        start_date=now.date(),
        end_date=now.date(),
        status="active",
    )


class TestYearsStatsEndpoint:
    """Coverage for `GET /api/v1/stats/years`."""

    def test_get_years_returns_200_and_empty_list_when_no_concerts(self, client):
        response = client.get("/api/v1/stats/years")

        assert response.status_code == 200
        assert response.json() == []

    def test_get_years_returns_200_with_populated_and_ordered_years(self, client, db_session):
        tour = _seed_tour(db_session)
        venues = create_venues(db_session, count=2)

        create_concert(
            db_session, tour, venues[0], day_offset=0, ticket_price="50.00",
            base_time=datetime(2024, 6, 1), tickets_sold=100,
        )
        create_concert(
            db_session, tour, venues[1], day_offset=0, ticket_price="60.00",
            base_time=datetime(2024, 7, 1), tickets_sold=0,
            is_cancelled=True, cancellation_reason="Weather",
        )
        create_concert(
            db_session, tour, venues[0], day_offset=0, ticket_price="70.00",
            base_time=datetime(2023, 3, 1), tickets_sold=50,
        )

        response = client.get("/api/v1/stats/years")

        assert response.status_code == 200
        assert response.json() == [
            {"year": 2023, "concerts": 1, "cancelled": 0, "tickets_sold": 50},
            {"year": 2024, "concerts": 2, "cancelled": 1, "tickets_sold": 100},
        ]

    def test_years_route_appears_in_openapi_schema(self, client):
        response = client.get("/openapi.json")

        assert response.status_code == 200
        assert "/api/v1/stats/years" in response.json()["paths"]

    def test_post_years_returns_405(self, client):
        response = client.post("/api/v1/stats/years")

        assert response.status_code == 405
