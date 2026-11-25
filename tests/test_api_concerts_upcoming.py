"""Tests for `GET /api/concerts/upcoming`."""

from datetime import date, datetime, time, timedelta

from tests.fixtures.dashboard_fixtures import create_concert, create_tour, create_venues

BASE_TIME = datetime.combine(date.today(), time(20, 0))


def _seed_concert(db_session, day_offset, venue=None, tour=None, ticket_price="80.00"):
    """Persist a concert on a real tour/venue, dated relative to today."""
    venue = venue or create_venues(db_session, count=1)[0]
    tour = tour or create_tour(
        db_session, "Neon Skyline World Tour", "Aurora Belle",
        (BASE_TIME - timedelta(days=30)).date(), (BASE_TIME + timedelta(days=30)).date(),
        "active",
    )
    return create_concert(db_session, tour, venue, day_offset=day_offset, ticket_price=ticket_price, base_time=BASE_TIME)


def test_upcoming_returns_200_and_sorted_payload(client, db_session):
    venues = create_venues(db_session, count=3)
    tour = create_tour(
        db_session, "Neon Skyline World Tour", "Aurora Belle",
        (BASE_TIME - timedelta(days=30)).date(), (BASE_TIME + timedelta(days=30)).date(),
        "active",
    )
    later = _seed_concert(db_session, day_offset=20, venue=venues[0], tour=tour)
    soonest = _seed_concert(db_session, day_offset=1, venue=venues[1], tour=tour)
    middle = _seed_concert(db_session, day_offset=10, venue=venues[2], tour=tour)

    response = client.get("/api/concerts/upcoming")

    assert response.status_code == 200
    assert [item["id"] for item in response.json()] == [soonest.id, middle.id, later.id]


def test_upcoming_returns_200_and_empty_list_when_none(client):
    response = client.get("/api/concerts/upcoming")

    assert response.status_code == 200
    assert response.json() == []


def test_upcoming_excludes_past_concerts(client, db_session):
    past_concert = _seed_concert(db_session, day_offset=-1)

    response = client.get("/api/concerts/upcoming")

    assert response.status_code == 200
    assert past_concert.id not in [item["id"] for item in response.json()]


def test_upcoming_includes_today(client, db_session):
    today_concert = _seed_concert(db_session, day_offset=0)

    response = client.get("/api/concerts/upcoming")

    assert response.status_code == 200
    assert [item["id"] for item in response.json()] == [today_concert.id]


def test_upcoming_response_fields_match_schema(client, db_session):
    concert = _seed_concert(db_session, day_offset=3)

    response = client.get("/api/concerts/upcoming")

    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 1
    item = payload[0]
    assert set(item.keys()) == {"id", "title", "date", "venue_id"}
    assert item["id"] == concert.id
    assert item["venue_id"] == concert.venue_id
    assert item["date"] == (BASE_TIME + timedelta(days=3)).date().isoformat()


def test_post_to_upcoming_returns_405(client):
    response = client.post("/api/concerts/upcoming")

    assert response.status_code == 405
