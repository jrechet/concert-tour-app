"""Tests for `GET /api/v1/stats/prices`."""

from datetime import datetime

from tests.fixtures.dashboard_fixtures import create_concert, create_tour, create_venues


def _seed_tour(db_session):
    now = datetime.now()
    return create_tour(
        db_session,
        name="Price Stats Tour",
        artist="Test Artist",
        start_date=now.date(),
        end_date=now.date(),
        status="active",
    )


class TestPriceStatsEndpoint:
    """Coverage for `GET /api/v1/stats/prices`."""

    def test_get_prices_returns_200_with_min_avg_max_on_mixed_dataset(self, client, db_session):
        tour = _seed_tour(db_session)
        venues = create_venues(db_session, count=3)
        now = datetime.now()
        create_concert(db_session, tour, venues[0], day_offset=1, ticket_price="50.00", base_time=now)
        create_concert(db_session, tour, venues[1], day_offset=2, ticket_price="100.00", base_time=now)
        create_concert(db_session, tour, venues[2], day_offset=3, ticket_price="150.00", base_time=now)
        # A past concert must not affect the stats.
        create_concert(db_session, tour, venues[0], day_offset=-10, ticket_price="1.00", base_time=now)
        # A cancelled concert must not affect the stats.
        create_concert(
            db_session, tour, venues[1], day_offset=4, ticket_price="9999.00", base_time=now,
            is_cancelled=True, cancellation_reason="Weather",
        )
        # A concert with no ticket price must not affect the stats.
        create_concert(db_session, tour, venues[2], day_offset=5, ticket_price=None, base_time=now)

        response = client.get("/api/v1/stats/prices")

        assert response.status_code == 200
        assert response.json() == {"min": 50.0, "avg": 100.0, "max": 150.0}

    def test_get_prices_returns_200_with_three_nulls_when_no_concerts(self, client):
        response = client.get("/api/v1/stats/prices")

        assert response.status_code == 200
        assert response.json() == {"min": None, "avg": None, "max": None}

    def test_post_prices_returns_405(self, client):
        response = client.post("/api/v1/stats/prices")

        assert response.status_code == 405

    def test_response_shape_matches_price_stats_schema(self, client, db_session):
        tour = _seed_tour(db_session)
        venues = create_venues(db_session, count=1)
        create_concert(db_session, tour, venues[0], day_offset=1, ticket_price="75.00", base_time=datetime.now())

        response = client.get("/api/v1/stats/prices")

        assert response.status_code == 200
        data = response.json()
        assert set(data.keys()) == {"min", "avg", "max"}
        for value in data.values():
            assert isinstance(value, float)
