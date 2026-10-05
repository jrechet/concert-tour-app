"""Tests for `POST /api/v1/tours/{tour_id}/duplicate`."""

from datetime import date

from tests.fixtures.dashboard_fixtures import create_tour


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
