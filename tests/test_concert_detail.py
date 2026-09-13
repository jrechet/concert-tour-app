"""Tests for the GET /concerts/{concert_id} detail page: headliner display,
supporting acts in running order, the no-lineup-yet empty state, and
HTML-escaping of stored artist names."""

from datetime import datetime, timedelta

from src.models import LineupEntry
from tests.fixtures.dashboard_fixtures import create_concert, create_tour, create_venues


def _build_concert(db_session, base_time=None):
    base_time = base_time or datetime(2026, 10, 1, 20, 0, 0)
    venue = create_venues(db_session, count=1)[0]
    tour = create_tour(
        db_session,
        name="Neon Skyline World Tour",
        artist="Aurora Belle",
        start_date=base_time.date(),
        end_date=(base_time + timedelta(days=30)).date(),
        status="active",
    )
    return create_concert(
        db_session, tour, venue, day_offset=0, ticket_price="95.00", base_time=base_time
    )


def test_concert_detail_shows_headliner_and_venue(client, db_session):
    concert = _build_concert(db_session)

    response = client.get(f"/concerts/{concert.id}")

    assert response.status_code == 200
    assert "Aurora Belle" in response.text
    assert "Madison Square Garden" in response.text


def test_concert_detail_renders_supporting_acts_in_running_order(client, db_session):
    concert = _build_concert(db_session)
    db_session.add_all([
        LineupEntry(
            concert_id=concert.id, artist_name="Second Opener", running_order=2,
            set_time=datetime(2026, 10, 1, 19, 30, 0),
        ),
        LineupEntry(
            concert_id=concert.id, artist_name="First Opener", running_order=1,
            set_time=datetime(2026, 10, 1, 18, 30, 0),
        ),
    ])
    db_session.commit()

    response = client.get(f"/concerts/{concert.id}")

    assert response.status_code == 200
    first_pos = response.text.index("First Opener")
    second_pos = response.text.index("Second Opener")
    assert first_pos < second_pos
    assert "06:30 PM" in response.text
    assert "07:30 PM" in response.text


def test_concert_detail_shows_empty_state_when_no_supporting_acts(client, db_session):
    concert = _build_concert(db_session)

    response = client.get(f"/concerts/{concert.id}")

    assert response.status_code == 200
    assert "Lineup to be announced" in response.text


def test_concert_detail_escapes_artist_names(client, db_session):
    concert = _build_concert(db_session)
    db_session.add(
        LineupEntry(
            concert_id=concert.id,
            artist_name="<script>alert('xss')</script>",
            running_order=1,
        )
    )
    db_session.commit()

    response = client.get(f"/concerts/{concert.id}")

    assert response.status_code == 200
    assert "<script>alert" not in response.text
    assert "&lt;script&gt;" in response.text


def test_concert_detail_returns_404_for_missing_concert(client):
    response = client.get("/concerts/999999")

    assert response.status_code == 404
