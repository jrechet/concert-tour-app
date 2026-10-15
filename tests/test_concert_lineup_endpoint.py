"""Tests for POST /api/v1/concerts/{concert_id}/lineup: adding a support act
to a concert's lineup.

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


def test_add_lineup_act_returns_201_with_created_act(client, db_session):
    concert = _build_concert(db_session)

    response = client.post(
        f"/api/v1/concerts/{concert.id}/lineup",
        json={"artist_name": "The Openers", "set_order": 1},
    )

    assert response.status_code == 201
    data = response.json()
    assert data["concert_id"] == concert.id
    assert data["artist_name"] == "The Openers"
    assert data["set_order"] == 1
    assert data["id"] is not None


def test_duplicate_set_order_returns_409_and_creates_no_row(client, db_session):
    concert = _build_concert(db_session)
    client.post(
        f"/api/v1/concerts/{concert.id}/lineup",
        json={"artist_name": "First Opener", "set_order": 1},
    )

    response = client.post(
        f"/api/v1/concerts/{concert.id}/lineup",
        json={"artist_name": "Second Opener", "set_order": 1},
    )

    assert response.status_code == 409
    entries = db_session.query(LineupEntry).filter(LineupEntry.concert_id == concert.id).all()
    assert len(entries) == 1


def test_same_set_order_on_different_concert_returns_201(client, db_session):
    concert_a = _build_concert(db_session)
    concert_b = _build_concert(db_session)
    client.post(
        f"/api/v1/concerts/{concert_a.id}/lineup",
        json={"artist_name": "Opener A", "set_order": 1},
    )

    response = client.post(
        f"/api/v1/concerts/{concert_b.id}/lineup",
        json={"artist_name": "Opener B", "set_order": 1},
    )

    assert response.status_code == 201


def test_unknown_concert_returns_404(client, db_session):
    nonexistent_id = 999999

    response = client.post(
        f"/api/v1/concerts/{nonexistent_id}/lineup",
        json={"artist_name": "The Openers", "set_order": 1},
    )

    assert response.status_code == 404
    assert "detail" in response.json()


def test_unknown_concert_checked_before_conflict(client, db_session):
    nonexistent_id = 999999

    response = client.post(
        f"/api/v1/concerts/{nonexistent_id}/lineup",
        json={"artist_name": "The Openers", "set_order": 1},
    )

    assert response.status_code == 404


def test_blank_artist_name_returns_422(client, db_session):
    concert = _build_concert(db_session)

    response = client.post(
        f"/api/v1/concerts/{concert.id}/lineup",
        json={"artist_name": "", "set_order": 1},
    )

    assert response.status_code == 422


def test_zero_set_order_returns_422(client, db_session):
    concert = _build_concert(db_session)

    response = client.post(
        f"/api/v1/concerts/{concert.id}/lineup",
        json={"artist_name": "The Openers", "set_order": 0},
    )

    assert response.status_code == 422


def test_lineup_order_after_two_successful_adds(client, db_session):
    concert = _build_concert(db_session)

    client.post(
        f"/api/v1/concerts/{concert.id}/lineup",
        json={"artist_name": "Plays Second", "set_order": 2},
    )
    client.post(
        f"/api/v1/concerts/{concert.id}/lineup",
        json={"artist_name": "Plays First", "set_order": 1},
    )

    response = client.get(f"/api/v1/concerts/{concert.id}/lineup")

    assert response.status_code == 200
    data = response.json()
    assert [entry["artist_name"] for entry in data] == ["Plays First", "Plays Second"]
    assert [entry["set_order"] for entry in data] == [1, 2]
