"""Tests for `POST /api/v1/concerts/{id}/uncancel`.

Covers the contract delegated to `src.services.concert_service.uncancel_concert`:
restoring a cancelled, future-dated concert; an unknown id; a concert that
isn't cancelled; a cancelled concert whose date has passed; and that a
second uncancel on an already-restored concert is rejected rather than
treated as a no-op.

Also asserts the route is actually registered on the running app (via the
generated OpenAPI schema), since a route defined on an unregistered router
would otherwise pass every other test here while never being reachable.

Uses real venue/tour fixtures persisted via the ORM so every foreign key is
a genuine committed id, not a hardcoded literal like venue_id=1.
"""

from datetime import datetime, timedelta

from src.models import ConcertStatus
from tests.fixtures.dashboard_fixtures import create_concert, create_tour, create_venues


def _seed_concert(db_session, day_offset, status):
    tour = create_tour(
        db_session,
        name="Uncancel Endpoint Tour",
        artist="Test Artist",
        start_date=(datetime.now() - timedelta(days=30)).date(),
        end_date=(datetime.now() + timedelta(days=90)).date(),
        status="active",
    )
    venue = create_venues(db_session, count=1)[0]
    concert = create_concert(
        db_session, tour, venue, day_offset=day_offset, ticket_price="50.00", base_time=datetime.now(),
    )
    concert.status = status
    db_session.commit()
    db_session.refresh(concert)
    return concert


def test_uncancel_route_is_registered_on_the_running_app(client):
    schema = client.get("/openapi.json").json()
    operations = schema["paths"]["/api/v1/concerts/{concert_id}/uncancel"]
    assert "post" in operations


def test_uncancel_cancelled_future_concert_returns_200_with_restored_status(client, db_session):
    concert = _seed_concert(db_session, day_offset=5, status=ConcertStatus.cancelled)

    response = client.post(f"/api/v1/concerts/{concert.id}/uncancel")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == concert.id
    assert data["status"] == "scheduled"

    get_response = client.get(f"/api/v1/concerts/{concert.id}")
    assert get_response.status_code == 200
    assert get_response.json()["status"] == "scheduled"


def test_uncancel_unknown_concert_returns_404(client, db_session):
    response = client.post("/api/v1/concerts/999999/uncancel")

    assert response.status_code == 404
    assert "detail" in response.json()


def test_uncancel_not_cancelled_concert_returns_409_naming_current_status(client, db_session):
    concert = _seed_concert(db_session, day_offset=5, status=ConcertStatus.scheduled)

    response = client.post(f"/api/v1/concerts/{concert.id}/uncancel")

    assert response.status_code == 409
    detail = response.json()["detail"]
    assert "not cancelled" in detail
    assert "scheduled" in detail


def test_uncancel_cancelled_past_dated_concert_returns_409_naming_the_date(client, db_session):
    concert = _seed_concert(db_session, day_offset=-5, status=ConcertStatus.cancelled)

    response = client.post(f"/api/v1/concerts/{concert.id}/uncancel")

    assert response.status_code == 409
    detail = response.json()["detail"]
    assert "past" in detail
    assert str(concert.date_time) in detail


def test_the_two_409_details_are_distinguishable(client, db_session):
    not_cancelled = _seed_concert(db_session, day_offset=5, status=ConcertStatus.scheduled)
    past_dated = _seed_concert(db_session, day_offset=-5, status=ConcertStatus.cancelled)

    not_cancelled_detail = client.post(f"/api/v1/concerts/{not_cancelled.id}/uncancel").json()["detail"]
    past_date_detail = client.post(f"/api/v1/concerts/{past_dated.id}/uncancel").json()["detail"]

    assert not_cancelled_detail != past_date_detail
    assert "not cancelled" in not_cancelled_detail
    assert "not cancelled" not in past_date_detail
    assert "past" in past_date_detail
    assert "past" not in not_cancelled_detail


def test_second_uncancel_on_already_restored_concert_returns_409(client, db_session):
    concert = _seed_concert(db_session, day_offset=5, status=ConcertStatus.cancelled)

    first_response = client.post(f"/api/v1/concerts/{concert.id}/uncancel")
    assert first_response.status_code == 200

    second_response = client.post(f"/api/v1/concerts/{concert.id}/uncancel")
    assert second_response.status_code == 409
    assert "not cancelled" in second_response.json()["detail"]
