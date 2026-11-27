"""Tests for `GET /api/v1/concerts` pagination: `page`/`page_size` query
params, the `X-Total-Count` response header, and the 422 validation cases
that must reject before any database query runs.
"""

from datetime import datetime, timedelta

from src.config import DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE
from tests.fixtures.dashboard_fixtures import create_concert, create_tour, create_venues


def _seed_concerts(db_session, count):
    tour = create_tour(
        db_session,
        name="Pagination Tour",
        artist="Pagination Artist",
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


def test_default_params_return_at_most_20_items_and_real_total_count(client, db_session):
    _seed_concerts(db_session, DEFAULT_PAGE_SIZE + 7)

    response = client.get("/api/v1/concerts/")

    assert response.status_code == 200
    assert len(response.json()) == DEFAULT_PAGE_SIZE
    assert response.headers["X-Total-Count"] == str(DEFAULT_PAGE_SIZE + 7)


def test_explicit_page_and_page_size_returns_disjoint_second_slice(client, db_session):
    _seed_concerts(db_session, 20)

    page1 = client.get("/api/v1/concerts/?page=1&page_size=10")
    page2 = client.get("/api/v1/concerts/?page=2&page_size=10")

    assert page1.status_code == 200
    assert page2.status_code == 200
    page1_ids = [c["id"] for c in page1.json()]
    page2_ids = [c["id"] for c in page2.json()]
    assert len(page2_ids) == 10
    assert set(page1_ids).isdisjoint(page2_ids)
    assert page1.headers["X-Total-Count"] == "20"
    assert page2.headers["X-Total-Count"] == "20"


def test_page_size_above_max_is_rejected_without_hitting_the_database(client, db_session):
    response = client.get(f"/api/v1/concerts/?page_size={MAX_PAGE_SIZE + 1}")
    assert response.status_code == 422


def test_zero_page_size_is_rejected_without_hitting_the_database(client, db_session):
    response = client.get("/api/v1/concerts/?page_size=0")
    assert response.status_code == 422


def test_zero_page_is_rejected_without_hitting_the_database(client, db_session):
    response = client.get("/api/v1/concerts/?page=0")
    assert response.status_code == 422


def test_non_integer_page_is_rejected_without_hitting_the_database(client, db_session):
    response = client.get("/api/v1/concerts/?page=abc")
    assert response.status_code == 422


def test_page_size_at_inclusive_max_is_accepted(client, db_session):
    _seed_concerts(db_session, 3)

    response = client.get(f"/api/v1/concerts/?page_size={MAX_PAGE_SIZE}")

    assert response.status_code == 200
    assert len(response.json()) == 3


def test_page_beyond_last_returns_empty_list_with_real_total_count(client, db_session):
    _seed_concerts(db_session, 5)

    response = client.get("/api/v1/concerts/?page=10&page_size=10")

    assert response.status_code == 200
    assert response.json() == []
    assert response.headers["X-Total-Count"] == "5"


def test_empty_table_returns_empty_list_and_zero_total_count(client, db_session):
    response = client.get("/api/v1/concerts/")

    assert response.status_code == 200
    assert response.json() == []
    assert response.headers["X-Total-Count"] == "0"
