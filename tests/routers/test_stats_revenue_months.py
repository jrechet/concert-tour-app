"""Tests for `GET /api/v1/stats/revenue/months`."""

from datetime import datetime

from tests.fixtures.dashboard_fixtures import create_concert, create_tour, create_venues

BASE_TIME = datetime(2026, 1, 15, 20, 0, 0)


def _seed_tour(db_session):
    return create_tour(
        db_session,
        name="Monthly Revenue Tour",
        artist="Test Artist",
        start_date=BASE_TIME.date(),
        end_date=BASE_TIME.date(),
        status="active",
    )


class TestRevenueByMonthEndpoint:
    """Coverage for `GET /api/v1/stats/revenue/months`."""

    def test_returns_200_and_empty_list_when_no_concerts(self, client):
        response = client.get("/api/v1/stats/revenue/months")

        assert response.status_code == 200
        assert response.json() == []

    def test_returns_200_with_months_in_order(self, client, db_session):
        tour = _seed_tour(db_session)
        venues = create_venues(db_session, count=3)
        create_concert(
            db_session, tour, venues[0], day_offset=0, ticket_price="80.00",
            base_time=datetime(2026, 11, 1), tickets_sold=10,
        )
        create_concert(
            db_session, tour, venues[1], day_offset=0, ticket_price="50.00",
            base_time=datetime(2026, 1, 1), tickets_sold=40,
        )
        create_concert(
            db_session, tour, venues[2], day_offset=0, ticket_price="80.00",
            base_time=datetime(2026, 1, 20), tickets_sold=60,
        )

        response = client.get("/api/v1/stats/revenue/months")

        assert response.status_code == 200
        data = response.json()
        assert [row["month"] for row in data] == ["2026-01", "2026-11"]
        assert data[0]["tickets_sold"] == 100
        assert data[0]["revenue"] == 40 * 50.0 + 60 * 80.0
        assert data[1]["tickets_sold"] == 10
        assert data[1]["revenue"] == 10 * 80.0

    def test_cancelled_concerts_excluded_from_response(self, client, db_session):
        tour = _seed_tour(db_session)
        venues = create_venues(db_session, count=2)
        create_concert(
            db_session, tour, venues[0], day_offset=0, ticket_price="80.00",
            base_time=BASE_TIME, tickets_sold=100,
        )
        create_concert(
            db_session, tour, venues[1], day_offset=5, ticket_price="200.00",
            base_time=BASE_TIME, tickets_sold=999,
            is_cancelled=True, cancellation_reason="Venue closed",
        )

        response = client.get("/api/v1/stats/revenue/months")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["month"] == "2026-01"
        assert data[0]["tickets_sold"] == 100
        assert data[0]["revenue"] == 100 * 80.0

    def test_concert_without_price_yields_zero_revenue(self, client, db_session):
        tour = _seed_tour(db_session)
        venues = create_venues(db_session, count=1)
        create_concert(
            db_session, tour, venues[0], day_offset=0, ticket_price=None,
            base_time=BASE_TIME, tickets_sold=75,
        )

        response = client.get("/api/v1/stats/revenue/months")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["tickets_sold"] == 75
        assert data[0]["revenue"] == 0

    def test_wrong_method_returns_405(self, client):
        response = client.post("/api/v1/stats/revenue/months")

        assert response.status_code == 405

    def test_unknown_stats_subpath_returns_404(self, client):
        response = client.get("/api/v1/stats/revenue/weeks")

        assert response.status_code == 404
