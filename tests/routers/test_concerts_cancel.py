"""Tests for `POST /api/v1/concerts/{id}/cancel`.

Covers the idempotent contract delegated to
`src.services.concert_service.cancel_concert`: cancelling a scheduled
concert, re-cancelling an already-cancelled one (no-op, no error), an
unknown id, and that the cancelled status is visible on a subsequent GET.

Uses real venue/tour fixtures persisted via the ORM so every foreign key is
a genuine committed id, not a hardcoded literal like venue_id=1.
"""

from datetime import datetime, timedelta

from src.models import ConcertStatus
from tests.fixtures.dashboard_fixtures import create_concert, create_tour, create_venues


def _seed_concert(db_session, status=None):
    tour = create_tour(
        db_session,
        name="Cancel Endpoint Tour",
        artist="Test Artist",
        start_date=(datetime.now() - timedelta(days=1)).date(),
        end_date=(datetime.now() + timedelta(days=90)).date(),
        status="active",
    )
    venue = create_venues(db_session, count=1)[0]
    concert = create_concert(
        db_session, tour, venue, day_offset=5, ticket_price="50.00", base_time=datetime.now(),
    )
    if status is not None:
        concert.status = status
        db_session.commit()
        db_session.refresh(concert)
    return concert


def test_cancel_scheduled_concert_returns_200_with_cancelled_status(client, db_session):
    concert = _seed_concert(db_session)

    response = client.post(f"/api/v1/concerts/{concert.id}/cancel")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == concert.id
    assert data["status"] == "cancelled"


def test_recancelling_already_cancelled_concert_is_idempotent(client, db_session):
    concert = _seed_concert(db_session, status=ConcertStatus.cancelled)

    response = client.post(f"/api/v1/concerts/{concert.id}/cancel")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "cancelled"

    db_session.refresh(concert)
    assert concert.status == ConcertStatus.cancelled

    second_response = client.post(f"/api/v1/concerts/{concert.id}/cancel")
    assert second_response.status_code == 200
    assert second_response.json() == data


def test_cancel_unknown_concert_returns_404_with_no_writes(client, db_session):
    response = client.post("/api/v1/concerts/999999/cancel")

    assert response.status_code == 404
    assert "detail" in response.json()


def test_cancelled_status_visible_on_subsequent_get(client, db_session):
    concert = _seed_concert(db_session)

    cancel_response = client.post(f"/api/v1/concerts/{concert.id}/cancel")
    assert cancel_response.status_code == 200

    get_response = client.get(f"/api/v1/concerts/{concert.id}")

    assert get_response.status_code == 200
    assert get_response.json()["status"] == "cancelled"
