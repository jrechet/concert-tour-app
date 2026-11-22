"""Tests for `POST /api/v1/tours/{tour_id}/uncancel` and
`PATCH /api/v1/tours/{tour_id}` (rename)."""

from datetime import datetime, timedelta

from src.models.tour import TOUR_NAME_MAX_LENGTH
from tests.fixtures.dashboard_fixtures import create_concert, create_tour, create_venues


class TestUncancelTourEndpoint:
    """Coverage for restoring a cancelled tour to `planned`."""

    def test_uncancel_restores_tour_and_cascaded_concerts(self, client, db_session):
        base_time = datetime(2024, 6, 15, 18, 0, 0)
        venues = create_venues(db_session, count=1)
        tour = create_tour(
            db_session, "Reunion Tour", "Test Artist",
            (base_time - timedelta(days=10)).date(), (base_time + timedelta(days=30)).date(), "cancelled",
        )
        concert = create_concert(
            db_session, tour, venues[0], day_offset=5, ticket_price="80.00", base_time=base_time,
            is_cancelled=True, cancellation_reason="Tour cancelled",
        )
        concert.cancelled_with_tour = True
        db_session.commit()

        response = client.post(f"/api/v1/tours/{tour.id}/uncancel")
        assert response.status_code == 200
        body = response.json()
        assert body["id"] == tour.id
        assert body["status"] == "planned"

        dates_response = client.get(f"/api/v1/tours/{tour.id}/dates")
        assert dates_response.status_code == 200
        restored_concert = next(c for c in dates_response.json() if c["id"] == concert.id)
        assert restored_concert["is_cancelled"] is False

    def test_uncancel_tour_not_cancelled_returns_409(self, client, db_session):
        tour = create_tour(
            db_session, "Active Tour", "Test Artist",
            datetime(2024, 6, 1).date(), datetime(2024, 7, 1).date(), "active",
        )

        response = client.post(f"/api/v1/tours/{tour.id}/uncancel")
        assert response.status_code == 409
        assert "detail" in response.json()

    def test_uncancel_tour_not_found(self, client):
        response = client.post("/api/v1/tours/999/uncancel")
        assert response.status_code == 404


class TestRenameTourEndpoint:
    """Coverage for `PATCH /api/v1/tours/{tour_id}`."""

    def test_rename_tour_returns_200_and_updated_tour(self, client, db_session):
        tour = create_tour(
            db_session, "Old Tour Name", "Test Artist",
            datetime(2024, 6, 1).date(), datetime(2024, 7, 1).date(), "planned",
        )

        response = client.patch(f"/api/v1/tours/{tour.id}", json={"name": "New Tour Name"})

        assert response.status_code == 200
        body = response.json()
        assert body["id"] == tour.id
        assert body["name"] == "New Tour Name"

    def test_rename_tour_is_persisted(self, client, db_session):
        tour = create_tour(
            db_session, "Old Tour Name", "Test Artist",
            datetime(2024, 6, 1).date(), datetime(2024, 7, 1).date(), "planned",
        )

        response = client.patch(f"/api/v1/tours/{tour.id}", json={"name": "Persisted Name"})
        assert response.status_code == 200

        follow_up = client.get(f"/api/v1/tours/{tour.id}")
        assert follow_up.status_code == 200
        assert follow_up.json()["name"] == "Persisted Name"

    def test_rename_tour_leaves_other_fields_unchanged(self, client, db_session):
        base_time = datetime(2024, 6, 15, 18, 0, 0)
        venues = create_venues(db_session, count=1)
        tour = create_tour(
            db_session, "Old Tour Name", "Test Artist",
            (base_time - timedelta(days=10)).date(), (base_time + timedelta(days=30)).date(), "active",
            description="Original description",
        )
        concert = create_concert(
            db_session, tour, venues[0], day_offset=5, ticket_price="80.00", base_time=base_time,
        )

        before = client.get(f"/api/v1/tours/{tour.id}").json()

        response = client.patch(f"/api/v1/tours/{tour.id}", json={"name": "Renamed Tour"})
        assert response.status_code == 200
        after = response.json()

        assert after["name"] == "Renamed Tour"
        for field in ("artist", "start_date", "end_date", "status", "description"):
            assert after[field] == before[field]

        dates_response = client.get(f"/api/v1/tours/{tour.id}/dates")
        assert dates_response.status_code == 200
        assert any(c["id"] == concert.id for c in dates_response.json())

    def test_rename_tour_empty_name_returns_422(self, client, db_session):
        tour = create_tour(
            db_session, "Unchanged Tour", "Test Artist",
            datetime(2024, 6, 1).date(), datetime(2024, 7, 1).date(), "planned",
        )

        response = client.patch(f"/api/v1/tours/{tour.id}", json={"name": ""})

        assert response.status_code == 422
        db_session.refresh(tour)
        assert tour.name == "Unchanged Tour"

    def test_rename_tour_name_too_long_returns_422(self, client, db_session):
        tour = create_tour(
            db_session, "Unchanged Tour", "Test Artist",
            datetime(2024, 6, 1).date(), datetime(2024, 7, 1).date(), "planned",
        )

        response = client.patch(
            f"/api/v1/tours/{tour.id}", json={"name": "A" * (TOUR_NAME_MAX_LENGTH + 1)}
        )

        assert response.status_code == 422
        db_session.refresh(tour)
        assert tour.name == "Unchanged Tour"

    def test_rename_unknown_tour_returns_404(self, client):
        response = client.patch("/api/v1/tours/999999", json={"name": "Anything"})

        assert response.status_code == 404
        assert response.json() == {"detail": "Tour not found"}
