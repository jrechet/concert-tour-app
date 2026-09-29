"""Tests for `GET /api/v1/tours/{tour_id}/cities`."""

from datetime import datetime

from tests.fixtures.dashboard_fixtures import create_concert, create_tour, create_venues

BASE_TIME = datetime(2024, 6, 15, 20, 0, 0)


class TestTourCitiesEndpoint:
    """Coverage for the tour cities endpoint."""

    def test_cities_for_tour_with_concerts(self, client, db_session):
        venues = create_venues(db_session, count=3)
        tour = create_tour(
            db_session, "Neon Skyline World Tour", "Aurora Belle",
            BASE_TIME.date(), BASE_TIME.date(), "active",
        )
        # New York, then London, then New York again (revisited), then Paris.
        create_concert(db_session, tour, venues[0], day_offset=0, ticket_price="80.00", base_time=BASE_TIME)
        create_concert(db_session, tour, venues[1], day_offset=1, ticket_price="90.00", base_time=BASE_TIME)
        create_concert(db_session, tour, venues[0], day_offset=2, ticket_price="100.00", base_time=BASE_TIME)
        create_concert(db_session, tour, venues[2], day_offset=3, ticket_price="110.00", base_time=BASE_TIME)
        create_concert(
            db_session, tour, venues[2], day_offset=4, ticket_price="999.00", base_time=BASE_TIME,
            is_cancelled=True, cancellation_reason="Artist illness",
        )

        response = client.get(f"/api/v1/tours/{tour.id}/cities")
        assert response.status_code == 200
        data = response.json()
        assert data["tour_id"] == tour.id
        # New York (0), London (1), New York again (dup, skipped), Paris (3);
        # the cancelled concert's venue does not add a second Paris entry.
        assert data["cities"] == ["New York", "London", "Paris"]

    def test_cities_for_tour_with_no_concerts(self, client, empty_tour):
        tour = empty_tour["tour"]

        response = client.get(f"/api/v1/tours/{tour.id}/cities")
        assert response.status_code == 200
        data = response.json()
        assert data == {"tour_id": tour.id, "cities": []}

    def test_cities_not_found(self, client):
        response = client.get("/api/v1/tours/999999/cities")
        assert response.status_code == 404
        assert response.json() == {"detail": "Tour not found"}
