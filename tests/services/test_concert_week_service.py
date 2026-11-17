"""Unit tests for `get_concerts_for_week`."""

from datetime import datetime, timedelta, timezone
from decimal import Decimal

from sqlalchemy import event as sa_event

from src.models import Concert, ConcertStatus
from src.services.concert_service import WEEK_WINDOW_DAYS, get_concerts_for_week
from tests.fixtures.dashboard_fixtures import create_tour, create_venues

REFERENCE_TIME = datetime(2026, 6, 1, 12, 0, 0, tzinfo=timezone.utc)
NAIVE_REFERENCE_TIME = REFERENCE_TIME.replace(tzinfo=None)


def _make_tour(db_session):
    """Persist and return a `Tour` row spanning `REFERENCE_TIME`."""
    return create_tour(
        db_session, "Reunion Tour", "Test Artist",
        (NAIVE_REFERENCE_TIME - timedelta(days=60)).date(),
        (NAIVE_REFERENCE_TIME + timedelta(days=60)).date(),
        "active",
    )


def _make_concert(db_session, tour, venue, date_time, status=None):
    """Persist and return a `Concert` at an exact `date_time`, linked to
    `tour`/`venue` via real foreign keys."""
    concert = Concert(
        tour_id=tour.id,
        venue_id=venue.id,
        date_time=date_time,
        ticket_price=Decimal("50.00"),
        tickets_sold=0,
    )
    if status is not None:
        concert.status = status
    db_session.add(concert)
    db_session.commit()
    db_session.refresh(concert)
    return concert


class TestGetConcertsForWeek:
    """Coverage for `get_concerts_for_week`."""

    def test_returns_concerts_within_week_soonest_first(self, db_session):
        venue = create_venues(db_session, count=1)[0]
        tour = _make_tour(db_session)

        later = _make_concert(db_session, tour, venue, NAIVE_REFERENCE_TIME + timedelta(days=5))
        soonest = _make_concert(db_session, tour, venue, NAIVE_REFERENCE_TIME + timedelta(hours=1))
        middle = _make_concert(db_session, tour, venue, NAIVE_REFERENCE_TIME + timedelta(days=2))

        result = get_concerts_for_week(db_session, now=REFERENCE_TIME)

        assert [concert.id for concert in result] == [soonest.id, middle.id, later.id]

    def test_excludes_cancelled_concerts_inside_window(self, db_session):
        venue = create_venues(db_session, count=1)[0]
        tour = _make_tour(db_session)

        cancelled = _make_concert(
            db_session, tour, venue, NAIVE_REFERENCE_TIME + timedelta(days=1),
            status=ConcertStatus.cancelled,
        )
        active = _make_concert(db_session, tour, venue, NAIVE_REFERENCE_TIME + timedelta(days=2))

        result = get_concerts_for_week(db_session, now=REFERENCE_TIME)

        returned_ids = [concert.id for concert in result]
        assert returned_ids == [active.id]
        assert cancelled.id not in returned_ids

    def test_excludes_concerts_that_already_started(self, db_session):
        venue = create_venues(db_session, count=1)[0]
        tour = _make_tour(db_session)

        past = _make_concert(db_session, tour, venue, NAIVE_REFERENCE_TIME - timedelta(seconds=1))
        upcoming = _make_concert(db_session, tour, venue, NAIVE_REFERENCE_TIME + timedelta(days=1))

        result = get_concerts_for_week(db_session, now=REFERENCE_TIME)

        returned_ids = [concert.id for concert in result]
        assert returned_ids == [upcoming.id]
        assert past.id not in returned_ids

    def test_excludes_concerts_beyond_the_window(self, db_session):
        venue = create_venues(db_session, count=1)[0]
        tour = _make_tour(db_session)

        beyond = _make_concert(
            db_session, tour, venue,
            NAIVE_REFERENCE_TIME + timedelta(days=WEEK_WINDOW_DAYS, seconds=1),
        )
        inside = _make_concert(db_session, tour, venue, NAIVE_REFERENCE_TIME + timedelta(days=6))

        result = get_concerts_for_week(db_session, now=REFERENCE_TIME)

        returned_ids = [concert.id for concert in result]
        assert returned_ids == [inside.id]
        assert beyond.id not in returned_ids

    def test_concert_starting_exactly_at_now_is_included(self, db_session):
        venue = create_venues(db_session, count=1)[0]
        tour = _make_tour(db_session)

        at_now = _make_concert(db_session, tour, venue, NAIVE_REFERENCE_TIME)

        result = get_concerts_for_week(db_session, now=REFERENCE_TIME)

        assert [concert.id for concert in result] == [at_now.id]

    def test_concert_starting_exactly_at_window_end_is_included(self, db_session):
        venue = create_venues(db_session, count=1)[0]
        tour = _make_tour(db_session)

        at_window_end = _make_concert(
            db_session, tour, venue, NAIVE_REFERENCE_TIME + timedelta(days=WEEK_WINDOW_DAYS),
        )

        result = get_concerts_for_week(db_session, now=REFERENCE_TIME)

        assert [concert.id for concert in result] == [at_window_end.id]

    def test_concert_one_second_past_window_end_is_excluded(self, db_session):
        venue = create_venues(db_session, count=1)[0]
        tour = _make_tour(db_session)

        _make_concert(
            db_session, tour, venue,
            NAIVE_REFERENCE_TIME + timedelta(days=WEEK_WINDOW_DAYS, seconds=1),
        )

        result = get_concerts_for_week(db_session, now=REFERENCE_TIME)

        assert result == []

    def test_returns_empty_list_when_nothing_matches(self, db_session):
        result = get_concerts_for_week(db_session, now=REFERENCE_TIME)

        assert result == []

    def test_venue_is_loaded_without_extra_query(self, db_session):
        venue = create_venues(db_session, count=1)[0]
        tour = _make_tour(db_session)
        concert = _make_concert(db_session, tour, venue, NAIVE_REFERENCE_TIME + timedelta(days=1))
        expected_name = concert.venue.name
        db_session.expire_all()

        queries = []
        engine = db_session.get_bind()

        def _record(conn, cursor, statement, parameters, context, executemany):
            queries.append(statement)

        sa_event.listen(engine, "before_cursor_execute", _record)
        try:
            result = get_concerts_for_week(db_session, now=REFERENCE_TIME)
            names = [concert.venue.name for concert in result]
        finally:
            sa_event.remove(engine, "before_cursor_execute", _record)

        select_queries = [q for q in queries if q.strip().upper().startswith("SELECT")]
        assert len(select_queries) == 1
        assert names == [expected_name]
