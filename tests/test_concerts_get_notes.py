"""Coverage for `notes` on `GET /api/v1/concerts/{id}`: null by default,
the exact stored string once set (including a 500-character value), a 404
for an unknown id, and a regression check that the previously documented
detail payload keys are all still present.

Concerts are seeded via real `Tour`/`Venue` foreign keys (through
`tests/fixtures/dashboard_fixtures.py`) rather than hardcoded ids, matching
the convention used by `tests/test_api_concert_notes.py`.
"""

from datetime import datetime, timedelta, timezone

from tests.fixtures.dashboard_fixtures import create_concert, create_tour, create_venues

BASE_TIME = datetime.now(timezone.utc).replace(microsecond=0, tzinfo=None) + timedelta(days=30)

PREVIOUSLY_DOCUMENTED_KEYS = {
    "id",
    "tour_id",
    "venue_id",
    "venue_name",
    "venue_city",
    "date_time",
    "days_until_concert",
    "ticket_price",
    "tickets_sold",
    "remaining_tickets",
    "tickets_remaining",
    "sold_out",
    "is_sold_out",
    "is_almost_sold_out",
    "is_cancelled",
    "cancellation_reason",
}


def _seed_concert(db_session):
    tour = create_tour(
        db_session,
        name="Get Notes Tour",
        artist="Test Artist",
        start_date=(datetime.now() - timedelta(days=1)).date(),
        end_date=(datetime.now() + timedelta(days=90)).date(),
        status="active",
    )
    venue = create_venues(db_session, count=1)[0]
    return create_concert(db_session, tour, venue, day_offset=0, ticket_price="80.00", base_time=BASE_TIME)


def test_get_concert_notes_null_for_fresh_concert(client, db_session):
    concert = _seed_concert(db_session)

    response = client.get(f"/api/v1/concerts/{concert.id}")

    assert response.status_code == 200
    assert response.json()["notes"] is None


def test_get_concert_notes_exact_value_after_put(client, db_session):
    concert = _seed_concert(db_session)

    put_response = client.put(f"/api/v1/concerts/{concert.id}/notes", json={"notes": "VIP meet-and-greet before doors"})
    assert put_response.status_code == 200

    response = client.get(f"/api/v1/concerts/{concert.id}")

    assert response.status_code == 200
    assert response.json()["notes"] == "VIP meet-and-greet before doors"


def test_get_concert_notes_exact_500_character_value(client, db_session):
    concert = _seed_concert(db_session)
    notes = "n" * 500

    put_response = client.put(f"/api/v1/concerts/{concert.id}/notes", json={"notes": notes})
    assert put_response.status_code == 200

    response = client.get(f"/api/v1/concerts/{concert.id}")

    assert response.status_code == 200
    assert response.json()["notes"] == notes
    assert len(response.json()["notes"]) == 500


def test_get_concert_unknown_id_returns_404(client, db_session):
    response = client.get("/api/v1/concerts/999999")

    assert response.status_code == 404


def test_get_concert_detail_keys_unchanged(client, db_session):
    concert = _seed_concert(db_session)

    response = client.get(f"/api/v1/concerts/{concert.id}")

    assert response.status_code == 200
    data = response.json()
    assert PREVIOUSLY_DOCUMENTED_KEYS.issubset(data.keys())
    assert "notes" in data
