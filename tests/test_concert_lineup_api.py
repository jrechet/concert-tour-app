"""Tests for GET /api/v1/concerts/{concert_id}/lineup: ordering, pagination,
the 404-for-missing-concert case, and the empty-lineup case.

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


def test_lineup_endpoint_returns_entries_in_ascending_set_order(client, db_session):
    concert = _build_concert(db_session)
    _add_lineup(db_session, concert, [
        ("Plays Third", 3),
        ("Plays First", 1),
        ("Plays Second", 2),
    ])

    response = client.get(f"/api/v1/concerts/{concert.id}/lineup")

    assert response.status_code == 200
    data = response.json()
    assert [entry["artist_name"] for entry in data] == [
        "Plays First", "Plays Second", "Plays Third",
    ]
    assert [entry["set_order"] for entry in data] == [1, 2, 3]


def test_lineup_endpoint_includes_expected_fields(client, db_session):
    concert = _build_concert(db_session)
    _add_lineup(db_session, concert, [("Support Act", 1)])

    response = client.get(f"/api/v1/concerts/{concert.id}/lineup")

    assert response.status_code == 200
    entry = response.json()[0]
    assert set(entry.keys()) == {"id", "artist_name", "set_order", "set_time"}
    assert entry["artist_name"] == "Support Act"
    assert entry["set_order"] == 1
    assert entry["set_time"] is None


def test_lineup_endpoint_returns_empty_list_for_concert_with_no_lineup(client, db_session):
    concert = _build_concert(db_session)

    response = client.get(f"/api/v1/concerts/{concert.id}/lineup")

    assert response.status_code == 200
    assert response.json() == []


def test_lineup_endpoint_returns_404_for_nonexistent_concert(client, db_session):
    _build_concert(db_session)
    nonexistent_id = 999999

    response = client.get(f"/api/v1/concerts/{nonexistent_id}/lineup")

    assert response.status_code == 404


def test_lineup_endpoint_pagination_limit(client, db_session):
    concert = _build_concert(db_session)
    _add_lineup(db_session, concert, [
        ("Act 1", 1), ("Act 2", 2), ("Act 3", 3), ("Act 4", 4), ("Act 5", 5),
    ])

    response = client.get(f"/api/v1/concerts/{concert.id}/lineup", params={"limit": 2})

    assert response.status_code == 200
    data = response.json()
    assert [entry["artist_name"] for entry in data] == ["Act 1", "Act 2"]


def test_lineup_endpoint_pagination_offset(client, db_session):
    concert = _build_concert(db_session)
    _add_lineup(db_session, concert, [
        ("Act 1", 1), ("Act 2", 2), ("Act 3", 3), ("Act 4", 4), ("Act 5", 5),
    ])

    response = client.get(
        f"/api/v1/concerts/{concert.id}/lineup", params={"limit": 2, "offset": 2}
    )

    assert response.status_code == 200
    data = response.json()
    assert [entry["artist_name"] for entry in data] == ["Act 3", "Act 4"]


def test_lineup_endpoint_offset_past_end_returns_empty_list(client, db_session):
    concert = _build_concert(db_session)
    _add_lineup(db_session, concert, [("Act 1", 1), ("Act 2", 2)])

    response = client.get(
        f"/api/v1/concerts/{concert.id}/lineup", params={"offset": 10}
    )

    assert response.status_code == 200
    assert response.json() == []


def test_lineup_endpoint_default_pagination_returns_all_when_under_limit(client, db_session):
    concert = _build_concert(db_session)
    _add_lineup(db_session, concert, [("Act 1", 1), ("Act 2", 2), ("Act 3", 3)])

    response = client.get(f"/api/v1/concerts/{concert.id}/lineup")

    assert response.status_code == 200
    assert len(response.json()) == 3


def test_lineup_endpoint_isolates_entries_by_concert(client, db_session):
    concert_a = _build_concert(db_session)
    concert_b = _build_concert(db_session)
    _add_lineup(db_session, concert_a, [("Opener A", 1)])
    _add_lineup(db_session, concert_b, [("Opener B", 1)])

    response = client.get(f"/api/v1/concerts/{concert_a.id}/lineup")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["artist_name"] == "Opener A"
