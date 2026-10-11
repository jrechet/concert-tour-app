"""Tests for `POST /api/v1/tours/{tour_id}/uncancel`."""

from datetime import datetime, timedelta

from tests.fixtures.dashboard_fixtures import create_concert, create_tour, create_venues

BASE_TIME = datetime(2024, 6, 15, 18, 0, 0)


def _make_cancelled_tour_with_concerts(db_session, concert_count=2):
    """A `cancelled` tour with `concert_count` concerts flagged
    `cancelled_with_tour`, as `POST /cancel` would have left them."""
    venues = create_venues(db_session, count=concert_count)
    tour = create_tour(
        db_session, "Reunion Tour", "Test Artist",
        (BASE_TIME - timedelta(days=10)).date(), (BASE_TIME + timedelta(days=30)).date(), "cancelled",
    )
    concerts = [
        create_concert(
            db_session, tour, venues[i], day_offset=i + 1, ticket_price="80.00", base_time=BASE_TIME,
            is_cancelled=True, cancellation_reason="Tour cancelled",
        )
        for i in range(concert_count)
    ]
    for concert in concerts:
        concert.cancelled_with_tour = True
    db_session.commit()
    for concert in concerts:
        db_session.refresh(concert)
    return tour, venues, concerts


class TestUncancelTourEndpoint:
    """Coverage for `POST /api/v1/tours/{tour_id}/uncancel`."""

    def test_uncancels_tour_and_tour_cancelled_concerts(self, client, db_session):
        tour, _venues, _concerts = _make_cancelled_tour_with_concerts(db_session, concert_count=2)

        response = client.post(f"/api/v1/tours/{tour.id}/uncancel")
        assert response.status_code == 200
        assert response.json()["status"] == "planned"

        dates_response = client.get(f"/api/v1/tours/{tour.id}/dates")
        assert dates_response.status_code == 200
        dates = dates_response.json()
        assert len(dates) == 2
        for concert in dates:
            assert concert["is_cancelled"] is False
            assert concert["cancellation_reason"] is None

    def test_individually_cancelled_concert_stays_cancelled(self, client, db_session):
        venues = create_venues(db_session, count=2)
        tour = create_tour(
            db_session, "Patchwork Tour", "Test Artist",
            (BASE_TIME - timedelta(days=10)).date(), (BASE_TIME + timedelta(days=30)).date(), "cancelled",
        )
        tour_cancelled_concert = create_concert(
            db_session, tour, venues[0], day_offset=1, ticket_price="80.00", base_time=BASE_TIME,
            is_cancelled=True, cancellation_reason="Tour cancelled",
        )
        tour_cancelled_concert.cancelled_with_tour = True
        individually_cancelled_concert = create_concert(
            db_session, tour, venues[1], day_offset=5, ticket_price="80.00", base_time=BASE_TIME,
            is_cancelled=True, cancellation_reason="User cancelled individually",
        )
        db_session.commit()

        response = client.post(f"/api/v1/tours/{tour.id}/uncancel")
        assert response.status_code == 200

        dates_response = client.get(f"/api/v1/tours/{tour.id}/dates")
        assert dates_response.status_code == 200
        by_id = {concert["id"]: concert for concert in dates_response.json()}

        assert by_id[tour_cancelled_concert.id]["is_cancelled"] is False
        assert by_id[individually_cancelled_concert.id]["is_cancelled"] is True
        assert by_id[individually_cancelled_concert.id]["cancellation_reason"] == "User cancelled individually"

    def test_uncancel_tour_not_cancelled_returns_409(self, client, db_session):
        tour = create_tour(
            db_session, "Planned Tour", "Test Artist",
            BASE_TIME.date(), (BASE_TIME + timedelta(days=30)).date(), "planned",
        )

        response = client.post(f"/api/v1/tours/{tour.id}/uncancel")
        assert response.status_code == 409
        assert "planned" in response.json()["detail"]

    def test_uncancel_unknown_tour_returns_404(self, client):
        response = client.post("/api/v1/tours/999999/uncancel")
        assert response.status_code == 404

    def test_uncancelling_twice_returns_409_on_second_call(self, client, db_session):
        tour, _venues, _concerts = _make_cancelled_tour_with_concerts(db_session, concert_count=1)

        first = client.post(f"/api/v1/tours/{tour.id}/uncancel")
        assert first.status_code == 200
        assert first.json()["status"] == "planned"

        second = client.post(f"/api/v1/tours/{tour.id}/uncancel")
        assert second.status_code == 409
        assert "planned" in second.json()["detail"]
