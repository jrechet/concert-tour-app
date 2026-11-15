"""Tests for `GET /api/v1/stats/cancellations`."""

from datetime import datetime

from tests.fixtures.dashboard_fixtures import create_concert, create_tour, create_venues


def _seed_tour(db_session, name="Cancellation Stats Tour"):
    now = datetime.now()
    return create_tour(
        db_session,
        name=name,
        artist="Test Artist",
        start_date=now.date(),
        end_date=now.date(),
        status="active",
    )


class TestCancellationsStatsEndpoint:
    """Coverage for `GET /api/v1/stats/cancellations`."""

    def test_get_cancellations_returns_200_and_zeros_when_no_concerts(self, client):
        response = client.get("/api/v1/stats/cancellations")

        assert response.status_code == 200
        assert response.json() == {
            "total_concerts": 0,
            "cancelled_concerts": 0,
            "cancellation_rate": 0.0,
            "by_tour": [],
        }

    def test_get_cancellations_returns_200_with_per_tour_breakdown(self, client, db_session):
        tour_a = _seed_tour(db_session, name="Tour A")
        tour_b = _seed_tour(db_session, name="Tour B")
        venues = create_venues(db_session, count=2)
        now = datetime.now()
        create_concert(
            db_session, tour_a, venues[0], day_offset=1, ticket_price="50.00",
            base_time=now, tickets_sold=0, is_cancelled=True, cancellation_reason="Weather",
        )
        create_concert(
            db_session, tour_a, venues[0], day_offset=2, ticket_price="50.00",
            base_time=now, tickets_sold=100,
        )
        create_concert(
            db_session, tour_b, venues[1], day_offset=1, ticket_price="60.00",
            base_time=now, tickets_sold=0, is_cancelled=True, cancellation_reason="Illness",
        )

        response = client.get("/api/v1/stats/cancellations")

        assert response.status_code == 200
        data = response.json()
        assert data["total_concerts"] == 3
        assert data["cancelled_concerts"] == 2
        assert data["cancellation_rate"] == 66.7
        assert len(data["by_tour"]) == 2
        tour_names = {entry["tour_name"] for entry in data["by_tour"]}
        assert tour_names == {"Tour A", "Tour B"}
        for entry in data["by_tour"]:
            assert entry["cancelled_concerts"] == 1

    def test_get_cancellations_rounds_rate_to_one_decimal(self, client, db_session):
        tour = _seed_tour(db_session)
        venues = create_venues(db_session, count=3)
        now = datetime.now()
        create_concert(
            db_session, tour, venues[0], day_offset=1, ticket_price="50.00",
            base_time=now, tickets_sold=0, is_cancelled=True, cancellation_reason="Weather",
        )
        create_concert(
            db_session, tour, venues[1], day_offset=2, ticket_price="50.00",
            base_time=now, tickets_sold=100,
        )
        create_concert(
            db_session, tour, venues[2], day_offset=3, ticket_price="50.00",
            base_time=now, tickets_sold=100,
        )

        response = client.get("/api/v1/stats/cancellations")

        assert response.status_code == 200
        assert response.json()["cancellation_rate"] == 33.3

    def test_cancellations_route_appears_in_openapi_schema(self, client):
        response = client.get("/openapi.json")

        assert response.status_code == 200
        assert "/api/v1/stats/cancellations" in response.json()["paths"]

    def test_post_cancellations_returns_405(self, client):
        response = client.post("/api/v1/stats/cancellations")

        assert response.status_code == 405

    def test_misspelled_sibling_path_returns_404(self, client):
        response = client.get("/api/v1/stats/cancellation")

        assert response.status_code == 404
