"""Tests for `GET /api/v1/tours/{tour_id}/summary`."""

from datetime import datetime, timedelta

from tests.fixtures.dashboard_fixtures import create_concert, create_tour, create_venues


class TestTourSummaryEndpoint:
    """Coverage for the aggregate tour summary endpoint."""

    def test_summary_for_tour_with_multiple_dates_and_cities(self, client, db_session):
        base_time = datetime(2024, 6, 1, 20, 0, 0)
        venues = create_venues(db_session, count=3)
        tour = create_tour(
            db_session, "Scramble Tour", "Test Artist",
            base_time.date(), (base_time + timedelta(days=30)).date(), "active",
        )
        create_concert(db_session, tour, venues[0], day_offset=20, ticket_price="80.00", base_time=base_time)
        create_concert(db_session, tour, venues[1], day_offset=1, ticket_price="80.00", base_time=base_time)
        create_concert(db_session, tour, venues[2], day_offset=10, ticket_price="80.00", base_time=base_time)

        response = client.get(f"/api/v1/tours/{tour.id}/summary")
        assert response.status_code == 200
        data = response.json()
        assert data["tour_id"] == tour.id
        assert data["date_count"] == 3
        assert data["first_date"] == (base_time + timedelta(days=1)).date().isoformat()
        assert data["last_date"] == (base_time + timedelta(days=20)).date().isoformat()
        assert data["distinct_city_count"] == 3

    def test_summary_dedupes_repeated_cities(self, client, db_session):
        base_time = datetime(2024, 6, 1, 20, 0, 0)
        venues = create_venues(db_session, count=2)
        tour = create_tour(
            db_session, "Repeat City Tour", "Test Artist",
            base_time.date(), (base_time + timedelta(days=30)).date(), "active",
        )
        # Same venue (same city) visited twice.
        create_concert(db_session, tour, venues[0], day_offset=1, ticket_price="80.00", base_time=base_time)
        create_concert(db_session, tour, venues[0], day_offset=15, ticket_price="80.00", base_time=base_time)
        create_concert(db_session, tour, venues[1], day_offset=8, ticket_price="80.00", base_time=base_time)

        response = client.get(f"/api/v1/tours/{tour.id}/summary")
        assert response.status_code == 200
        data = response.json()
        assert data["date_count"] == 3
        assert data["distinct_city_count"] == 2

    def test_summary_for_tour_with_no_dates(self, client, empty_tour):
        tour = empty_tour["tour"]

        response = client.get(f"/api/v1/tours/{tour.id}/summary")
        assert response.status_code == 200
        data = response.json()
        assert data == {
            "tour_id": tour.id,
            "date_count": 0,
            "first_date": None,
            "last_date": None,
            "distinct_city_count": 0,
        }

    def test_summary_not_found(self, client):
        response = client.get("/api/v1/tours/999/summary")
        assert response.status_code == 404
