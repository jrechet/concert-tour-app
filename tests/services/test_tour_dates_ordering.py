"""Unit tests for `list_tour_dates`, the shared "next concert first"
chronological ordering helper.

Concerts are seeded through real `Venue`/`Tour` foreign keys (via
`tests/fixtures/dashboard_fixtures.py`) rather than a hardcoded
`venue_id`, and `reference_time` is passed explicitly so ordering
assertions never depend on the real wall clock.
"""

from datetime import datetime, timedelta

from src.services.tour_dates import list_tour_dates
from tests.fixtures.dashboard_fixtures import create_concert, create_tour, create_venues

REFERENCE_TIME = datetime(2026, 6, 1, 12, 0, 0)


def _make_tour(db_session):
    """Persist and return a `Tour` row spanning `REFERENCE_TIME`."""
    return create_tour(
        db_session, "Reunion Tour", "Test Artist",
        (REFERENCE_TIME - timedelta(days=60)).date(),
        (REFERENCE_TIME + timedelta(days=60)).date(),
        "active",
    )


class TestListTourDatesOrdering:
    """Coverage for `list_tour_dates`'s chronological ordering behaviour."""

    def test_next_concert_is_first_when_future_dates_exist(self, db_session):
        venues = create_venues(db_session, count=3)
        tour = _make_tour(db_session)

        far_future = create_concert(db_session, tour, venues[0], day_offset=30, ticket_price="50.00", base_time=REFERENCE_TIME)
        next_concert = create_concert(db_session, tour, venues[1], day_offset=1, ticket_price="50.00", base_time=REFERENCE_TIME)
        mid_future = create_concert(db_session, tour, venues[2], day_offset=10, ticket_price="50.00", base_time=REFERENCE_TIME)

        result = list_tour_dates(db_session, reference_time=REFERENCE_TIME)

        assert [c.id for c in result] == [next_concert.id, mid_future.id, far_future.id]

    def test_past_dates_follow_upcoming_dates_in_reverse_chronological_order(self, db_session):
        venues = create_venues(db_session, count=4)
        tour = _make_tour(db_session)

        upcoming = create_concert(db_session, tour, venues[0], day_offset=5, ticket_price="50.00", base_time=REFERENCE_TIME)
        recent_past = create_concert(db_session, tour, venues[1], day_offset=-3, ticket_price="50.00", base_time=REFERENCE_TIME)
        older_past = create_concert(db_session, tour, venues[2], day_offset=-20, ticket_price="50.00", base_time=REFERENCE_TIME)
        oldest_past = create_concert(db_session, tour, venues[3], day_offset=-40, ticket_price="50.00", base_time=REFERENCE_TIME)

        result = list_tour_dates(db_session, reference_time=REFERENCE_TIME)

        assert [c.id for c in result] == [
            upcoming.id, recent_past.id, older_past.id, oldest_past.id,
        ]

    def test_include_past_false_excludes_past_dates(self, db_session):
        venues = create_venues(db_session, count=2)
        tour = _make_tour(db_session)

        upcoming = create_concert(db_session, tour, venues[0], day_offset=5, ticket_price="50.00", base_time=REFERENCE_TIME)
        create_concert(db_session, tour, venues[1], day_offset=-5, ticket_price="50.00", base_time=REFERENCE_TIME)

        result = list_tour_dates(db_session, include_past=False, reference_time=REFERENCE_TIME)

        assert [c.id for c in result] == [upcoming.id]

    def test_concert_exactly_at_reference_time_counts_as_upcoming(self, db_session):
        venues = create_venues(db_session, count=2)
        tour = _make_tour(db_session)

        exactly_now = create_concert(db_session, tour, venues[0], day_offset=0, ticket_price="50.00", base_time=REFERENCE_TIME)
        past = create_concert(db_session, tour, venues[1], day_offset=-1, ticket_price="50.00", base_time=REFERENCE_TIME)

        result = list_tour_dates(db_session, reference_time=REFERENCE_TIME)

        assert [c.id for c in result] == [exactly_now.id, past.id]
        excluding_past = list_tour_dates(db_session, include_past=False, reference_time=REFERENCE_TIME)
        assert [c.id for c in excluding_past] == [exactly_now.id]

    def test_same_datetime_entries_are_ordered_deterministically_by_id(self, db_session):
        venues = create_venues(db_session, count=2)
        tour = _make_tour(db_session)

        first = create_concert(db_session, tour, venues[0], day_offset=10, ticket_price="50.00", base_time=REFERENCE_TIME)
        second = create_concert(db_session, tour, venues[1], day_offset=10, ticket_price="50.00", base_time=REFERENCE_TIME)
        assert first.date_time == second.date_time
        assert first.id < second.id

        for _ in range(3):
            result = list_tour_dates(db_session, reference_time=REFERENCE_TIME)
            assert [c.id for c in result] == [first.id, second.id]

    def test_empty_table_returns_empty_list(self, db_session):
        assert list_tour_dates(db_session, reference_time=REFERENCE_TIME) == []
