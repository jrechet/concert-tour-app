"""Tests for the concert cancel/uncancel API endpoints and the
`include_cancelled` filter on the concerts list endpoint.

Uses real venue/tour/concert fixtures persisted via the ORM so every
foreign key is a genuine committed id, not a hardcoded literal like
venue_id=1.
"""

from datetime import datetime, timedelta

from tests.fixtures.dashboard_fixtures import create_concert, create_tour, create_venues


def _seed_tour_and_venue(db_session, name="Cancellation Tour"):
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


class TestCancelConcert:
    def test_cancel_with_valid_reason_returns_200_and_sets_fields(self, client, db_session):
        tour, venue = _seed_tour_and_venue(db_session)
        concert = create_concert(
            db_session, tour, venue, day_offset=5, ticket_price="50.00", base_time=datetime.now(),
        )

        response = client.post(
            f"/api/v1/concerts/{concert.id}/cancel", json={"reason": "Artist illness"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["is_cancelled"] is True
        assert data["cancellation_reason"] == "Artist illness"

    def test_cancel_with_missing_reason_returns_422(self, client, db_session):
        tour, venue = _seed_tour_and_venue(db_session)
        concert = create_concert(
            db_session, tour, venue, day_offset=5, ticket_price="50.00", base_time=datetime.now(),
        )

        response = client.post(f"/api/v1/concerts/{concert.id}/cancel", json={})

        assert response.status_code == 422

    def test_cancel_with_empty_reason_returns_422(self, client, db_session):
        tour, venue = _seed_tour_and_venue(db_session)
        concert = create_concert(
            db_session, tour, venue, day_offset=5, ticket_price="50.00", base_time=datetime.now(),
        )

        response = client.post(f"/api/v1/concerts/{concert.id}/cancel", json={"reason": "   "})

        assert response.status_code == 422

    def test_cancel_already_cancelled_returns_409(self, client, db_session):
        tour, venue = _seed_tour_and_venue(db_session)
        concert = create_concert(
            db_session, tour, venue, day_offset=5, ticket_price="50.00", base_time=datetime.now(),
            is_cancelled=True, cancellation_reason="Weather",
        )

        response = client.post(
            f"/api/v1/concerts/{concert.id}/cancel", json={"reason": "Another reason"}
        )

        assert response.status_code == 409

    def test_cancel_unknown_concert_returns_404(self, client, db_session):
        response = client.post("/api/v1/concerts/999999/cancel", json={"reason": "Weather"})

        assert response.status_code == 404


class TestUncancelConcert:
    def test_uncancel_cancelled_concert_returns_200_and_clears_fields(self, client, db_session):
        tour, venue = _seed_tour_and_venue(db_session)
        concert = create_concert(
            db_session, tour, venue, day_offset=5, ticket_price="50.00", base_time=datetime.now(),
            is_cancelled=True, cancellation_reason="Weather",
        )

        response = client.post(f"/api/v1/concerts/{concert.id}/uncancel")

        assert response.status_code == 200
        data = response.json()
        assert data["is_cancelled"] is False
        assert data["cancellation_reason"] is None

    def test_uncancel_non_cancelled_concert_returns_409(self, client, db_session):
        tour, venue = _seed_tour_and_venue(db_session)
        concert = create_concert(
            db_session, tour, venue, day_offset=5, ticket_price="50.00", base_time=datetime.now(),
        )

        response = client.post(f"/api/v1/concerts/{concert.id}/uncancel")

        assert response.status_code == 409

    def test_uncancel_unknown_concert_returns_404(self, client, db_session):
        response = client.post("/api/v1/concerts/999999/uncancel")

        assert response.status_code == 404


class TestListConcertsIncludeCancelledFilter:
    def test_default_includes_cancelled(self, client, db_session):
        tour, venue = _seed_tour_and_venue(db_session)
        create_concert(
            db_session, tour, venue, day_offset=5, ticket_price="50.00", base_time=datetime.now(),
            is_cancelled=True, cancellation_reason="Weather",
        )
        create_concert(
            db_session, tour, venue, day_offset=10, ticket_price="50.00", base_time=datetime.now(),
        )

        response = client.get("/api/v1/concerts/")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

    def test_include_cancelled_true_returns_cancelled(self, client, db_session):
        tour, venue = _seed_tour_and_venue(db_session)
        create_concert(
            db_session, tour, venue, day_offset=5, ticket_price="50.00", base_time=datetime.now(),
            is_cancelled=True, cancellation_reason="Weather",
        )

        response = client.get("/api/v1/concerts/", params={"include_cancelled": "true"})

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["is_cancelled"] is True

    def test_include_cancelled_false_excludes_cancelled(self, client, db_session):
        tour, venue = _seed_tour_and_venue(db_session)
        create_concert(
            db_session, tour, venue, day_offset=5, ticket_price="50.00", base_time=datetime.now(),
            is_cancelled=True, cancellation_reason="Weather",
        )
        active = create_concert(
            db_session, tour, venue, day_offset=10, ticket_price="50.00", base_time=datetime.now(),
        )

        response = client.get("/api/v1/concerts/", params={"include_cancelled": "false"})

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["id"] == active.id
        assert data[0]["is_cancelled"] is False

    def test_include_cancelled_false_pagination_still_works(self, client, db_session):
        tour, venue = _seed_tour_and_venue(db_session)
        create_concert(
            db_session, tour, venue, day_offset=1, ticket_price="50.00", base_time=datetime.now(),
            is_cancelled=True, cancellation_reason="Weather",
        )
        for i in range(3):
            create_concert(
                db_session, tour, venue, day_offset=10 + i, ticket_price="50.00",
                base_time=datetime.now(),
            )

        response = client.get(
            "/api/v1/concerts/", params={"include_cancelled": "false", "skip": 1, "limit": 1}
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
