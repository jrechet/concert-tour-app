"""Tests for `GET /api/v1/tours/{tour_id}/calendar.ics`."""

from contextlib import contextmanager
from datetime import datetime

from icalendar import Calendar
from sqlalchemy import event

from tests.conftest import engine
from tests.fixtures.dashboard_fixtures import create_concert, create_tour, create_venues

BASE_TIME = datetime(2024, 6, 15, 20, 0, 0)


@contextmanager
def _count_queries():
    """Count SQL statements executed against the test engine while the
    `with` block runs, so tests can assert a fixed query count (no N+1)."""
    statements = []

    def _listener(conn, cursor, statement, parameters, context, executemany):
        statements.append(statement)

    event.listen(engine, "before_cursor_execute", _listener)
    try:
        yield statements
    finally:
        event.remove(engine, "before_cursor_execute", _listener)


class TestTourCalendarEndpoint:
    """Coverage for the tour calendar (.ics) endpoint."""

    def test_calendar_for_tour_with_concerts(self, client, db_session):
        venues = create_venues(db_session, count=3)
        tour = create_tour(
            db_session, "Neon Skyline World Tour", "Aurora Belle",
            BASE_TIME.date(), BASE_TIME.date(), "active",
        )
        for i, venue in enumerate(venues):
            create_concert(db_session, tour, venue, day_offset=i, ticket_price="80.00", base_time=BASE_TIME)

        response = client.get(f"/api/v1/tours/{tour.id}/calendar.ics")

        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/calendar")
        assert response.headers["content-disposition"] == f'attachment; filename="tour-{tour.id}.ics"'

        parsed = Calendar.from_ical(response.content)
        vevents = [component for component in parsed.walk() if component.name == "VEVENT"]
        assert len(vevents) == 3

    def test_calendar_for_tour_with_no_concerts(self, client, empty_tour):
        tour = empty_tour["tour"]

        response = client.get(f"/api/v1/tours/{tour.id}/calendar.ics")

        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/calendar")

        parsed = Calendar.from_ical(response.content)
        vevents = [component for component in parsed.walk() if component.name == "VEVENT"]
        assert vevents == []

    def test_nonexistent_tour_returns_404(self, client):
        response = client.get("/api/v1/tours/999999/calendar.ics")

        assert response.status_code == 404
        assert response.json()["detail"] == "Tour not found"

    def test_query_count_does_not_scale_with_concert_count(self, client, db_session):
        venues = create_venues(db_session, count=3)
        tour = create_tour(
            db_session, "Neon Skyline World Tour", "Aurora Belle",
            BASE_TIME.date(), BASE_TIME.date(), "active",
        )
        for i, venue in enumerate(venues):
            create_concert(db_session, tour, venue, day_offset=i, ticket_price="80.00", base_time=BASE_TIME)
        tour_id = tour.id
        url = f"/api/v1/tours/{tour_id}/calendar.ics"

        with _count_queries() as few_concert_queries:
            response = client.get(url)
        assert response.status_code == 200

        for i, venue in enumerate(venues):
            create_concert(db_session, tour, venue, day_offset=10 + i, ticket_price="80.00", base_time=BASE_TIME)

        with _count_queries() as many_concert_queries:
            response = client.get(url)
        assert response.status_code == 200

        # 1 query for the tour, plus 1 for its concerts joined with venue
        # (via `selectinload`), regardless of how many concerts exist.
        assert len(few_concert_queries) == len(many_concert_queries) == 2
