"""Tests for the `PATCH /api/v1/concerts/{id}` reschedule endpoint.

Uses real venue/tour/concert fixtures persisted via the ORM so every
foreign key is a genuine committed id, not a hardcoded literal like
venue_id=1.
"""

from datetime import datetime, timedelta, timezone

from tests.fixtures.dashboard_fixtures import create_concert, create_tour, create_venues

BASE_TIME = datetime.now(timezone.utc).replace(microsecond=0, tzinfo=None) + timedelta(days=30)


def _seed_tour_and_venue(db_session, name="Reschedule API Tour"):
    tour = create_tour(
        db_session,
        name=name,
        artist="Test Artist",
        start_date=(datetime.now() - timedelta(days=1)).date(),
        end_date=(datetime.now() + timedelta(days=90)).date(),
        status="active",
    )
    venue = create_venues(db_session, count=1)[0]
    return tour, venue


class TestRescheduleConcertEndpoint:
    def test_reschedule_with_valid_future_date_returns_200_and_updated_concert(self, client, db_session):
        tour, venue = _seed_tour_and_venue(db_session)
        concert = create_concert(
            db_session, tour, venue, day_offset=0, ticket_price="80.00", base_time=BASE_TIME,
        )
        new_date_time = BASE_TIME + timedelta(days=10)

        response = client.patch(
            f"/api/v1/concerts/{concert.id}", json={"date_time": new_date_time.isoformat()}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == concert.id
        assert data["date_time"] == new_date_time.isoformat()

    def test_reschedule_to_past_date_returns_422(self, client, db_session):
        tour, venue = _seed_tour_and_venue(db_session, "Past Date API Tour")
        concert = create_concert(
            db_session, tour, venue, day_offset=0, ticket_price="80.00", base_time=BASE_TIME,
        )
        past_date_time = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=1)

        response = client.patch(
            f"/api/v1/concerts/{concert.id}", json={"date_time": past_date_time.isoformat()}
        )

        assert response.status_code == 422

    def test_reschedule_cancelled_concert_returns_409(self, client, db_session):
        tour, venue = _seed_tour_and_venue(db_session, "Cancelled API Tour")
        concert = create_concert(
            db_session, tour, venue, day_offset=0, ticket_price="80.00", base_time=BASE_TIME,
            is_cancelled=True, cancellation_reason="Weather",
        )
        new_date_time = BASE_TIME + timedelta(days=10)

        response = client.patch(
            f"/api/v1/concerts/{concert.id}", json={"date_time": new_date_time.isoformat()}
        )

        assert response.status_code == 409

    def test_reschedule_unknown_concert_returns_404(self, client, db_session):
        new_date_time = BASE_TIME + timedelta(days=10)

        response = client.patch(
            "/api/v1/concerts/999999", json={"date_time": new_date_time.isoformat()}
        )

        assert response.status_code == 404
