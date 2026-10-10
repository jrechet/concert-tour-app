"""Integration tests for DELETE /api/v1/concerts/{id}/lineup, exercised
against real seeded tour/venue/concert fixtures (real foreign keys, not
hardcoded IDs).
"""

from datetime import datetime, timedelta

from src.models import LineupEntry
from tests.fixtures.dashboard_fixtures import create_concert, create_tour, create_venues


def _seed_concert_with_lineup(db_session, num_entries=3):
    tour = create_tour(
        db_session,
        name="Lineup Clear Test Tour",
        artist="Test Artist",
        start_date=(datetime.now() - timedelta(days=1)).date(),
        end_date=(datetime.now() + timedelta(days=90)).date(),
        status="active",
    )
    venue = create_venues(db_session, count=1)[0]
    concert = create_concert(
        db_session,
        tour,
        venue,
        day_offset=10,
        ticket_price="50.00",
        base_time=datetime.now() + timedelta(days=30),
    )

    entries = [
        LineupEntry(concert_id=concert.id, artist_name=f"Opener {i}", set_order=i + 1)
        for i in range(num_entries)
    ]
    db_session.add_all(entries)
    db_session.commit()

    return concert


def test_delete_lineup_returns_204_and_clears_acts(client, db_session):
    concert = _seed_concert_with_lineup(db_session)

    response = client.delete(f"/api/v1/concerts/{concert.id}/lineup")

    assert response.status_code == 204
    assert response.content == b""

    lineup_response = client.get(f"/api/v1/concerts/{concert.id}/lineup")
    assert lineup_response.status_code == 200
    assert lineup_response.json() == []


def test_delete_lineup_unknown_concert_returns_404(client, db_session):
    concert = _seed_concert_with_lineup(db_session)
    nonexistent_id = concert.id + 1

    response = client.delete(f"/api/v1/concerts/{nonexistent_id}/lineup")

    assert response.status_code == 404
    assert response.json()["detail"] == "Concert not found"


def test_delete_lineup_concert_record_preserved_after_clear(client, db_session):
    concert = _seed_concert_with_lineup(db_session)

    response = client.delete(f"/api/v1/concerts/{concert.id}/lineup")
    assert response.status_code == 204

    get_response = client.get(f"/api/v1/concerts/{concert.id}")
    assert get_response.status_code == 200
    assert get_response.json()["id"] == concert.id
