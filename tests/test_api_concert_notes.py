"""End-to-end coverage for `notes` on `GET /api/v1/concerts/{id}`: it must
be present in the JSON response (null by default, the stored string once
set), and an unknown id must still 404. Seeded through real `Tour`/`Venue`
foreign keys (via `tests/fixtures/dashboard_fixtures.py`), matching the
convention used by `tests/api/test_concerts.py`.
"""

from datetime import datetime, timedelta

from tests.fixtures.dashboard_fixtures import create_concert, create_tour, create_venues


def _seed_concert(db_session):
    tour = create_tour(
        db_session,
        name="Countdown Tour",
        artist="Test Artist",
        start_date=(datetime.now() - timedelta(days=1)).date(),
        end_date=(datetime.now() + timedelta(days=90)).date(),
        status="active",
    )
    venue = create_venues(db_session, count=1)[0]
    return create_concert(
        db_session, tour, venue, day_offset=30, ticket_price="50.00", base_time=datetime.now()
    )


def test_get_concert_notes_null_by_default(client, db_session):
    concert = _seed_concert(db_session)

    response = client.get(f"/api/v1/concerts/{concert.id}")

    assert response.status_code == 200
    assert response.json()["notes"] is None


def test_get_concert_notes_after_put_reflects_value(client, db_session):
    concert = _seed_concert(db_session)

    concert.notes = "VIP meet-and-greet before doors open"
    db_session.commit()

    response = client.get(f"/api/v1/concerts/{concert.id}")

    assert response.status_code == 200
    assert response.json()["notes"] == "VIP meet-and-greet before doors open"


def test_get_concert_unknown_still_404(client, db_session):
    response = client.get("/api/v1/concerts/999999")

    assert response.status_code == 404
