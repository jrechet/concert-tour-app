"""Tests for `GET /api/v1/stats/months`."""

from datetime import datetime

from tests.fixtures.dashboard_fixtures import create_concert, create_tour, create_venues


def _seed_tour(db_session):
    now = datetime.now()
    return create_tour(
        db_session,
        name="Monthly Stats Tour",
        artist="Test Artist",
        start_date=now.date(),
        end_date=now.date(),
        status="active",
    )


class TestMonthsStatsEndpoint:
    """Coverage for `GET /api/v1/stats/months`."""

    def test_get_months_returns_200_and_empty_list_when_no_concerts(self, client):
        response = client.get("/api/v1/stats/months")

        assert response.status_code == 200
        assert response.json() == []

    def test_get_months_returns_200_with_aggregated_chronological_months(self, client, db_session):
        tour = _seed_tour(db_session)
        venues = create_venues(db_session, count=3)
        # Seed out of chronological order to verify the response is re-ordered.
        create_concert(
            db_session, tour, venues[0], day_offset=0, ticket_price="50.00",
            base_time=datetime(2026, 3, 5),
        )
        create_concert(
            db_session, tour, venues[1], day_offset=0, ticket_price="50.00",
            base_time=datetime(2026, 1, 10),
        )
        create_concert(
            db_session, tour, venues[1], day_offset=1, ticket_price="50.00",
            base_time=datetime(2026, 1, 10),
        )
        create_concert(
            db_session, tour, venues[1], day_offset=2, ticket_price="50.00",
            base_time=datetime(2026, 1, 10),
        )
        create_concert(
            db_session, tour, venues[2], day_offset=0, ticket_price="50.00",
            base_time=datetime(2026, 2, 20),
        )

        response = client.get("/api/v1/stats/months")

        assert response.status_code == 200
        assert response.json() == [
            {"month": "2026-01", "count": 3},
            {"month": "2026-02", "count": 1},
            {"month": "2026-03", "count": 1},
        ]

    def test_get_months_excludes_cancelled_concerts(self, client, db_session):
        tour = _seed_tour(db_session)
        venues = create_venues(db_session, count=2)
        create_concert(
            db_session, tour, venues[0], day_offset=0, ticket_price="50.00",
            base_time=datetime(2026, 1, 10),
        )
        create_concert(
            db_session, tour, venues[1], day_offset=1, ticket_price="50.00",
            base_time=datetime(2026, 1, 10),
            is_cancelled=True, cancellation_reason="Weather",
        )

        response = client.get("/api/v1/stats/months")

        assert response.status_code == 200
        assert response.json() == [{"month": "2026-01", "count": 1}]

    def test_post_months_returns_405(self, client):
        response = client.post("/api/v1/stats/months")

        assert response.status_code == 405

    def test_get_unknown_stats_path_returns_404(self, client):
        response = client.get("/api/v1/stats/monthz")

        assert response.status_code == 404

    def test_months_route_appears_in_openapi_schema(self, client):
        response = client.get("/openapi.json")

        assert response.status_code == 200
        assert "/api/v1/stats/months" in response.json()["paths"]
