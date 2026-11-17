"""Tests for `GET /api/v1/concerts/week`.

Concerts are seeded through real `Venue`/`Tour` foreign keys (via the
`tests/fixtures/dashboard_fixtures.py` helpers) rather than hardcoded ids,
and exercised through the public endpoint only (never the private
`get_concerts_for_week` service directly).
"""

from datetime import datetime, timedelta

from src.models import ConcertStatus
from tests.fixtures.dashboard_fixtures import create_concert, create_tour, create_venues

BASE_TIME = datetime.now()


def _make_tour(db_session, name="Week Endpoint Tour"):
    return create_tour(
        db_session, name, "Test Artist",
        (BASE_TIME - timedelta(days=30)).date(),
        (BASE_TIME + timedelta(days=30)).date(),
        "active",
    )


class TestGetConcertsForWeekEndpoint:
    """Coverage for `GET /api/v1/concerts/week`."""

    def test_returns_200_with_ordered_payload_and_venue_details(self, client, db_session):
        venues = create_venues(db_session, count=2)
        tour = _make_tour(db_session)

        later = create_concert(
            db_session, tour, venues[0], day_offset=5, ticket_price="60.00", base_time=BASE_TIME
        )
        soonest = create_concert(
            db_session, tour, venues[1], day_offset=1, ticket_price="60.00", base_time=BASE_TIME
        )

        response = client.get("/api/v1/concerts/week")

        assert response.status_code == 200
        payload = response.json()
        assert [item["id"] for item in payload] == [soonest.id, later.id]
        assert payload[0]["venue_name"] == venues[1].name
        assert payload[0]["venue_city"] == venues[1].city
        assert payload[1]["venue_name"] == venues[0].name
        assert payload[1]["venue_city"] == venues[0].city

    def test_returns_200_with_empty_list_when_no_concert_in_window(self, client):
        response = client.get("/api/v1/concerts/week")

        assert response.status_code == 200
        assert response.json() == []

    def test_cancelled_concert_absent_from_payload(self, client, db_session):
        venue = create_venues(db_session, count=1)[0]
        tour = _make_tour(db_session)

        cancelled = create_concert(
            db_session, tour, venue, day_offset=2, ticket_price="60.00", base_time=BASE_TIME
        )
        cancelled.status = ConcertStatus.cancelled
        db_session.commit()

        scheduled = create_concert(
            db_session, tour, venue, day_offset=3, ticket_price="60.00", base_time=BASE_TIME
        )

        response = client.get("/api/v1/concerts/week")

        assert response.status_code == 200
        ids = [item["id"] for item in response.json()]
        assert ids == [scheduled.id]
        assert cancelled.id not in ids

    def test_concert_outside_window_absent_from_payload(self, client, db_session):
        venue = create_venues(db_session, count=1)[0]
        tour = _make_tour(db_session)

        beyond_window = create_concert(
            db_session, tour, venue, day_offset=10, ticket_price="60.00", base_time=BASE_TIME
        )
        within_window = create_concert(
            db_session, tour, venue, day_offset=2, ticket_price="60.00", base_time=BASE_TIME
        )

        response = client.get("/api/v1/concerts/week")

        assert response.status_code == 200
        ids = [item["id"] for item in response.json()]
        assert ids == [within_window.id]
        assert beyond_window.id not in ids

    def test_week_path_resolves_to_week_handler_not_concert_id_route(self, client):
        response = client.get("/api/v1/concerts/week")

        assert response.status_code == 200
        assert isinstance(response.json(), list)
