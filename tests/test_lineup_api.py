"""Tests for PATCH /api/v1/concerts/{concert_id}/lineup/{entry_id}: reordering
a lineup entry over HTTP.

Uses real venue/tour/concert fixtures persisted via the ORM so every foreign
key (concert_id) is a genuine committed id, not a hardcoded literal.
"""

from datetime import datetime, timedelta

from src.models import LineupEntry
from tests.fixtures.dashboard_fixtures import create_concert, create_tour, create_venues


def _build_concert(db_session):
    base_time = datetime(2026, 11, 1, 20, 0, 0)
    venue = create_venues(db_session, count=1)[0]
    tour = create_tour(
        db_session,
        name="Test Tour",
        artist="Test Artist",
        start_date=base_time.date(),
        end_date=(base_time + timedelta(days=10)).date(),
        status="planned",
    )
    return create_concert(
        db_session, tour, venue, day_offset=0, ticket_price="50.00", base_time=base_time
    )


def _add_lineup(db_session, concert, entries):
    """entries: list of (artist_name, set_order) tuples."""
    db_session.add_all([
        LineupEntry(concert_id=concert.id, artist_name=name, set_order=order)
        for name, order in entries
    ])
    db_session.commit()


def test_reorder_lineup_entry_returns_200_with_updated_set_order(client, db_session):
    concert = _build_concert(db_session)
    _add_lineup(db_session, concert, [
        ("Act 1", 1), ("Act 2", 2), ("Act 3", 3),
    ])
    moved = db_session.query(LineupEntry).filter_by(concert_id=concert.id, artist_name="Act 1").one()

    response = client.patch(
        f"/api/v1/concerts/{concert.id}/lineup/{moved.id}",
        json={"set_order": 3},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == moved.id
    assert data["set_order"] == 3


def test_reorder_lineup_entry_shifts_sibling_entries(client, db_session):
    concert = _build_concert(db_session)
    _add_lineup(db_session, concert, [
        ("Act 1", 1), ("Act 2", 2), ("Act 3", 3),
    ])
    moved = db_session.query(LineupEntry).filter_by(concert_id=concert.id, artist_name="Act 1").one()

    client.patch(f"/api/v1/concerts/{concert.id}/lineup/{moved.id}", json={"set_order": 3})

    response = client.get(f"/api/v1/concerts/{concert.id}/lineup")
    assert response.status_code == 200
    data = response.json()
    ordered = {entry["artist_name"]: entry["set_order"] for entry in data}
    assert ordered == {"Act 2": 1, "Act 3": 2, "Act 1": 3}


def test_reorder_lineup_entry_rejects_zero_set_order(client, db_session):
    concert = _build_concert(db_session)
    _add_lineup(db_session, concert, [("Act 1", 1)])
    entry = db_session.query(LineupEntry).filter_by(concert_id=concert.id).one()

    response = client.patch(
        f"/api/v1/concerts/{concert.id}/lineup/{entry.id}",
        json={"set_order": 0},
    )

    assert response.status_code == 422


def test_reorder_lineup_entry_rejects_negative_set_order(client, db_session):
    concert = _build_concert(db_session)
    _add_lineup(db_session, concert, [("Act 1", 1)])
    entry = db_session.query(LineupEntry).filter_by(concert_id=concert.id).one()

    response = client.patch(
        f"/api/v1/concerts/{concert.id}/lineup/{entry.id}",
        json={"set_order": -1},
    )

    assert response.status_code == 422


def test_reorder_lineup_entry_returns_404_for_nonexistent_concert(client, db_session):
    nonexistent_concert_id = 999999

    response = client.patch(
        f"/api/v1/concerts/{nonexistent_concert_id}/lineup/1",
        json={"set_order": 1},
    )

    assert response.status_code == 404


def test_reorder_lineup_entry_returns_404_for_nonexistent_entry(client, db_session):
    concert = _build_concert(db_session)
    nonexistent_entry_id = 999999

    response = client.patch(
        f"/api/v1/concerts/{concert.id}/lineup/{nonexistent_entry_id}",
        json={"set_order": 1},
    )

    assert response.status_code == 404


def test_reorder_lineup_entry_returns_404_when_entry_belongs_to_different_concert(client, db_session):
    concert_a = _build_concert(db_session)
    concert_b = _build_concert(db_session)
    _add_lineup(db_session, concert_b, [("Opener B", 1)])
    entry_id = db_session.query(LineupEntry).filter_by(concert_id=concert_b.id).one().id

    response = client.patch(
        f"/api/v1/concerts/{concert_a.id}/lineup/{entry_id}",
        json={"set_order": 1},
    )

    assert response.status_code == 404
    unchanged = db_session.query(LineupEntry).filter_by(id=entry_id).one()
    assert unchanged.set_order == 1
