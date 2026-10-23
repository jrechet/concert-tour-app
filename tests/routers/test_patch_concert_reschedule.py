"""Tests for `PATCH /api/v1/concerts/{id}`, which reschedules a concert
using the `ConcertReschedule` request schema.

Concerts are seeded through real venue/tour foreign keys rather than
hardcoded ids, matching the project's fixture conventions.
"""

from datetime import datetime, timedelta, timezone

from tests.fixtures.dashboard_fixtures import create_concert, create_tour, create_venues

BASE_TIME = datetime.now(timezone.utc).replace(microsecond=0, tzinfo=None) + timedelta(days=30)


def _seed_concert(db_session, name="Reschedule Tour", **concert_kwargs):
    tour = create_tour(
        db_session,
        name=name,
        artist="Test Artist",
        start_date=(datetime.now() - timedelta(days=1)).date(),
        end_date=(datetime.now() + timedelta(days=90)).date(),
        status="active",
    )
    venue = create_venues(db_session, count=1)[0]
    concert = create_concert(
        db_session, tour, venue, day_offset=0, ticket_price="80.00", base_time=BASE_TIME, **concert_kwargs
    )
    return concert


class TestPatchConcertReschedule:
    """Coverage for `PATCH /api/v1/concerts/{id}`."""

    def test_future_date_time_returns_200_with_updated_body(self, client, db_session):
        concert = _seed_concert(db_session)
        new_date_time = BASE_TIME + timedelta(days=10)

        response = client.patch(
            f"/api/v1/concerts/{concert.id}", json={"date_time": new_date_time.isoformat()}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == concert.id
        assert data["date_time"] == new_date_time.isoformat()

    def test_change_is_persisted_and_visible_via_get(self, client, db_session):
        concert = _seed_concert(db_session, "Persistence Tour")
        new_date_time = BASE_TIME + timedelta(days=20)

        patch_response = client.patch(
            f"/api/v1/concerts/{concert.id}", json={"date_time": new_date_time.isoformat()}
        )
        assert patch_response.status_code == 200

        get_response = client.get(f"/api/v1/concerts/{concert.id}")
        assert get_response.status_code == 200
        assert get_response.json()["date_time"] == new_date_time.isoformat()

    def test_past_date_time_returns_422_and_does_not_mutate(self, client, db_session):
        concert = _seed_concert(db_session, "Past Date Tour")
        original_date_time = concert.date_time
        past_date_time = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=1)

        response = client.patch(
            f"/api/v1/concerts/{concert.id}", json={"date_time": past_date_time.isoformat()}
        )

        assert response.status_code == 422
        db_session.refresh(concert)
        assert concert.date_time == original_date_time

    def test_cancelled_concert_returns_409_with_conflict_detail_and_is_not_moved(self, client, db_session):
        concert = _seed_concert(
            db_session, "Cancelled Tour", is_cancelled=True, cancellation_reason="Weather"
        )
        original_date_time = concert.date_time
        new_date_time = BASE_TIME + timedelta(days=10)

        response = client.patch(
            f"/api/v1/concerts/{concert.id}", json={"date_time": new_date_time.isoformat()}
        )

        assert response.status_code == 409
        assert response.json()["detail"] == f"Concert {concert.id} is cancelled"
        db_session.refresh(concert)
        assert concert.date_time == original_date_time

    def test_unknown_id_returns_404(self, client):
        new_date_time = BASE_TIME + timedelta(days=10)

        response = client.patch(
            "/api/v1/concerts/999999", json={"date_time": new_date_time.isoformat()}
        )

        assert response.status_code == 404
        assert response.json()["detail"] == "Concert not found"

    def test_non_integer_id_returns_422(self, client):
        new_date_time = BASE_TIME + timedelta(days=10)

        response = client.patch(
            "/api/v1/concerts/not-an-id", json={"date_time": new_date_time.isoformat()}
        )

        assert response.status_code == 422

    def test_missing_body_returns_422(self, client, db_session):
        concert = _seed_concert(db_session, "Missing Body Tour")

        response = client.patch(f"/api/v1/concerts/{concert.id}")

        assert response.status_code == 422

    def test_empty_body_returns_422(self, client, db_session):
        concert = _seed_concert(db_session, "Empty Body Tour")

        response = client.patch(f"/api/v1/concerts/{concert.id}", json={})

        assert response.status_code == 422
