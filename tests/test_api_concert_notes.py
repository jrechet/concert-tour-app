"""Tests for the `PUT /api/v1/concerts/{id}/notes` endpoint.

Uses real venue/tour/concert fixtures persisted via the ORM so every
foreign key is a genuine committed id, not a hardcoded literal like
venue_id=1.
"""

from datetime import datetime, timedelta, timezone

from tests.fixtures.dashboard_fixtures import create_concert, create_tour, create_venues

BASE_TIME = datetime.now(timezone.utc).replace(microsecond=0, tzinfo=None) + timedelta(days=30)


def _seed_concert(db_session, notes=None):
    tour = create_tour(
        db_session,
        name="Notes API Tour",
        artist="Test Artist",
        start_date=(datetime.now() - timedelta(days=1)).date(),
        end_date=(datetime.now() + timedelta(days=90)).date(),
        status="active",
    )
    venue = create_venues(db_session, count=1)[0]
    concert = create_concert(
        db_session, tour, venue, day_offset=0, ticket_price="80.00", base_time=BASE_TIME,
    )
    if notes is not None:
        concert.notes = notes
        db_session.commit()
        db_session.refresh(concert)
    return concert


def test_put_notes_success_200(client, db_session):
    concert = _seed_concert(db_session)

    response = client.put(f"/api/v1/concerts/{concert.id}/notes", json={"notes": "Opening act TBD"})

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == concert.id
    assert data["notes"] == "Opening act TBD"


def test_put_notes_too_long_422(client, db_session):
    concert = _seed_concert(db_session)
    too_long = "a" * 501

    response = client.put(f"/api/v1/concerts/{concert.id}/notes", json={"notes": too_long})

    assert response.status_code == 422


def test_put_notes_exactly_500_ok(client, db_session):
    concert = _seed_concert(db_session)
    exactly_500 = "a" * 500

    response = client.put(f"/api/v1/concerts/{concert.id}/notes", json={"notes": exactly_500})

    assert response.status_code == 200
    assert response.json()["notes"] == exactly_500


def test_put_notes_unknown_concert_404(client, db_session):
    response = client.put("/api/v1/concerts/999999/notes", json={"notes": "Anything"})

    assert response.status_code == 404


def test_put_notes_moves_from_null_to_provided_string(client, db_session):
    concert = _seed_concert(db_session)
    assert concert.notes is None

    response = client.put(f"/api/v1/concerts/{concert.id}/notes", json={"notes": "New note"})

    assert response.status_code == 200
    assert response.json()["notes"] == "New note"
