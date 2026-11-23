"""Unit tests for `src.services.tour_date_service.list_tour_dates`.

Concerts are seeded through real `Venue`/`Tour` foreign keys (via
`tests/fixtures/dashboard_fixtures.py`) rather than a hardcoded
`venue_id`, and `reference_time` is passed explicitly so ordering
assertions never depend on the real wall clock.
"""

from datetime import datetime, timedelta

from src.services.tour_date_service import list_tour_dates
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

    def test_mixed_past_and_future_returns_next_upcoming_concert_first(self, db_session):
        venues = create_venues(db_session, count=4)
        tour = _make_tour(db_session)

        far_future = create_concert(db_session, tour, venues[0], day_offset=30, ticket_price="50.00", base_time=REFERENCE_TIME)
        next_concert = create_concert(db_session, tour, venues[1], day_offset=1, ticket_price="50.00", base_time=REFERENCE_TIME)
        recent_past = create_concert(db_session, tour, venues[2], day_offset=-3, ticket_price="50.00", base_time=REFERENCE_TIME)
        older_past = create_concert(db_session, tour, venues[3], day_offset=-20, ticket_price="50.00", base_time=REFERENCE_TIME)

        result = list_tour_dates(db_session, reference_time=REFERENCE_TIME)

        assert result[0].id == next_concert.id
        assert [c.id for c in result] == [
            next_concert.id, far_future.id, older_past.id, recent_past.id,
        ]

    def test_all_future_rows_returned_strictly_ascending(self, db_session):
        venues = create_venues(db_session, count=3)
        tour = _make_tour(db_session)

        far_future = create_concert(db_session, tour, venues[0], day_offset=30, ticket_price="50.00", base_time=REFERENCE_TIME)
        next_concert = create_concert(db_session, tour, venues[1], day_offset=1, ticket_price="50.00", base_time=REFERENCE_TIME)
        mid_future = create_concert(db_session, tour, venues[2], day_offset=10, ticket_price="50.00", base_time=REFERENCE_TIME)

        result = list_tour_dates(db_session, reference_time=REFERENCE_TIME)

        assert [c.id for c in result] == [next_concert.id, mid_future.id, far_future.id]

    def test_all_past_rows_returned_ascending_after_nothing(self, db_session):
        venues = create_venues(db_session, count=3)
        tour = _make_tour(db_session)

        oldest_past = create_concert(db_session, tour, venues[0], day_offset=-40, ticket_price="50.00", base_time=REFERENCE_TIME)
        recent_past = create_concert(db_session, tour, venues[1], day_offset=-3, ticket_price="50.00", base_time=REFERENCE_TIME)
        older_past = create_concert(db_session, tour, venues[2], day_offset=-20, ticket_price="50.00", base_time=REFERENCE_TIME)

        result = list_tour_dates(db_session, reference_time=REFERENCE_TIME)

        assert [c.id for c in result] == [oldest_past.id, older_past.id, recent_past.id]

    def test_same_datetime_entries_tie_break_by_venue_name_then_id(self, db_session):
        venues = create_venues(db_session, count=2)
        tour = _make_tour(db_session)

        zebra_venue, alpha_venue = venues[0], venues[1]
        zebra_venue.name = "Zebra Arena"
        alpha_venue.name = "Alpha Theater"
        db_session.add_all([zebra_venue, alpha_venue])
        db_session.commit()

        first_created = create_concert(db_session, tour, zebra_venue, day_offset=10, ticket_price="50.00", base_time=REFERENCE_TIME)
        second_created = create_concert(db_session, tour, alpha_venue, day_offset=10, ticket_price="50.00", base_time=REFERENCE_TIME)
        assert first_created.date_time == second_created.date_time

        result = list_tour_dates(db_session, reference_time=REFERENCE_TIME)

        # "Alpha Theater" sorts before "Zebra Arena", regardless of insertion/id order.
        assert [c.id for c in result] == [second_created.id, first_created.id]

    def test_same_datetime_same_venue_name_tie_break_by_id(self, db_session):
        venues = create_venues(db_session, count=2)
        tour = _make_tour(db_session)
        venues[0].name = "Shared Hall"
        venues[1].name = "Shared Hall"
        db_session.add_all(venues)
        db_session.commit()

        first = create_concert(db_session, tour, venues[0], day_offset=10, ticket_price="50.00", base_time=REFERENCE_TIME)
        second = create_concert(db_session, tour, venues[1], day_offset=10, ticket_price="50.00", base_time=REFERENCE_TIME)

        result = list_tour_dates(db_session, reference_time=REFERENCE_TIME)

        assert [c.id for c in result] == [first.id, second.id]

    def test_empty_table_returns_empty_list(self, db_session):
        assert list_tour_dates(db_session, reference_time=REFERENCE_TIME) == []
