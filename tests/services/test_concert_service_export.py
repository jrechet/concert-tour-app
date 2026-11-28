"""Unit tests for `get_concerts_for_export`."""

from datetime import datetime
from decimal import Decimal

from sqlalchemy import event as sa_event, text

from src.models import Concert
from src.services.concert_service import get_concerts_for_export
from tests.fixtures.dashboard_fixtures import create_tour, create_venues

BASE_TIME = datetime(2024, 6, 15, 20, 0, 0)


def _make_concert(db_session, tour, venue, date_time):
    """Persist and return a `Concert` at an exact `date_time`, linked to
    `tour`/`venue` via real foreign keys."""
    concert = Concert(
        tour_id=tour.id,
        venue_id=venue.id,
        date_time=date_time,
        ticket_price=Decimal("50.00"),
        tickets_sold=0,
    )
    db_session.add(concert)
    db_session.commit()
    db_session.refresh(concert)
    return concert


class TestGetConcertsForExport:
    """Coverage for `get_concerts_for_export`."""

    def test_returns_empty_list_when_no_concerts(self, db_session):
        assert get_concerts_for_export(db_session) == []

    def test_concerts_inserted_out_of_order_come_back_sorted_by_date(self, db_session):
        venue = create_venues(db_session, count=1)[0]
        tour = create_tour(
            db_session, "Neon Skyline World Tour", "Aurora Belle",
            BASE_TIME.date(), BASE_TIME.date(), "active",
        )

        middle = _make_concert(db_session, tour, venue, BASE_TIME)
        last = _make_concert(db_session, tour, venue, BASE_TIME.replace(year=2025))
        first = _make_concert(db_session, tour, venue, BASE_TIME.replace(year=2023))

        result = get_concerts_for_export(db_session)

        assert [concert.id for concert in result] == [first.id, middle.id, last.id]

    def test_venue_and_tour_are_loaded_without_extra_queries(self, db_session):
        venue = create_venues(db_session, count=1)[0]
        tour = create_tour(
            db_session, "Neon Skyline World Tour", "Aurora Belle",
            BASE_TIME.date(), BASE_TIME.date(), "active",
        )
        concert = _make_concert(db_session, tour, venue, BASE_TIME)
        expected_venue_name = venue.name
        expected_tour_name = tour.name
        db_session.expire_all()

        queries = []
        engine = db_session.get_bind()

        def _record(conn, cursor, statement, parameters, context, executemany):
            queries.append(statement)

        sa_event.listen(engine, "before_cursor_execute", _record)
        try:
            result = get_concerts_for_export(db_session)
            venue_names = [row.venue.name for row in result]
            tour_names = [row.tour.name for row in result]
        finally:
            sa_event.remove(engine, "before_cursor_execute", _record)

        select_queries = [q for q in queries if q.strip().upper().startswith("SELECT")]
        assert len(select_queries) == 1
        assert result[0].id == concert.id
        assert venue_names == [expected_venue_name]
        assert tour_names == [expected_tour_name]

    def test_concert_with_null_tour_relationship_is_still_returned(self, db_session):
        venue = create_venues(db_session, count=1)[0]
        tour = create_tour(
            db_session, "Solo Tour", "Test Artist",
            BASE_TIME.date(), BASE_TIME.date(), "active",
        )
        concert = _make_concert(db_session, tour, venue, BASE_TIME)

        # Bypass the ORM to remove the referenced tour row while leaving
        # `concert.tour_id` pointing at it, so the eager-loaded `tour`
        # relationship resolves to `None` via the `LEFT OUTER JOIN`
        # `joinedload` issues, without requiring a nullable `tour_id` column.
        db_session.execute(text("DELETE FROM tours WHERE id = :id"), {"id": tour.id})
        db_session.commit()

        result = get_concerts_for_export(db_session)

        assert [row.id for row in result] == [concert.id]
        assert result[0].tour is None
        assert result[0].venue.name == venue.name
