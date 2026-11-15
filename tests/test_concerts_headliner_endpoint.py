"""Tests for GET /api/v1/concerts/{concert_id}/headliner.

Uses real venue/tour/concert fixtures persisted via the ORM so every
foreign key (concert_id) is a genuine committed id, not a hardcoded literal.
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


def _add_entry(db_session, concert, artist_name, set_order):
    entry = LineupEntry(concert_id=concert.id, artist_name=artist_name, set_order=set_order)
    db_session.add(entry)
    db_session.commit()
    db_session.refresh(entry)
    return entry


def test_three_act_lineup_seeded_out_of_order_returns_the_highest_set_order_act(client, db_session):
    concert = _build_concert(db_session)
    _add_entry(db_session, concert, "Plays Third", set_order=3)
    _add_entry(db_session, concert, "Plays First", set_order=1)
    _add_entry(db_session, concert, "Plays Second", set_order=2)

    response = client.get(f"/api/v1/concerts/{concert.id}/headliner")

    assert response.status_code == 200
    assert response.json() == {"name": "Plays Third", "set_position": 3}


def test_single_act_lineup_returns_that_act(client, db_session):
    concert = _build_concert(db_session)
    _add_entry(db_session, concert, "Solo Act", set_order=1)

    response = client.get(f"/api/v1/concerts/{concert.id}/headliner")

    assert response.status_code == 200
    assert response.json() == {"name": "Solo Act", "set_position": 1}


def test_unknown_concert_returns_404_identifying_the_concert(client, db_session):
    nonexistent_id = 999999

    response = client.get(f"/api/v1/concerts/{nonexistent_id}/headliner")

    assert response.status_code == 404
    assert str(nonexistent_id) in response.json()["detail"]


def test_empty_lineup_returns_404_stating_the_lineup_is_empty(client, db_session):
    concert = _build_concert(db_session)

    response = client.get(f"/api/v1/concerts/{concert.id}/headliner")

    assert response.status_code == 404
    assert "lineup" in response.json()["detail"].lower()


def test_unknown_concert_and_empty_lineup_details_differ(client, db_session):
    concert = _build_concert(db_session)

    unknown_response = client.get("/api/v1/concerts/999999/headliner")
    empty_lineup_response = client.get(f"/api/v1/concerts/{concert.id}/headliner")

    assert unknown_response.json()["detail"] != empty_lineup_response.json()["detail"]


def test_non_integer_id_returns_422(client, db_session):
    response = client.get("/api/v1/concerts/abc/headliner")

    assert response.status_code == 422


def test_response_contains_no_extra_fields(client, db_session):
    concert = _build_concert(db_session)
    _add_entry(db_session, concert, "The Headliners", set_order=1)

    response = client.get(f"/api/v1/concerts/{concert.id}/headliner")

    assert set(response.json().keys()) == {"name", "set_position"}
