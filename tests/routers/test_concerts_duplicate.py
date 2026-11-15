"""Tests for `POST /api/v1/concerts/{id}/duplicate`, which duplicates a
concert using the `ConcertDuplicateRequest` request schema.

Concerts are seeded through real venue/tour foreign keys rather than
hardcoded ids, matching the project's fixture conventions.
"""

from datetime import datetime, timedelta, timezone

from src.models import LineupEntry
from tests.fixtures.dashboard_fixtures import create_concert, create_tour, create_venues

BASE_TIME = datetime.now(timezone.utc).replace(microsecond=0, tzinfo=None) + timedelta(days=30)


def _seed_concert(db_session, name="Duplicate Tour", **concert_kwargs):
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


class TestDuplicateConcertEndpoint:
    """Coverage for `POST /api/v1/concerts/{id}/duplicate`."""

    def test_future_date_time_returns_201_with_duplicate_body(self, client, db_session):
        concert = _seed_concert(db_session)
        entry = LineupEntry(concert_id=concert.id, artist_name="Opening Act", set_order=1)
        db_session.add(entry)
        db_session.commit()
        new_date_time = BASE_TIME + timedelta(days=10)

        response = client.post(
            f"/api/v1/concerts/{concert.id}/duplicate", json={"date_time": new_date_time.isoformat()}
        )

        assert response.status_code == 201
        body = response.json()
        assert body["id"] != concert.id
        assert body["tour_id"] == concert.tour_id
        assert body["venue_id"] == concert.venue_id
        assert body["ticket_price"] == "80.00"
        assert body["tickets_sold"] == 0
        assert body["is_cancelled"] is False
        assert body["date_time"] == new_date_time.isoformat()

        lineup_response = client.get(f"/api/v1/concerts/{body['id']}/lineup")
        assert lineup_response.status_code == 200
        assert [item["artist_name"] for item in lineup_response.json()] == ["Opening Act"]

    def test_past_date_time_returns_422_and_creates_nothing(self, client, db_session):
        concert = _seed_concert(db_session, "Past Date Tour")
        past_date_time = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=1)

        response = client.post(
            f"/api/v1/concerts/{concert.id}/duplicate", json={"date_time": past_date_time.isoformat()}
        )

        assert response.status_code == 422

    def test_conflicting_date_time_at_same_venue_returns_409_and_creates_nothing(self, client, db_session):
        concert = _seed_concert(db_session, "Conflict Tour")
        other_tour = create_tour(
            db_session,
            name="Other Tour",
            artist="Other Artist",
            start_date=(datetime.now() - timedelta(days=1)).date(),
            end_date=(datetime.now() + timedelta(days=90)).date(),
            status="active",
        )
        conflicting_time = BASE_TIME + timedelta(days=5)
        create_concert(
            db_session, other_tour, concert.venue, day_offset=5, ticket_price="60.00", base_time=BASE_TIME
        )

        response = client.post(
            f"/api/v1/concerts/{concert.id}/duplicate", json={"date_time": conflicting_time.isoformat()}
        )

        assert response.status_code == 409
        assert "Concert" not in response.json()["detail"]

        all_concerts = client.get("/api/v1/concerts/", params={"page_size": 100}).json()
        assert len(all_concerts) == 2

    def test_unknown_concert_id_returns_404(self, client):
        new_date_time = BASE_TIME + timedelta(days=10)

        response = client.post(
            f"/api/v1/concerts/999999/duplicate", json={"date_time": new_date_time.isoformat()}
        )

        assert response.status_code == 404
        assert response.json()["detail"] == "Concert not found"

    def test_missing_body_returns_422(self, client, db_session):
        concert = _seed_concert(db_session, "Missing Body Tour")

        response = client.post(f"/api/v1/concerts/{concert.id}/duplicate")

        assert response.status_code == 422

    def test_malformed_date_time_returns_422(self, client, db_session):
        concert = _seed_concert(db_session, "Malformed Body Tour")

        response = client.post(
            f"/api/v1/concerts/{concert.id}/duplicate", json={"date_time": "not-a-date"}
        )

        assert response.status_code == 422

    def test_duplicate_leaves_source_concert_untouched(self, client, db_session):
        concert = _seed_concert(db_session, "Untouched Tour", tickets_sold=10)
        original_date_time = concert.date_time
        original_ticket_price = concert.ticket_price
        new_date_time = BASE_TIME + timedelta(days=10)

        response = client.post(
            f"/api/v1/concerts/{concert.id}/duplicate", json={"date_time": new_date_time.isoformat()}
        )
        assert response.status_code == 201

        get_response = client.get(f"/api/v1/concerts/{concert.id}")
        assert get_response.status_code == 200
        body = get_response.json()
        assert body["date_time"] == original_date_time.isoformat()
        assert body["ticket_price"] == str(original_ticket_price)
        assert body["tickets_sold"] == 10
        assert body["is_cancelled"] is False
