"""Integration tests for `GET /api/v1/tours/sold-out`, and a regression
check that `GET /api/v1/tours/{tour_id}` still works and still validates
its path param now that `/sold-out` is registered ahead of it.

Tours/venues/concerts are seeded through real foreign keys via
`tests/fixtures/dashboard_fixtures.py` helpers, never hardcoded ids.
"""

from datetime import datetime, timedelta

from tests.fixtures.dashboard_fixtures import create_concert, create_tour, create_venues

BASE_TIME = datetime(2024, 6, 15, 18, 0, 0)


class TestSoldOutToursEndpoint:
    """Coverage for `GET /api/v1/tours/sold-out`."""

    def test_sold_out_tours_returns_only_fully_sold_out_tour(self, client, db_session):
        venues = create_venues(db_session, count=3)

        sold_out_tour = create_tour(
            db_session, "Sold Out Tour", "Test Artist",
            BASE_TIME.date(), (BASE_TIME + timedelta(days=30)).date(), "active",
        )
        create_concert(
            db_session, sold_out_tour, venues[0], day_offset=1,
            ticket_price="80.00", base_time=BASE_TIME, tickets_sold=venues[0].capacity,
        )

        partially_sold_tour = create_tour(
            db_session, "Partially Sold Tour", "Test Artist",
            BASE_TIME.date(), (BASE_TIME + timedelta(days=30)).date(), "active",
        )
        create_concert(
            db_session, partially_sold_tour, venues[1], day_offset=1,
            ticket_price="80.00", base_time=BASE_TIME, tickets_sold=venues[1].capacity - 1,
        )

        all_cancelled_tour = create_tour(
            db_session, "All Cancelled Tour", "Test Artist",
            BASE_TIME.date(), (BASE_TIME + timedelta(days=30)).date(), "active",
        )
        create_concert(
            db_session, all_cancelled_tour, venues[2], day_offset=1,
            ticket_price="80.00", base_time=BASE_TIME, tickets_sold=venues[2].capacity,
            is_cancelled=True, cancellation_reason="Venue closed",
        )

        response = client.get("/api/v1/tours/sold-out")
        assert response.status_code == 200
        payload = response.json()

        assert [tour["id"] for tour in payload] == [sold_out_tour.id]

    def test_sold_out_tours_returns_200_empty_list_when_none_qualify(self, client, db_session):
        venues = create_venues(db_session, count=1)
        tour = create_tour(
            db_session, "Not Sold Out Tour", "Test Artist",
            BASE_TIME.date(), (BASE_TIME + timedelta(days=30)).date(), "active",
        )
        create_concert(
            db_session, tour, venues[0], day_offset=1,
            ticket_price="80.00", base_time=BASE_TIME, tickets_sold=0,
        )

        response = client.get("/api/v1/tours/sold-out")
        assert response.status_code == 200
        assert response.json() == []

    def test_sold_out_tours_returns_200_empty_list_on_empty_database(self, client):
        response = client.get("/api/v1/tours/sold-out")
        assert response.status_code == 200
        assert response.json() == []


class TestTourDetailRouteStillWorks:
    """Regression coverage: `/sold-out` must not shadow `/{tour_id}`."""

    def test_get_tour_by_id_returns_200_with_payload(self, client, db_session):
        tour = create_tour(
            db_session, "Detail Route Tour", "Test Artist",
            BASE_TIME.date(), (BASE_TIME + timedelta(days=30)).date(), "active",
        )

        response = client.get(f"/api/v1/tours/{tour.id}")
        assert response.status_code == 200
        assert response.json()["id"] == tour.id

    def test_get_tour_by_unknown_id_returns_404(self, client):
        response = client.get("/api/v1/tours/999999")
        assert response.status_code == 404

    def test_get_tour_by_non_int_id_returns_422(self, client):
        response = client.get("/api/v1/tours/not-an-int")
        assert response.status_code == 422
