"""Tests for `page`/`page_size` pagination and the `X-Total-Count` header
on `GET /api/v1/concerts/`."""

from datetime import datetime, timedelta

from src.config import DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE
from tests.fixtures.dashboard_fixtures import create_concert, create_tour, create_venues


def _seed_concerts(db_session, count):
    tour = create_tour(
        db_session,
        name="Pagination Test Tour",
        artist="Test Artist",
        start_date=(datetime.now() - timedelta(days=1)).date(),
        end_date=(datetime.now() + timedelta(days=90)).date(),
        status="active",
    )
    venue = create_venues(db_session, count=1)[0]
    base_time = datetime.now()
    for i in range(count):
        create_concert(
            db_session, tour, venue, day_offset=i, ticket_price="50.00",
            base_time=base_time, tickets_sold=0,
        )
    return tour, venue


def test_default_page_size_caps_results_and_sets_total_count(client, db_session):
    _seed_concerts(db_session, DEFAULT_PAGE_SIZE + 5)

    response = client.get("/api/v1/concerts/")
    assert response.status_code == 200
    assert len(response.json()) == DEFAULT_PAGE_SIZE
    assert response.headers["X-Total-Count"] == str(DEFAULT_PAGE_SIZE + 5)


def test_page_and_page_size_return_correct_slice(client, db_session):
    _seed_concerts(db_session, 10)

    response = client.get("/api/v1/concerts/?page=2&page_size=5")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 5

    all_response = client.get("/api/v1/concerts/?page_size=10")
    all_data = all_response.json()
    assert [c["id"] for c in data] == [c["id"] for c in all_data[5:10]]
    assert response.headers["X-Total-Count"] == "10"


def test_page_size_above_max_is_rejected(client, db_session):
    _seed_concerts(db_session, 3)

    response = client.get(f"/api/v1/concerts/?page_size={MAX_PAGE_SIZE + 1}")
    assert response.status_code == 422


def test_zero_or_negative_page_is_rejected(client, db_session):
    _seed_concerts(db_session, 3)

    assert client.get("/api/v1/concerts/?page=0").status_code == 422
    assert client.get("/api/v1/concerts/?page=-1").status_code == 422


def test_zero_or_negative_page_size_is_rejected(client, db_session):
    _seed_concerts(db_session, 3)

    assert client.get("/api/v1/concerts/?page_size=0").status_code == 422
    assert client.get("/api/v1/concerts/?page_size=-1").status_code == 422


def test_total_count_reflects_filtered_set_not_full_table(client, db_session):
    tour, venues = _seed_two_cities(db_session)
    target, other = venues

    response = client.get(f"/api/v1/concerts/?city={target.city}&page=1&page_size=1")
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.headers["X-Total-Count"] == "3"


def _seed_two_cities(db_session):
    tour = create_tour(
        db_session,
        name="Filtered Pagination Tour",
        artist="Test Artist",
        start_date=(datetime.now() - timedelta(days=1)).date(),
        end_date=(datetime.now() + timedelta(days=90)).date(),
        status="active",
    )
    venues = create_venues(db_session, count=2)
    target, other = venues
    base_time = datetime.now()
    for i in range(3):
        create_concert(
            db_session, tour, target, day_offset=i, ticket_price="50.00",
            base_time=base_time, tickets_sold=0,
        )
    for i in range(5):
        create_concert(
            db_session, tour, other, day_offset=10 + i, ticket_price="60.00",
            base_time=base_time, tickets_sold=0,
        )
    return tour, venues


def test_total_count_unaffected_by_page_and_page_size(client, db_session):
    _seed_concerts(db_session, 7)

    unpaginated = client.get("/api/v1/concerts/?page_size=7")
    paginated = client.get("/api/v1/concerts/?page=3&page_size=2")

    assert unpaginated.headers["X-Total-Count"] == "7"
    assert paginated.headers["X-Total-Count"] == "7"


def test_legacy_skip_and_limit_still_work_and_take_precedence(client, db_session):
    _seed_concerts(db_session, 5)

    response = client.get("/api/v1/concerts/?skip=2&limit=2&page=1&page_size=20")
    assert response.status_code == 200
    assert len(response.json()) == 2
    assert response.headers["X-Total-Count"] == "5"
