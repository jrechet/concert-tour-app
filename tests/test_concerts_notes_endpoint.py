"""Coverage for `PUT /api/v1/concerts/{id}/notes`, driven through the API
test client against the public endpoint rather than any private helper.

Concerts are seeded via real `Tour`/`Venue` foreign keys (through
`tests/fixtures/dashboard_fixtures.py`), matching the convention used by
`tests/test_api_concert_notes.py`.
"""

from datetime import datetime, timedelta, timezone

from src.models import Concert
from tests.fixtures.dashboard_fixtures import create_concert, create_tour, create_venues

BASE_TIME = datetime.now(timezone.utc).replace(microsecond=0, tzinfo=None) + timedelta(days=30)


def _seed_concert(db_session):
    tour = create_tour(
        db_session,
        name="Notes Endpoint Tour",
        artist="Test Artist",
        start_date=(datetime.now() - timedelta(days=1)).date(),
        end_date=(datetime.now() + timedelta(days=90)).date(),
        status="active",
    )
    venue = create_venues(db_session, count=1)[0]
    return create_concert(db_session, tour, venue, day_offset=0, ticket_price="80.00", base_time=BASE_TIME)


def test_put_notes_returns_200_and_body(client, db_session):
    concert = _seed_concert(db_session)

    response = client.put(f"/api/v1/concerts/{concert.id}/notes", json={"notes": "Soundcheck at 4pm"})

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == concert.id
    assert data["notes"] == "Soundcheck at 4pm"


def test_put_notes_persists_and_is_visible_on_subsequent_read(client, db_session):
    concert = _seed_concert(db_session)

    put_response = client.put(f"/api/v1/concerts/{concert.id}/notes", json={"notes": "Load-in at noon"})
    assert put_response.status_code == 200

    get_response = client.get(f"/api/v1/concerts/{concert.id}")
    assert get_response.status_code == 200
    assert get_response.json()["notes"] == "Load-in at noon"


def test_put_notes_501_characters_returns_422(client, db_session):
    concert = _seed_concert(db_session)

    response = client.put(f"/api/v1/concerts/{concert.id}/notes", json={"notes": "a" * 501})

    assert response.status_code == 422


def test_put_notes_exactly_500_characters_returns_200(client, db_session):
    concert = _seed_concert(db_session)
    notes = "a" * 500

    response = client.put(f"/api/v1/concerts/{concert.id}/notes", json={"notes": notes})

    assert response.status_code == 200
    assert response.json()["notes"] == notes


def test_put_notes_missing_field_returns_422(client, db_session):
    concert = _seed_concert(db_session)

    response = client.put(f"/api/v1/concerts/{concert.id}/notes", json={})

    assert response.status_code == 422


def test_put_notes_null_returns_422(client, db_session):
    concert = _seed_concert(db_session)

    response = client.put(f"/api/v1/concerts/{concert.id}/notes", json={"notes": None})

    assert response.status_code == 422


def test_put_notes_non_string_returns_422(client, db_session):
    concert = _seed_concert(db_session)

    response = client.put(f"/api/v1/concerts/{concert.id}/notes", json={"notes": 12345})

    assert response.status_code == 422


def test_put_notes_unknown_concert_returns_404(client, db_session):
    response = client.put("/api/v1/concerts/999999/notes", json={"notes": "Anything"})

    assert response.status_code == 404


def test_put_notes_unknown_concert_creates_nothing(client, db_session):
    count_before = db_session.query(Concert).count()

    response = client.put("/api/v1/concerts/999999/notes", json={"notes": "Anything"})

    assert response.status_code == 404
    assert db_session.query(Concert).count() == count_before


def test_put_notes_overwrites_rather_than_appends(client, db_session):
    concert = _seed_concert(db_session)

    first = client.put(f"/api/v1/concerts/{concert.id}/notes", json={"notes": "First note"})
    assert first.status_code == 200
    assert first.json()["notes"] == "First note"

    second = client.put(f"/api/v1/concerts/{concert.id}/notes", json={"notes": "Second note"})
    assert second.status_code == 200
    assert second.json()["notes"] == "Second note"

    get_response = client.get(f"/api/v1/concerts/{concert.id}")
    assert get_response.json()["notes"] == "Second note"
