"""Integration tests for PATCH /api/v1/concerts/{concert_id}/lineup/{entry_id},
exercised against real seeded tour/venue/concert fixtures (real foreign keys,
not hardcoded IDs).
"""

from datetime import datetime, timedelta

from src.models import LineupEntry
from tests.fixtures.dashboard_fixtures import create_concert, create_tour, create_venues


def _build_concert(db_session):
    tour = create_tour(
        db_session,
        name="Lineup Move Test Tour",
        artist="Test Artist",
        start_date=(datetime.now() - timedelta(days=1)).date(),
        end_date=(datetime.now() + timedelta(days=90)).date(),
        status="active",
    )
    venue = create_venues(db_session, count=1)[0]
    return create_concert(
        db_session,
        tour,
        venue,
        day_offset=10,
        ticket_price="50.00",
        base_time=datetime.now() + timedelta(days=30),
    )


def _add_lineup(db_session, concert, entries):
    """entries: list of (artist_name, set_order) tuples."""
    db_session.add_all(
        [
            LineupEntry(concert_id=concert.id, artist_name=name, set_order=order)
            for name, order in entries
        ]
    )
    db_session.commit()


def test_move_lineup_entry_returns_200_with_new_set_order(client, db_session):
    concert = _build_concert(db_session)
    _add_lineup(db_session, concert, [("Act 1", 1), ("Act 2", 2), ("Act 3", 3)])
    moved = db_session.query(LineupEntry).filter_by(concert_id=concert.id, artist_name="Act 1").one()

    response = client.patch(
        f"/api/v1/concerts/{concert.id}/lineup/{moved.id}",
        json={"set_order": 3},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == moved.id
    assert data["concert_id"] == concert.id
    assert data["artist_name"] == "Act 1"
    assert data["set_order"] == 3
    assert "created_at" in data


def test_move_lineup_entry_leaves_contiguous_order_on_followup_get(client, db_session):
    concert = _build_concert(db_session)
    _add_lineup(db_session, concert, [("Act 1", 1), ("Act 2", 2), ("Act 3", 3)])
    moved = db_session.query(LineupEntry).filter_by(concert_id=concert.id, artist_name="Act 1").one()

    client.patch(f"/api/v1/concerts/{concert.id}/lineup/{moved.id}", json={"set_order": 3})

    response = client.get(f"/api/v1/concerts/{concert.id}/lineup")
    assert response.status_code == 200
    ordered = {entry["artist_name"]: entry["set_order"] for entry in response.json()}
    assert ordered == {"Act 2": 1, "Act 3": 2, "Act 1": 3}


def test_move_lineup_entry_rejects_zero_set_order(client, db_session):
    concert = _build_concert(db_session)
    _add_lineup(db_session, concert, [("Act 1", 1)])
    entry = db_session.query(LineupEntry).filter_by(concert_id=concert.id).one()

    response = client.patch(
        f"/api/v1/concerts/{concert.id}/lineup/{entry.id}",
        json={"set_order": 0},
    )

    assert response.status_code == 422


def test_move_lineup_entry_rejects_negative_set_order(client, db_session):
    concert = _build_concert(db_session)
    _add_lineup(db_session, concert, [("Act 1", 1)])
    entry = db_session.query(LineupEntry).filter_by(concert_id=concert.id).one()

    response = client.patch(
        f"/api/v1/concerts/{concert.id}/lineup/{entry.id}",
        json={"set_order": -2},
    )

    assert response.status_code == 422


def test_move_lineup_entry_rejects_missing_set_order(client, db_session):
    concert = _build_concert(db_session)
    _add_lineup(db_session, concert, [("Act 1", 1)])
    entry = db_session.query(LineupEntry).filter_by(concert_id=concert.id).one()

    response = client.patch(
        f"/api/v1/concerts/{concert.id}/lineup/{entry.id}",
        json={},
    )

    assert response.status_code == 422


def test_move_lineup_entry_rejects_non_integer_set_order(client, db_session):
    concert = _build_concert(db_session)
    _add_lineup(db_session, concert, [("Act 1", 1)])
    entry = db_session.query(LineupEntry).filter_by(concert_id=concert.id).one()

    response = client.patch(
        f"/api/v1/concerts/{concert.id}/lineup/{entry.id}",
        json={"set_order": "first"},
    )

    assert response.status_code == 422


def test_move_lineup_entry_returns_404_for_unknown_concert(client, db_session):
    response = client.patch(
        "/api/v1/concerts/999999/lineup/1",
        json={"set_order": 1},
    )

    assert response.status_code == 404


def test_move_lineup_entry_returns_404_for_unknown_entry(client, db_session):
    concert = _build_concert(db_session)

    response = client.patch(
        f"/api/v1/concerts/{concert.id}/lineup/999999",
        json={"set_order": 1},
    )

    assert response.status_code == 404


def test_move_lineup_entry_returns_404_when_entry_belongs_to_different_concert(client, db_session):
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
