"""Tests for the ORM-backed dashboard fixtures (tours, venues, concerts).

Unlike `tests/test_dashboard_fixtures.py` (which locks in the API/schema
based seed data from `tests/fixtures/dashboard_data.py`), these tests
exercise the persisted `Venue`/`Concert` models directly through the ORM,
verifying real foreign key relationships and per-test isolation.
"""

from datetime import datetime

from src.models import Concert, Venue


def test_tour_with_many_concerts_has_at_least_ten_concerts(tour_with_many_concerts):
    assert len(tour_with_many_concerts["concerts"]) >= 10


def test_tour_with_many_concerts_spans_past_present_and_future(tour_with_many_concerts):
    now = datetime.now()
    dates = [c.date_time for c in tour_with_many_concerts["concerts"]]
    assert any(d < now for d in dates)
    assert any(d > now for d in dates)


def test_tour_with_many_concerts_uses_multiple_distinct_venues(tour_with_many_concerts):
    venue_ids = {c.venue_id for c in tour_with_many_concerts["concerts"]}
    assert len(venue_ids) >= 3


def test_concert_foreign_keys_reference_real_persisted_rows(tour_with_many_concerts):
    tour = tour_with_many_concerts["tour"]
    venue_ids = {v.id for v in tour_with_many_concerts["venues"]}
    for concert in tour_with_many_concerts["concerts"]:
        assert concert.tour_id == tour.id
        assert concert.venue_id in venue_ids


def test_concerts_are_queryable_through_the_session(db_session, tour_with_many_concerts):
    tour = tour_with_many_concerts["tour"]
    concerts = db_session.query(Concert).filter(Concert.tour_id == tour.id).all()
    assert len(concerts) == len(tour_with_many_concerts["concerts"])


def test_empty_tour_has_zero_concerts(empty_tour, db_session):
    assert empty_tour["concerts"] == []
    count = db_session.query(Concert).filter(Concert.tour_id == empty_tour["tour"].id).count()
    assert count == 0


def test_future_only_tour_has_no_past_concerts(future_only_tour):
    now = datetime.now()
    assert len(future_only_tour["concerts"]) >= 1
    assert all(c.date_time > now for c in future_only_tour["concerts"])


def test_past_only_tour_has_no_future_concerts(past_only_tour):
    now = datetime.now()
    assert len(past_only_tour["concerts"]) >= 1
    assert all(c.date_time < now for c in past_only_tour["concerts"])


def test_fixtures_do_not_leak_state_between_tests(db_session):
    """The autouse `setup_database` fixture recreates tables per test, so no
    venues/concerts from other tests' fixtures should be visible here."""
    assert db_session.query(Venue).count() == 0
    assert db_session.query(Concert).count() == 0
