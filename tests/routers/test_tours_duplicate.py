"""Tests for `POST /api/v1/tours/{tour_id}/duplicate`."""

from datetime import datetime

from tests.fixtures.dashboard_fixtures import create_concert, create_tour, create_venues

BASE_TIME = datetime(2025, 6, 1, 20, 0, 0)


class TestDuplicateTourEndpoint:
    """Coverage for `POST /api/v1/tours/{tour_id}/duplicate`."""

    def test_duplicate_tour_returns_201_and_copy(self, client, db_session):
        source = create_tour(
            db_session, "Neon Skyline World Tour", "Aurora Belle",
            BASE_TIME.date(), BASE_TIME.date(), "active",
        )

        response = client.post(f"/api/v1/tours/{source.id}/duplicate")

        assert response.status_code == 201
        body = response.json()
        assert body["id"] != source.id
        assert body["artist"] == source.artist
        assert body["name"] == "Neon Skyline World Tour (copy)"
        assert body["status"] == "planned"

    def test_duplicate_tour_copy_has_no_concerts(self, client, db_session):
        venues = create_venues(db_session, count=1)
        source = create_tour(
            db_session, "Neon Skyline World Tour", "Aurora Belle",
            BASE_TIME.date(), BASE_TIME.date(), "active",
        )
        create_concert(db_session, source, venues[0], day_offset=0, ticket_price="80.00", base_time=BASE_TIME)

        response = client.post(f"/api/v1/tours/{source.id}/duplicate")

        assert response.status_code == 201
        copy_id = response.json()["id"]
        dates_response = client.get(f"/api/v1/tours/{copy_id}/dates")
        assert dates_response.status_code == 200
        assert dates_response.json() == []

    def test_duplicate_unknown_tour_returns_404(self, client):
        response = client.post("/api/v1/tours/999999/duplicate")

        assert response.status_code == 404
        assert response.json()["detail"] == "Tour not found"

    def test_duplicate_tour_invalid_id_returns_422(self, client):
        response = client.post("/api/v1/tours/not-an-id/duplicate")

        assert response.status_code == 422

    def test_duplicate_tour_leaves_source_unchanged(self, client, db_session):
        venues = create_venues(db_session, count=1)
        source = create_tour(
            db_session, "Neon Skyline World Tour", "Aurora Belle",
            BASE_TIME.date(), BASE_TIME.date(), "active",
        )
        create_concert(db_session, source, venues[0], day_offset=0, ticket_price="80.00", base_time=BASE_TIME)

        response = client.post(f"/api/v1/tours/{source.id}/duplicate")
        assert response.status_code == 201

        get_response = client.get(f"/api/v1/tours/{source.id}")
        assert get_response.status_code == 200
        body = get_response.json()
        assert body["name"] == "Neon Skyline World Tour"
        assert body["status"] == "active"

        dates_response = client.get(f"/api/v1/tours/{source.id}/dates")
        assert dates_response.status_code == 200
        assert len(dates_response.json()) == 1
