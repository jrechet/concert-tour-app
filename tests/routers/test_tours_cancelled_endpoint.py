"""Integration tests for `GET /api/v1/tours/cancelled`, and a regression
check that `GET /api/v1/tours/{tour_id}` still works now that `/cancelled`
is registered ahead of it.

Tours/venues/concerts are seeded through real foreign keys via
`tests/fixtures/dashboard_fixtures.py` helpers, never hardcoded ids.
"""

from datetime import date, datetime, timedelta

from tests.fixtures.dashboard_fixtures import create_concert, create_tour, create_venues

BASE_TIME = datetime(2024, 6, 15, 18, 0, 0)


class TestCancelledToursEndpoint:
    """Coverage for `GET /api/v1/tours/cancelled`."""

    def test_returns_cancelled_tours_ordered_by_start_date_with_counts(self, client, db_session):
        venues = create_venues(db_session, count=2)

        earliest = create_tour(
            db_session, "Farewell Tour", "Aurora Belle",
            date(2024, 1, 1), date(2024, 1, 10), "cancelled",
        )
        latest = create_tour(
            db_session, "Final Bow Tour", "Aurora Belle",
            date(2024, 6, 1), date(2024, 6, 10), "cancelled",
        )
        active = create_tour(
            db_session, "Active Tour", "Someone Else",
            date(2024, 4, 1), date(2024, 4, 10), "active",
        )
        create_concert(db_session, earliest, venues[0], day_offset=0, ticket_price="80.00", base_time=BASE_TIME)
        create_concert(db_session, latest, venues[1], day_offset=0, ticket_price="80.00", base_time=BASE_TIME)
        create_concert(db_session, latest, venues[0], day_offset=1, ticket_price="80.00", base_time=BASE_TIME)
        create_concert(db_session, active, venues[1], day_offset=1, ticket_price="80.00", base_time=BASE_TIME)

        response = client.get("/api/v1/tours/cancelled")
        assert response.status_code == 200
        payload = response.json()

        assert [tour["id"] for tour in payload] == [latest.id, earliest.id]
        assert payload[0]["name"] == "Final Bow Tour"
        assert payload[0]["concert_count"] == 2
        assert payload[1]["name"] == "Farewell Tour"
        assert payload[1]["concert_count"] == 1

    def test_returns_200_empty_list_when_no_tour_is_cancelled(self, client, db_session):
        venues = create_venues(db_session, count=1)
        tour = create_tour(
            db_session, "Active Tour", "Test Artist",
            BASE_TIME.date(), (BASE_TIME + timedelta(days=30)).date(), "active",
        )
        create_concert(
            db_session, tour, venues[0], day_offset=1,
            ticket_price="80.00", base_time=BASE_TIME,
        )

        response = client.get("/api/v1/tours/cancelled")
        assert response.status_code == 200
        assert response.json() == []

    def test_returns_200_empty_list_on_empty_database(self, client):
        response = client.get("/api/v1/tours/cancelled")
        assert response.status_code == 200
        assert response.json() == []


class TestTourDetailRouteStillWorks:
    """Regression coverage: `/cancelled` must not shadow `/{tour_id}`."""

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
