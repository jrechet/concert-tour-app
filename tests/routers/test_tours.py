"""Tests for `POST /api/v1/tours/{tour_id}/duplicate` and `GET /api/v1/tours/sold-out`."""

from datetime import date, datetime

from tests.fixtures.dashboard_fixtures import create_concert, create_tour, create_venues

BASE_TIME = datetime(2024, 6, 15, 20, 0, 0)


class TestDuplicateTourEndpoint:
    """Coverage for the tour-duplication endpoint."""

    def test_duplicate_existing_tour_returns_201(self, client, db_session):
        source = create_tour(
            db_session, "Neon Skyline World Tour", "Aurora Belle",
            date(2024, 6, 1), date(2024, 12, 31), "active",
        )

        response = client.post(f"/api/v1/tours/{source.id}/duplicate")

        assert response.status_code == 201
        data = response.json()
        assert data["id"] != source.id
        assert data["name"] == "Neon Skyline World Tour (copy)"
        assert data["status"] == "planned"
        assert data["artist"] == "Aurora Belle"

        dates_response = client.get(f"/api/v1/tours/{data['id']}/dates")
        assert dates_response.status_code == 200
        assert dates_response.json() == []

    def test_duplicate_tour_not_found(self, client):
        response = client.post("/api/v1/tours/999999/duplicate")
        assert response.status_code == 404
        assert response.json() == {"detail": "Tour not found"}


class TestSoldOutToursEndpoint:
    """Coverage for `GET /api/v1/tours/sold-out`."""

    def test_sold_out_tours_endpoint_returns_qualifying_tours(self, client, db_session):
        venues = create_venues(db_session, count=1)
        tour = create_tour(
            db_session, "Neon Skyline World Tour", "Aurora Belle",
            BASE_TIME.date(), BASE_TIME.date(), "active",
        )
        create_concert(
            db_session, tour, venues[0], day_offset=0, ticket_price="80.00",
            base_time=BASE_TIME, tickets_sold=venues[0].capacity,
        )

        response = client.get("/api/v1/tours/sold-out")

        assert response.status_code == 200
        data = response.json()
        assert [t["id"] for t in data] == [tour.id]
        assert data[0]["name"] == "Neon Skyline World Tour"

    def test_sold_out_tours_endpoint_returns_empty_list(self, client, db_session):
        venues = create_venues(db_session, count=1)
        tour = create_tour(
            db_session, "Neon Skyline World Tour", "Aurora Belle",
            BASE_TIME.date(), BASE_TIME.date(), "active",
        )
        create_concert(
            db_session, tour, venues[0], day_offset=0, ticket_price="80.00",
            base_time=BASE_TIME, tickets_sold=1,
        )

        response = client.get("/api/v1/tours/sold-out")

        assert response.status_code == 200
        assert response.json() == []

    def test_get_tour_by_id_still_works_after_sold_out_route_added(self, client, db_session):
        tour = create_tour(
            db_session, "Neon Skyline World Tour", "Aurora Belle",
            BASE_TIME.date(), BASE_TIME.date(), "active",
        )

        response = client.get(f"/api/v1/tours/{tour.id}")

        assert response.status_code == 200
        assert response.json()["id"] == tour.id

    def test_get_tour_by_id_404_still_works(self, client):
        response = client.get("/api/v1/tours/999999")
        assert response.status_code == 404
        assert response.json() == {"detail": "Tour not found"}
