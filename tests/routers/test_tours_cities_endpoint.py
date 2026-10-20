"""Tests for `GET /api/v1/tours/{tour_id}/cities`."""

from datetime import datetime, timedelta

from tests.fixtures.dashboard_fixtures import create_concert, create_tour, create_venues

BASE_TIME = datetime(2024, 6, 15, 20, 0, 0)


class TestGetTourCitiesEndpoint:
    """Coverage for the tour cities endpoint."""

    def test_get_cities_returns_200_and_ordered_distinct_cities(self, client, db_session):
        venues = create_venues(db_session, count=3)
        tour = create_tour(
            db_session, "Neon Skyline World Tour", "Aurora Belle",
            BASE_TIME.date(), BASE_TIME.date(), "active",
        )
        create_concert(db_session, tour, venues[2], day_offset=3, ticket_price="110.00", base_time=BASE_TIME)
        create_concert(db_session, tour, venues[0], day_offset=0, ticket_price="80.00", base_time=BASE_TIME)
        create_concert(db_session, tour, venues[1], day_offset=1, ticket_price="90.00", base_time=BASE_TIME)

        response = client.get(f"/api/v1/tours/{tour.id}/cities")

        assert response.status_code == 200
        assert response.json() == {
            "tour_id": tour.id,
            "cities": [
                {"city": "New York", "first_concert_date": BASE_TIME.date().isoformat()},
                {"city": "London", "first_concert_date": (BASE_TIME + timedelta(days=1)).date().isoformat()},
                {"city": "Paris", "first_concert_date": (BASE_TIME + timedelta(days=3)).date().isoformat()},
            ],
        }

    def test_get_cities_omits_cancelled_concerts_returns_200(self, client, db_session):
        venues = create_venues(db_session, count=2)
        tour = create_tour(
            db_session, "Solstice Echoes Tour", "Vela Ashford",
            BASE_TIME.date(), BASE_TIME.date(), "active",
        )
        create_concert(db_session, tour, venues[0], day_offset=0, ticket_price="80.00", base_time=BASE_TIME)
        create_concert(
            db_session, tour, venues[1], day_offset=1, ticket_price="120.00", base_time=BASE_TIME,
            is_cancelled=True, cancellation_reason="Venue unavailable",
        )

        response = client.get(f"/api/v1/tours/{tour.id}/cities")

        assert response.status_code == 200
        data = response.json()
        assert data["tour_id"] == tour.id
        assert data["cities"] == [
            {"city": "New York", "first_concert_date": BASE_TIME.date().isoformat()},
        ]

    def test_get_cities_empty_tour_returns_200_with_empty_list(self, client, db_session):
        tour = create_tour(
            db_session, "Unannounced Tour", "TBD Collective",
            BASE_TIME.date(), BASE_TIME.date(), "planned",
        )

        response = client.get(f"/api/v1/tours/{tour.id}/cities")

        assert response.status_code == 200
        assert response.json() == {"tour_id": tour.id, "cities": []}

    def test_get_unknown_tour_returns_404(self, client):
        response = client.get("/api/v1/tours/999999/cities")

        assert response.status_code == 404
        assert response.json() == {"detail": "Tour not found"}

    def test_get_cities_non_integer_id_returns_422(self, client):
        response = client.get("/api/v1/tours/not-an-id/cities")

        assert response.status_code == 422
