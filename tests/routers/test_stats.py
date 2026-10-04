"""Tests for `GET /api/v1/stats/revenue/cities`."""

from datetime import datetime

from tests.fixtures.dashboard_fixtures import create_concert, create_tour, create_venues

BASE_TIME = datetime(2024, 6, 17, 20, 0, 0)


def _seed_tour(db_session):
    return create_tour(
        db_session,
        name="Revenue Stats Tour",
        artist="Test Artist",
        start_date=BASE_TIME.date(),
        end_date=BASE_TIME.date(),
        status="active",
    )


class TestRevenueByCityEndpoint:
    """Coverage for `GET /api/v1/stats/revenue/cities`."""

    def test_returns_200_empty_array_when_no_concerts(self, client):
        response = client.get("/api/v1/stats/revenue/cities")

        assert response.status_code == 200
        assert response.json() == []

    def test_multi_city_dataset_ordered_by_revenue_descending(self, client, db_session):
        tour = _seed_tour(db_session)
        venues = create_venues(db_session, count=3)  # New York, London, Paris
        create_concert(
            db_session, tour, venues[0], day_offset=0, ticket_price="50.00",
            base_time=BASE_TIME, tickets_sold=100,
        )  # New York: 5000 (highest)
        create_concert(
            db_session, tour, venues[1], day_offset=1, ticket_price="20.00",
            base_time=BASE_TIME, tickets_sold=10,
        )  # London: 200 (lowest)
        create_concert(
            db_session, tour, venues[2], day_offset=2, ticket_price="30.00",
            base_time=BASE_TIME, tickets_sold=50,
        )  # Paris: 1500 (middle)

        response = client.get("/api/v1/stats/revenue/cities")

        assert response.status_code == 200
        data = response.json()
        assert [entry["city"] for entry in data] == ["New York", "Paris", "London"]
        assert [entry["revenue"] for entry in data] == [5000.0, 1500.0, 200.0]
        assert all(isinstance(entry["revenue"], (int, float)) for entry in data)

    def test_cancelled_concert_revenue_not_counted(self, client, db_session):
        tour = _seed_tour(db_session)
        venues = create_venues(db_session, count=1)
        create_concert(
            db_session, tour, venues[0], day_offset=0, ticket_price="40.00",
            base_time=BASE_TIME, tickets_sold=20,
        )
        create_concert(
            db_session, tour, venues[0], day_offset=1, ticket_price="9999.00",
            base_time=BASE_TIME, tickets_sold=9999, is_cancelled=True,
            cancellation_reason="Artist illness",
        )

        response = client.get("/api/v1/stats/revenue/cities")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["city"] == venues[0].city
        assert data[0]["revenue"] == 800.0
