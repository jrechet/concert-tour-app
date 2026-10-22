"""Tests for DELETE /api/v1/concerts/{concert_id}/lineup/{entry_id}.

Builds venue -> two concerts -> lineup entries through real, committed
foreign-key relationships (never hardcoded ids), then exercises every
status code the endpoint can return.
"""

from datetime import datetime, timedelta

from src.models import LineupEntry
from tests.fixtures.dashboard_fixtures import create_concert, create_tour, create_venues


def _build_two_concerts(db_session):
    """One venue, one tour, two concerts -- for the "entry belongs to
    another concert" case."""
    base_time = datetime(2026, 11, 1, 20, 0, 0)
    venue = create_venues(db_session, count=1)[0]
    tour = create_tour(
        db_session,
        name="Delete Lineup Test Tour",
        artist="Delete Lineup Test Artist",
        start_date=base_time.date(),
        end_date=(base_time + timedelta(days=10)).date(),
        status="planned",
    )
    concert_a = create_concert(
        db_session, tour, venue, day_offset=0, ticket_price="50.00", base_time=base_time
    )
    concert_b = create_concert(
        db_session, tour, venue, day_offset=1, ticket_price="50.00", base_time=base_time
    )
    return concert_a, concert_b


def _add_lineup_entry(db_session, concert, artist_name="Opening Act", set_order=1):
    entry = LineupEntry(concert_id=concert.id, artist_name=artist_name, set_order=set_order)
    db_session.add(entry)
    db_session.commit()
    db_session.refresh(entry)
    return entry


def test_delete_existing_entry_returns_204_and_removes_it_from_lineup(client, db_session):
    concert_a, _ = _build_two_concerts(db_session)
    entry = _add_lineup_entry(db_session, concert_a)

    response = client.delete(f"/api/v1/concerts/{concert_a.id}/lineup/{entry.id}")

    assert response.status_code == 204
    assert response.content == b""

    lineup_response = client.get(f"/api/v1/concerts/{concert_a.id}/lineup")
    assert lineup_response.status_code == 200
    assert entry.id not in [item["id"] for item in lineup_response.json()]


def test_delete_same_entry_twice_returns_204_then_404(client, db_session):
    concert_a, _ = _build_two_concerts(db_session)
    entry = _add_lineup_entry(db_session, concert_a)

    first_response = client.delete(f"/api/v1/concerts/{concert_a.id}/lineup/{entry.id}")
    second_response = client.delete(f"/api/v1/concerts/{concert_a.id}/lineup/{entry.id}")

    assert first_response.status_code == 204
    assert second_response.status_code == 404


def test_delete_entry_for_unknown_concert_returns_404(client, db_session):
    _build_two_concerts(db_session)
    nonexistent_concert_id = 999999

    response = client.delete(f"/api/v1/concerts/{nonexistent_concert_id}/lineup/1")

    assert response.status_code == 404


def test_delete_unknown_entry_on_existing_concert_returns_404(client, db_session):
    concert_a, _ = _build_two_concerts(db_session)
    nonexistent_entry_id = 999999

    response = client.delete(f"/api/v1/concerts/{concert_a.id}/lineup/{nonexistent_entry_id}")

    assert response.status_code == 404


def test_delete_entry_belonging_to_another_concert_returns_404_and_entry_still_readable(
    client, db_session
):
    concert_a, concert_b = _build_two_concerts(db_session)
    entry = _add_lineup_entry(db_session, concert_b)

    response = client.delete(f"/api/v1/concerts/{concert_a.id}/lineup/{entry.id}")

    assert response.status_code == 404

    lineup_response = client.get(f"/api/v1/concerts/{concert_b.id}/lineup")
    assert lineup_response.status_code == 200
    assert entry.id in [item["id"] for item in lineup_response.json()]


def test_delete_with_non_integer_entry_id_returns_422(client, db_session):
    concert_a, _ = _build_two_concerts(db_session)

    response = client.delete(f"/api/v1/concerts/{concert_a.id}/lineup/not-an-integer")

    assert response.status_code == 422
