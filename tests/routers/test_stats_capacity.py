"""Tests for `GET /api/v1/stats/capacity`."""

from datetime import datetime

from tests.fixtures.dashboard_fixtures import create_concert, create_tour, create_venues


def _seed_tour(db_session):
    now = datetime.now()
    return create_tour(
        db_session,
        name="Capacity Stats Tour",
        artist="Test Artist",
        start_date=now.date(),
        end_date=now.date(),
        status="active",
    )


class TestCapacityStatsEndpoint:
    """Coverage for `GET /api/v1/stats/capacity`."""

    def test_get_capacity_returns_200_and_zeros_when_no_concerts(self, client):
        response = client.get("/api/v1/stats/capacity")

        assert response.status_code == 200
        assert response.json() == {
            "total_capacity": 0,
            "tickets_sold": 0,
            "seats_left": 0,
        }

    def test_get_capacity_returns_200_with_aggregated_values(self, client, db_session):
        tour = _seed_tour(db_session)
        venues = create_venues(db_session, count=2)
        now = datetime.now()
        create_concert(
            db_session, tour, venues[0], day_offset=1, ticket_price="50.00",
            base_time=now, tickets_sold=100,
        )
        create_concert(
            db_session, tour, venues[1], day_offset=2, ticket_price="60.00",
            base_time=now, tickets_sold=200,
        )

        response = client.get("/api/v1/stats/capacity")

        assert response.status_code == 200
        data = response.json()
        expected_capacity = venues[0].capacity + venues[1].capacity
        assert data["total_capacity"] == expected_capacity
        assert data["tickets_sold"] == 300
        assert data["seats_left"] == expected_capacity - 300

    def test_get_capacity_ignores_cancelled_and_past_concerts(self, client, db_session):
        tour = _seed_tour(db_session)
        venues = create_venues(db_session, count=3)
        now = datetime.now()
        create_concert(
            db_session, tour, venues[0], day_offset=1, ticket_price="50.00",
            base_time=now, tickets_sold=100,
            is_cancelled=True, cancellation_reason="Weather",
        )
        create_concert(
            db_session, tour, venues[1], day_offset=-5, ticket_price="50.00",
            base_time=now, tickets_sold=100,
        )
        create_concert(
            db_session, tour, venues[2], day_offset=1, ticket_price="50.00",
            base_time=now, tickets_sold=50,
        )

        response = client.get("/api/v1/stats/capacity")

        assert response.status_code == 200
        data = response.json()
        assert data["total_capacity"] == venues[2].capacity
        assert data["tickets_sold"] == 50
        assert data["seats_left"] == venues[2].capacity - 50

    def test_get_capacity_response_shape_is_three_integer_fields(self, client, db_session):
        tour = _seed_tour(db_session)
        venues = create_venues(db_session, count=1)
        create_concert(
            db_session, tour, venues[0], day_offset=1, ticket_price="50.00",
            base_time=datetime.now(), tickets_sold=10,
        )

        response = client.get("/api/v1/stats/capacity")

        assert response.status_code == 200
        data = response.json()
        assert set(data.keys()) == {"total_capacity", "tickets_sold", "seats_left"}
        for value in data.values():
            assert isinstance(value, int)

    def test_post_capacity_returns_405(self, client):
        response = client.post("/api/v1/stats/capacity")

        assert response.status_code == 405
